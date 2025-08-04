# AiRadioDramaCreator/core/generators.py

import mimetypes
import struct
from pathlib import Path
from pydub import AudioSegment
from google.genai import types

from .api_client import GeminiApiClient
from .models import SpeechConfig, WriteConfig

class TextGenerator:
    def __init__(self, api_conn: GeminiApiClient, write_config: WriteConfig, prompt: str=None, parent=None, basename=None):
        self.connector = api_conn
        self.content = self._set_content(prompt)
        self.content_config = write_config.model_config
        self.parent = parent
        self.basename = basename
    
    def _set_content(self, prompt):
        return [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
    
    def generate(self):
        """
        ストリーミングレスポンスの全チャンクを結合して、完全なテキストを返す。
        """
        full_response = "" # 全てのテキストを結合するための空の文字列を準備
        
        # ストリーミングAPIを呼び出し、全チャンクをループ処理する
        stream = self.connector.client.models.generate_content_stream(
            model=self.connector.model_name,
            contents=self.content,
            config=self.content_config,
        )

        for chunk in stream:
            # chunk.textがNoneでないことを確認してから結合
            if chunk.text:
                full_response += chunk.text
        
        # 全てのループが終わった後で、結合した完全なテキストを返す
        return full_response.strip()
        
        # for chunk in self.connector.client.models.generate_content_stream(
        #     model=self.connector.model_name,
        #     contents=self.content,
        #     config=self.content_config,
        # ):
        #     return(chunk.text)

class SpeechGenerator:
    def __init__(self, api_conn: GeminiApiClient, speech_config: SpeechConfig, ssml_dialog: str, parent:Path, basename: str):
        self.connector = api_conn
        self.content = self._set_content(ssml_dialog)
        self.content_config = speech_config.model_config
        self.parent = parent
        self.basename = basename
        self._wav_file = None
        self._mp3_file = None
    
    def _set_content(self, ssml):
        return [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=ssml),
                ],
            ),
        ]

    def _parse_audio_mime_type(self, mime_type: str) -> dict[str, int | None]:
        bits_per_sample = 16
        rate = 24000

        # Extract rate from parameters
        parts = mime_type.split(";")
        for param in parts: # Skip the main type part
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate_str = param.split("=", 1)[1]
                    rate = int(rate_str)
                except (ValueError, IndexError):
                    # Handle cases like "rate=" with no value or non-integer value
                    pass # Keep rate as default
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass # Keep bits_per_sample as default if conversion fails

        return {"bits_per_sample": bits_per_sample, "rate": rate}
        
    def _convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        parameters = self._parse_audio_mime_type(mime_type)
        bits_per_sample = parameters["bits_per_sample"]
        sample_rate = parameters["rate"]
        num_channels = 1
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

        # http://soundfile.sapp.org/doc/WaveFormat/

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",          # ChunkID
            chunk_size,       # ChunkSize (total file size - 8 bytes)
            b"WAVE",          # Format
            b"fmt ",          # Subchunk1ID
            16,               # Subchunk1Size (16 for PCM)
            1,                # AudioFormat (1 for PCM)
            num_channels,     # NumChannels
            sample_rate,      # SampleRate
            byte_rate,        # ByteRate
            block_align,      # BlockAlign
            bits_per_sample,  # BitsPerSample
            b"data",          # Subchunk2ID
            data_size         # Subchunk2Size (size of audio data)
        )
        return header + audio_data

    def _convert_to_mp3(self, wav_file: Path):
        # 出力先のMP3ファイルパスを定義する（これは元のままでOK）
        mp3_file = Path(self.parent / f"{self.basename}.mp3")

        # ★修正点1: 入力ファイル(wav_file)の存在をチェックする
        if not wav_file.exists():
            print(f"Error: Input WAV file not found for MP3 conversion: {wav_file}")
            return None

        # 出力ディレクトリの存在を確認（これは元のコードにもあり、良いプラクティス）
        mp3_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"Converting {wav_file.name} to MP3...")
        try:
            # pydubでWAVファイルを読み込む
            audio = AudioSegment.from_file(wav_file, format=wav_file.suffix.lstrip('.'))

            # ★修正点2: 正しい出力パス(mp3_file)にエクスポートする
            audio.export(mp3_file, format="mp3")

            print(f"Successfully converted to: {mp3_file}")

            # インスタンス変数にも保存しておく
            self._mp3_file = mp3_file

            return self._mp3_file

        except FileNotFoundError:
            print(f"Error: ffmpeg not found. Please install ffmpeg and ensure it's in your system's PATH.")
            print("See: https://ffmpeg.org/download.html")
            return None
        except Exception as e:
            print(f"An error occurred during MP3 conversion: {e}")
            return None

    def _save_binary_file(self, file_name, data):
        with open(file_name, "wb") as f:
            f.write(data)
        print(f"File saved to: {file_name}")

    def generate(self):
        # Generate audio content from the dialog
        print(f"Generating audio content for dialog.")

        wav_file = Path(self.parent / f"{self.basename}.wav")
        full_audio_data = bytearray()
        final_mime_type = None

        try:
            # ここで音声を生成する。
            for chunk in self.connector.client.models.generate_content_stream(
                model=self.connector.model_name,
                contents=self.content,
                config=self.content_config,
            ):
                if (
                    chunk.candidates
                    and chunk.candidates[0].content
                    and chunk.candidates[0].content.parts
                    and chunk.candidates[0].content.parts[0].inline_data
                    and chunk.candidates[0].content.parts[0].inline_data.data
                ):
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    
                    # データをバッファに追加
                    full_audio_data.extend(inline_data.data)

                    # 最後のMIMEタイプを保持
                    final_mime_type = inline_data.mime_type
                
                elif chunk.text:
                    print(f"Text chunk: {chunk.text}")
        except Exception as e:
            print(f"An error occurred during audio generation: {e}")
            raise e
        
        if full_audio_data and final_mime_type:
            file_extension = mimetypes.guess_extension(final_mime_type)
            if file_extension is None:
                print(f"Warning: Could not guess extension for MIME type {final_mime_type}. Assuming .wav and converting.")
                try:
                    # WAVに変換して保存する。
                    wav_data = self._convert_to_wav(bytes(full_audio_data), final_mime_type)
                    self._save_binary_file(wav_file, wav_data)
                    self._convert_to_mp3(wav_file)

                except Exception as e:
                    print(f"Error converting or saving data with MIME {final_mime_type} to WAV: {e}")
                    return None
            else:
                 # その他の形式の場合（通常は発生しないが念のため）
                 self._save_binary_file(wav_file, bytes(full_audio_data))
        else:
            print("No audio data was generated.")
            return None
        
        self._wav_file = wav_file