# AiRadioDramaCreator/core/configs.py

from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Dict
from google.genai import types
from typing import List, Dict, Optional 
from enum import Enum

from typing import List, Dict, Union, Any

class Voice(Enum):
    """
    利用可能な話者の情報を定義する列挙型。

    各メンバーは、APIで実際に使用する名前、声の特徴、性別を属性として持ちます。
    
    使用例:
    >>> print(Voice.ACHERNAR.api_name)
    'Achernar'
    >>> print(Voice.ACHERNAR.description)
    'Soft'
    """
    def __init__(self, api_name: str, description: str, gender: str):
        self.api_name = api_name
        self.description = description
        self.gender = gender

    # --- 話者リスト ---
    # Enumメンバー名 = (API名, 特徴, 性別)
    ACHERNAR = ("Achernar", "Soft", "F")
    ACHIRD = ("Achird", "Friendly", "M")
    ALGENIB = ("Algenib", "Gravelly", "M")
    ALGIEBA = ("Algieba", "Smooth", "M")
    ALNILAM = ("Alnilam", "Firm", "M")
    AOEDE = ("Aoede", "Breezy", "F")
    AUTONOE = ("Autonoe", "Bright", "F")
    CALLIRRHOE = ("Callirrhoe", "Easy-going", "F")
    CHARON = ("Charon", "Informative", "M")
    DESPINA = ("Despina", "Smooth", "F")
    ENCELADUS = ("Enceladus", "Breathy", "M")
    ERINOME = ("Erinome", "Clear", "F")
    FENRIR = ("Fenrir", "Excitable", "M")
    GACRUX = ("Gacrux", "Mature", "F")
    IAPETUS = ("Iapetus", "Clear", "M")
    KORE = ("Kore", "Firm", "F")
    LAOMEDEIA = ("Laomedeia", "Upbeat", "F")
    LEDA = ("Leda", "Youthful", "F")
    ORUS = ("Orus", "Firm", "M")
    PUCK = ("Puck", "Upbeat", "M")
    PULCHERRIMA = ("Pulcherrima", "Forward", "M")
    RASALGETHI = ("Rasalgethi", "Informative", "M")
    SADACHBIA = ("Sadachbia", "Lively", "M")
    SADALTAGER = ("Sadaltager", "Knowledgeable", "M")
    SCHEDAR = ("Schedar", "Even", "M")
    SULAFAT = ("Sulafat", "Warm", "F")
    UMBRIEL = ("Umbriel", "Easy-going", "M")
    VINDEMIATRIX = ("Vindemiatrix", "Gentle", "F")
    ZEPHYR = ("Zephyr", "Bright", "F")
    ZUBENELGENUBI = ("Zubenelgenubi", "Casual", "M")

    @classmethod
    def get_female_voices(cls):
        """女性の話者のみをリストで返します。"""
        return [member for member in cls if member.gender == 'F']

    @classmethod
    def get_male_voices(cls):
        """男性の話者のみをリストで返します。"""
        return [member for member in cls if member.gender == 'M']

class SPEECH_CONFIG_TYPE(Enum):
    SINGLE = "SINGLE"
    MULTI = "MULTI"
    SIMPLE = "SIMPLE"

class Character:
    def __init__(
            self,
            name: str,
            voice: Voice,
            personality: str,
            traits: List[str],
            speech_style: str,
            verbal_tics: List[str],
            background: Optional[str] = None,
            role: Optional[str] = None):
        self.name: str = name
        self.voice: str = voice
        self.personality: str = personality
        self.traits: List[str] = traits
        self.speech_style: str = speech_style
        self.verbal_tics: List[str] = verbal_tics
        self.background: Optional[str] = background
        self.role: Optional[str] = role
    
    def get_character_prompt(self) -> str:
        """
        このキャラクターの属性に基づいて、AI用のプロンプト文字列を生成する。
        """
        # プロンプトの各行をリストとして構築していくと、管理がしやすい
        prompt_parts = []
        prompt_parts.append(f"### {self.name}")

        # Noneや空でない属性だけをプロンプトに追加する
        if self.personality:
            prompt_parts.append(f"- 性格: {self.personality}")
        if self.speech_style:
            prompt_parts.append(f"- 話し方: {self.speech_style}")
        if self.traits:
            prompt_parts.append(f"- 特性: {', '.join(self.traits)}")
        if self.verbal_tics:
            prompt_parts.append(f"- 口癖: {', '.join(self.verbal_tics)}")
        if self.background:
            prompt_parts.append(f"- 背景設定: {self.background}")
        if self.role:
            prompt_parts.append(f"- 役割: {self.role}")
        
        # 各行を改行で結合し、最後にキャラクター間の区切りとして空行を2つ追加する
        return "\n".join(prompt_parts) + "\n\n"

