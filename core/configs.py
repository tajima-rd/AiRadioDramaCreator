# AiRadioDramaCreator/core/configs.py

from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Dict
from google.genai import types
from typing import List, Dict, Optional 

class SPEECH_CONFIG_TYPE(Enum):
    SINGLE = "SINGLE"
    MULTI = "MULTI"
    SIMPLE = "SIMPLE"

class Project:
    def __init__(self, 
        project_name: str = "", 
        project_description: str = "", 
        author: str = "", 
        version: str = "", 
        api_keys: Optional[List[str]] = None, # Noneを許容するためにOptionalを使用
        api_index: Optional[int] = None,      # Noneを許容するためにOptionalを使用
        speech_model: Optional[str] = None,   # Noneを許容するためにOptionalを使用
        text_model: Optional[str] = None,     # Noneを許容するためにOptionalを使用
        created_date: Optional[str] = None,   # JSONからは文字列で来ることを想定
        updated_date: Optional[str] = None,   # JSONからは文字列で来ることを想定
        root_path: Optional[str] = None,      # Noneを許容するためにOptionalを使用
        speakers: Optional[Dict[str, str]] = None, # Noneを許容し、辞書型を明示
        wait_time: int = 30 # デフォルト値を設定
    ):
        self.project_name = project_name
        self.project_description = project_description
        self.author = author
        self.version = version
        self.api_keys = api_keys if api_keys is not None else [] # Noneの場合は空リストに初期化
        self.api_index = api_index
        self.speech_model = speech_model
        self.text_model = text_model

        # 日付の処理: created_date/updated_dateが与えられていない場合、現在時刻をISOフォーマット文字列で設定
        self.created_at = created_date if created_date is not None else datetime.now().isoformat()
        self.updated_at = updated_date if updated_date is not None else datetime.now().isoformat()

        # ルートパスとディレクトリ作成のロジックを修正
        # 引数としてroot_pathが有効な文字列/Pathとして与えられた場合のみディレクトリ作成を試みる
        self.root_path = None # 初期値としてNoneを設定

        if root_path: # root_pathがNoneや空文字列でない場合のみ処理
            # pathlib.Pathオブジェクトに変換し、解決された絶対パスを取得
            resolved_root_path = Path(root_path).resolve()
            try:
                # ルートディレクトリを、親ディレクトリも含めて、もし存在しなければ作成する
                # exist_ok=True により、ディレクトリが既に存在してもエラーにならない
                resolved_root_path.mkdir(parents=True, exist_ok=True)
                
                # 定義されたサブディレクトリを作成
                subdirs = ["persona", "script", "dialog", "ssml", "audio"]
                for subdir in subdirs:
                    (resolved_root_path / subdir).mkdir(exist_ok=True)
                
                # 正常に作成できた場合、resolved_root_path を属性に保存
                self.root_path = resolved_root_path # Pathオブジェクトとして保存
            except Exception as e:
                # ディレクトリ作成に失敗した場合の警告を出力
                import sys # sysモジュールをインポートしてstderrに警告を出力
                print(f"Warning: Could not create project directories at '{root_path}': {e}", file=sys.stderr)
                # 失敗した場合でも、root_path自体はPathオブジェクトとして保存（存在しないパスになる）
                self.root_path = Path(root_path)
        
        self.speakers = speakers if speakers is not None else {} # Noneの場合は空辞書に初期化
        self.wait_time = wait_time

class SpeechConfig:
    def __init__(self, temperature=1.0, modalities=["audio"], speakers: Dict=None):
        try:
            self.temperature = temperature
            self.modalities = modalities
            
            # 各設定を格納するためのインスタンス変数を初期化
            self.single_speaker_voice_config = None
            self.multi_speaker_voice_config = None

            speaker_config_list = []
            if speakers:
                for character, voice_name in speakers.items():
                    single_speaker_model = types.SpeakerVoiceConfig(
                        speaker=character,
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name
                            )
                        ),
                    )
                    speaker_config_list.append(single_speaker_model)
            
            num_speakers = len(speaker_config_list)

            if num_speakers == 0:
                print("Warning: No speakers provided. Using default simple config.")
                self.model_config = self._get_simple_config()
            elif num_speakers == 1:
                print("Warning: Only one speaker provided. Using single speaker config.")
                # SpeakerVoiceConfigからVoiceConfigを取り出して単一話者用の変数に格納
                self.single_speaker_voice_config = speaker_config_list[0]
                self.model_config = self._get_single_speaker_config()
            else:
                print(f"Using multi-speaker config with {num_speakers} speakers.")
                # 複数話者用の設定オブジェクトを生成して変数に格納
                self.multi_speaker_voice_config = types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=speaker_config_list
                )
                self.model_config = self._get_multi_speaker_config()

        except Exception as e:
            print(f"Content Config の生成に失敗しました: {e}")
            raise


    def _get_simple_config(self):
        return types.GenerateContentConfig(
            temperature=self.temperature,  # Adjust temperature as needed (higher = more varied speech)
            response_modalities=self.modalities,
        )
    
    def _get_single_speaker_config(self):
        if not self.single_speaker_voice_config == None:
            return types.GenerateContentConfig(
                temperature = self.temperature, # Adjust temperature as needed (higher = more varied speech)
                response_modalities = self.modalities,
                speech_config = types.SpeechConfig(
                    voice_config = self.single_speaker_voice_config
                )
            )
        else:
            print("Warning: No speaker configuration provided. Using default content config.")
            self.get_simple_config()
    
    def _get_multi_speaker_config(self):
        if not self.multi_speaker_voice_config == None:
            return types.GenerateContentConfig(
                temperature = self.temperature, # Adjust temperature as needed (higher = more varied speech)
                response_modalities = self.modalities,
                speech_config = types.SpeechConfig(
                    multi_speaker_voice_config = self.multi_speaker_voice_config
                )
            )
        else:
            print("Warning: No speaker configuration provided. Using default content config.")
            self.get_simple_config()

class WriteConfig:
    def __init__(self, temperature=1.0, top_p=0.95, max_output_tokens=65536, thinking_budget=-1):
        self.temperature = temperature
        self.top_p = top_p
        self.max_output_tokens = max_output_tokens
        self.thinking_budget = thinking_budget
        self.model_config = self._create_content_config()

    def _create_content_config(self):
        return types.GenerateContentConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            max_output_tokens=self.max_output_tokens,
            thinking_config = types.ThinkingConfig(
                thinking_budget = self.thinking_budget,
            ),
        )