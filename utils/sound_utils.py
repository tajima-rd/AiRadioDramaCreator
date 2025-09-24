from pathlib import Path
from .configs import Dialog, SpeechParams
from .generators import Generator, AudioProcessor
from .api_client import GeminiApiClient

# --- 1. 準備 ---
api_connection = GeminiApiClient(...)
character_a = ...
character_b = ...
output_dir = Path("./audio_output")
basename = "scene_01"

# --- 2. 設定オブジェクトの作成 ---
# 音声生成用の設定を持つDialogシーンオブジェクトを作成
dialog_scene = Dialog(
    character_1=character_a,
    character_2=character_b,
    speech_params=SpeechParams(temperature=0.95)
)

# --- 3. ジェネレーターの初期化 ---
# APIクライアントと「シーン設定」を渡してジェネレーターを作成
generator = Generator(api_conn=api_connection, scene_config=dialog_scene)

# --- 4. 音声データの「生成」 ---
# SSML/プロンプトを渡して、生の音声データを取得
prompt = "<speaker Alice>Hello Bob.<speaker Bob>Hi Alice."
result = generator.generate_audio(prompt)

# --- 5. 音声データの「加工と保存」 ---
if result:
    # Generatorから返された生の音声データをAudioProcessorに渡す
    raw_audio = result["audio_data"]
    mime_type = result["mime_type"]
    
    # WAV形式のバイトデータに変換
    wav_data = AudioProcessor.to_wav(raw_audio, mime_type)
    
    # MP3としてファイルに保存
    mp3_file_path = output_dir / f"{basename}.mp3"
    AudioProcessor.save_as_mp3(wav_data, mp3_file_path)