class Project:
    def __init__(self, 
        project_name: str = "", 
        project_description: str = "", 
        author: str = "", 
        version: str = "", 
        api_keys: Optional[List[str]] = None,
        api_index: Optional[int] = None,
        speech_model: Optional[str] = None,
        text_model: Optional[str] = None,
        created_date: Optional[str] = None,
        updated_date: Optional[str] = None,
        root_path: Optional[str] = None,
        characters: Optional[List[Character]] = None,
        wait_time: int = 30
    ):
        self.project_name = project_name
        self.project_description = project_description
        self.author = author
        self.version = version
        self.api_keys = api_keys if api_keys is not None else []
        self.api_index = api_index
        self.speech_model = speech_model
        self.text_model = text_model

        self.created_at = created_date if created_date is not None else datetime.now().isoformat()
        self.updated_at = updated_date if updated_date is not None else datetime.now().isoformat()

        self.root_path = None
        if root_path:
            resolved_root_path = Path(root_path).resolve()
            try:
                resolved_root_path.mkdir(parents=True, exist_ok=True)
                subdirs = ["persona", "script", "dialog", "ssml", "audio"]
                for subdir in subdirs:
                    (resolved_root_path / subdir).mkdir(exist_ok=True)
                self.root_path = resolved_root_path
            except Exception as e:
                import sys
                print(f"Warning: Could not create project directories at '{root_path}': {e}", file=sys.stderr)
                self.root_path = Path(root_path)
        
        # ★★★ ここを修正 ★★★
        # self.speakers = speakers ... の行を完全に置き換える
        self.characters = characters if characters is not None else []
        
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

def convert_speaker_dict_to_character(data: Any) -> List[Character]:
    """
    話者・キャラクターデータを正規化し、必ず新しい形式(List[Character])で返す。

    この関数は、古い形式(Dict[str, str])と新しい形式(List[Character])の
    両方のデータ入力を受け付け、互換性を維持します。

    Args:
        data: 設定ファイルなどから読み込んだキャラクターデータ。
              以下のいずれかの形式を想定:
              - 新: List[Character]
              - 旧: Dict[str, str] (例: {'名前': 'ボイス名'})
              - それ以外 (None, 空の辞書/リストなど)

    Returns:
        必ず List[Character] 形式に変換されたデータ。
        変換不可能な場合や入力が空の場合は、空のリストを返す。
    """
    # 1. データが既に新しい形式 (List[Character]) の場合
    if isinstance(data, list):
        # リストが空であるか、最初の要素がCharacterインスタンスなら、新しい形式と判断
        if not data or isinstance(data[0], Character):
            return data

    # 2. データが古い形式 (Dict[str, str]) の場合
    if isinstance(data, dict):
        new_character_list: List[Character] = []
        default_voice = list(Voice)[0] # 不明なボイス名の場合のフォールバック

        for name, voice_name in data.items():
            try:
                # 文字列のボイス名から、対応するVoice Enumメンバーを取得
                # .upper()で大文字に統一し、堅牢性を高める
                voice_enum = Voice[voice_name.upper()]
            except (KeyError, AttributeError):
                # 設定ファイル上のボイス名がEnumに存在しない場合
                print(f"警告: ボイス名 '{voice_name}' が見つかりません。デフォルトのボイスを割り当てます。")
                voice_enum = default_voice

            # 新しいCharacterオブジェクトを生成。
            # 古い形式には存在しない属性は、空のデフォルト値で初期化。
            character = Character(
                name=name,
                voice=voice_enum,
                personality="",
                traits=[],
                speech_style="",
                verbal_tics=[]
                # background と role はデフォルトで None になる
            )
            new_character_list.append(character)
        
        return new_character_list

    # 3. 予期しない形式やNoneの場合は、空のリストを返す
    return []