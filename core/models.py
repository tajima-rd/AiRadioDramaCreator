# AiRadioDramaCreator/core/models.py
from google.genai import types

from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import (
    List, 
    Dict, 
    Union, 
    Any, 
    Optional
)

@dataclass
class TextParams:
    temperature: float = 0.8
    top_p: float = 0.95
    max_output_tokens: int = 8192
    thinking_budget: int = -1
    # 今後、テキスト生成に関するパラメータが増えたらここに追加する

@dataclass
class SpeechParams:
    temperature: float = 1.0
    # 今後、音声生成に関する共通パラメータが増えたらここに追加する

@dataclass
class Script:
    order: int
    voice: str
    text : str

    def get_line(self):
        return "{self.voice}: {text}\n\n"

class Voice(Enum):
    """
    利用可能な話者の情報を定義する列挙型。    
    使用例:
    Voice.ACHERNAR.api_name
    """
    def __init__(
                self, 
                api_name: str, 
                description: str, 
                gender: str
            ):

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

class SceneConfig(ABC):
    """
    あらゆる生成タスクの設定を構築するための汎用的な抽象基底クラス。
    各モダリティは独立したパラメータオブジェクトによって設定される。
    """
    def __init__(self,
                 speech_params: Optional[SpeechParams] = None,
                 text_params: Optional[TextParams] = None,
                 scene_prompt: Optional[str] = None
                ):
        """
        Args:
            speech_params (Optional[SpeechParams]): 音声生成用のパラメータオブジェクト。
            text_params (Optional[TextParams]): テキスト生成用のパラメータオブジェクト。
            scene_prompt (Optional[str]): このシーンの設定を微調整するための共通プロンプト。
        """
        self.speech_params = speech_params
        self.text_params = text_params
        self.scene_prompt = scene_prompt

        # 渡されたパラメータオブジェクトに基づいて、このインスタンスがサポートする
        # モダリティを動的に決定する。
        self.modalities: List[str] = []
        if self.speech_params is not None:
            self.modalities.append("audio")
        if self.text_params is not None:
            self.modalities.append("text")

        # どちらのパラメータも渡されなかった場合はエラー
        if not self.modalities:
            raise ValueError("speech_params または text_params の少なくとも一方は提供される必要があります。")

    def get_speech_config(self) -> types.GenerateContentConfig:
        """
        音声生成用のGenerateContentConfigオブジェクトを構築して返す。
        """
        if "audio" not in self.modalities:
            raise AttributeError("このシーン設定に speech_params は提供されていません。")
        return self._build_speech_config()

    def get_text_config(self) -> types.GenerateContentConfig:
        """
        テキスト生成用のGenerateContentConfigオブジェクトを構築して返す。
        """
        if "text" not in self.modalities:
            raise AttributeError("このシーン設定に text_params は提供されていません。")
        return self._build_text_config()

    @abstractmethod
    def _build_speech_config(self) -> types.GenerateContentConfig:
        """
        【サブクラスで実装】音声生成用の設定オブジェクトを具体的に構築する。
        self.speech_params と、サブクラス固有の情報（話者など）を使用する。
        """
        pass

    @abstractmethod
    def _build_text_config(self) -> types.GenerateContentConfig:
        """
        【サブクラスで実装】テキスト生成用の設定オブジェクトを具体的に構築する。
        self.text_params を使用する。
        """
        pass

class Monolog(SceneConfig):
    """
    一人語り（独白）シーンの設定を定義するクラス。
    単一話者での音声生成と、テキスト生成の設定構築ロジックを担当する。
    """
    def __init__(self,
                 speaker: Character,
                 speech_params: Optional[SpeechParams] = None,
                 text_params: Optional[TextParams] = None,
                 scene_prompt: Optional[str] = None
                ):
        """
        Args:
            speaker (Character): 独白を行う単一のキャラクター。
            speech_params (Optional[SpeechParams]): 音声生成用のパラメータ。
            text_params (Optional[TextParams]): テキスト生成用のパラメータ。
            scene_prompt (Optional[str]): このシーンの設定を微調整するための共通プロンプト。
        """
        # 親クラスのコンストラクタを呼び出し、パラメータを初期化
        super().__init__(
            speech_params, 
            text_params, 
            scene_prompt
        )

        if not isinstance(speaker, Character):
            raise TypeError("speakerはCharacterオブジェクトである必要があります。")
        self.speaker = speaker

    def _build_speech_config(self) -> types.GenerateContentConfig:
        """
        【実装】単一話者向けの音声生成設定を構築する。
        """
        # 単一話者用のVoiceConfigオブジェクトを生成
        voice_config = types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=self.speaker.voice.api_name
            )
        )

        # 全体のGenerateContentConfigを構築して返す
        return types.GenerateContentConfig(
            temperature=self.speech_params.temperature,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=voice_config
            )
        )

    def _build_text_config(self) -> types.GenerateContentConfig:
        """
        【実装】テキスト生成設定を構築する。
        元のWriteConfigクラスが持っていたロジックをここに集約する。
        """
        # 全体のGenerateContentConfigを構築して返す
        return types.GenerateContentConfig(
            temperature=self.text_params.temperature,
            top_p=self.text_params.top_p,
            max_output_tokens=self.text_params.max_output_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.text_params.thinking_budget,
            )
        )

class Narration(SceneConfig):
    """
    ナレーションの設定を定義するクラス。
    単一話者での音声生成と、テキスト生成の設定構築ロジックを担当する。
    """
    def __init__(self,
                 speaker: Character,
                 speech_params: Optional[SpeechParams] = None,
                 text_params: Optional[TextParams] = None,
                 scene_prompt: Optional[str] = None
                ):
        """
        Args:
            speaker (Character): 独白を行う単一のキャラクター。
            speech_params (Optional[SpeechParams]): 音声生成用のパラメータ。
            text_params (Optional[TextParams]): テキスト生成用のパラメータ。
            scene_prompt (Optional[str]): このシーンの設定を微調整するための共通プロンプト。
        """
        # 親クラスのコンストラクタを呼び出し、パラメータを初期化
        super().__init__(
            speech_params, 
            text_params, 
            scene_prompt
        )

        if not isinstance(speaker, Character):
            raise TypeError("speakerはCharacterオブジェクトである必要があります。")
        self.speaker = speaker

    def _build_speech_config(self) -> types.GenerateContentConfig:
        """
        【実装】単一話者向けの音声生成設定を構築する。
        元のSpeechConfigクラスが持っていた単一話者用のロジックをここに集約する。
        """
        # 単一話者用のVoiceConfigオブジェクトを生成
        voice_config = types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=self.speaker.voice.api_name
            )
        )

        # 全体のGenerateContentConfigを構築して返す
        return types.GenerateContentConfig(
            temperature=self.speech_params.temperature,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=voice_config
            )
        )

    def _build_text_config(self) -> types.GenerateContentConfig:
        """
        【実装】テキスト生成設定を構築する。
        元のWriteConfigクラスが持っていたロジックをここに集約する。
        """
        # 全体のGenerateContentConfigを構築して返す
        return types.GenerateContentConfig(
            temperature=self.text_params.temperature,
            top_p=self.text_params.top_p,
            max_output_tokens=self.text_params.max_output_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.text_params.thinking_budget,
            )
        )

class Dialog(SceneConfig):
    """
    二人会話シーンの設定を定義するクラス。
    2人の登場人物に特化した設定構築ロジックを担当する。
    """
    def __init__(
                self,
                character_1: Character,
                character_2: Character,
                speech_params: Optional[SpeechParams] = None,
                text_params: Optional[TextParams] = None,
                scene_prompt: Optional[str] = None
            ):

        super().__init__(
            speech_params,
            text_params,
            scene_prompt
        )

        if not isinstance(character_1, Character):
            raise TypeError("character_1 はCharacterオブジェクトである必要があります。")
        
        if not isinstance(character_2, Character):
            raise TypeError("character_2 はCharacterオブジェクトである必要があります。")

        # ★★★ 修正点 ★★★
        # 登場人物を個別の変数として保持し、意図を明確化する
        self.character_1 = character_1
        self.character_2 = character_2


    def _build_speech_config(self) -> types.GenerateContentConfig:
        """
        【実装】二人会話向けの音声生成設定を構築する。
        """
        # ★★★ 修正点 ★★★
        # 2人の登場人物から設定リストを構築する
        characters_in_dialog = [self.character_1, self.character_2]

        speaker_config_list = [
            types.SpeakerVoiceConfig(
                speaker=char.name,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=char.voice.api_name
                    )
                )
            ) for char in characters_in_dialog
        ]

        multi_speaker_config = types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=speaker_config_list
        )
        
        return types.GenerateContentConfig(
            temperature=self.speech_params.temperature,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=multi_speaker_config
            )
        )

    def _build_text_config(self) -> types.GenerateContentConfig:
        """
        【実装】テキスト生成設定を構築する。
        """
        return types.GenerateContentConfig(
            temperature=self.text_params.temperature,
            top_p=self.text_params.top_p,
            max_output_tokens=self.text_params.max_output_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.text_params.thinking_budget,
            )
        )

class Discussion(SceneConfig):
    """
    複数人（3人以上）の会話シーンの設定を定義するクラス。
    SceneConfigを直接継承し、複数話者の設定構築ロジックを担当する。
    """
    def __init__(
                self,
                participants: List[Character],
                speech_params: Optional[SpeechParams] = None,
                text_params: Optional[TextParams] = None,
                scene_prompt: Optional[str] = None
            ):

        # 親クラスのコンストラクタを呼び出し、パラメータを初期化
        super().__init__(
            speech_params,
            text_params,
            scene_prompt
        )

        # ★★★ バリデーションを修正 ★★★
        if not isinstance(participants, list) or len(participants) < 3:
            raise ValueError("Discussionのparticipantsは3人以上のCharacterを含むリストである必要があります。")
        
        # 念のため、リストの中身もチェック
        if not all(isinstance(p, Character) for p in participants):
            raise TypeError("participantsリストのすべての要素はCharacterオブジェクトである必要があります。")

        self.participants = participants

    def _build_speech_config(self) -> types.GenerateContentConfig:
        """
        【実装】複数話者向けの音声生成設定を構築する。
        このロジックはDialogクラスと実質的に同じだが、独立して実装する。
        """
        # 複数話者用のSpeakerVoiceConfigリストを生成
        speaker_config_list = [
            types.SpeakerVoiceConfig(
                speaker=char.name,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=char.voice.api_name
                    )
                )
            ) for char in self.participants
        ]

        multi_speaker_config = types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=speaker_config_list
        )
        
        # ★★★ パラメータの参照元を修正 ★★★
        return types.GenerateContentConfig(
            temperature=self.speech_params.temperature,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=multi_speaker_config
            )
        )

    def _build_text_config(self) -> types.GenerateContentConfig:
        """
        【実装】テキスト生成設定を構築する。
        このロジックは話者の数に依存しない。
        """
        return types.GenerateContentConfig(
            temperature=self.text_params.temperature,
            top_p=self.text_params.top_p,
            max_output_tokens=self.text_params.max_output_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.text_params.thinking_budget,
            )
        )

class Scene:
    order: int

    def __init__(
            self,
            scene_config: SceneConfig,
            script: str
    ):
        self.scene_config = scene_config
        self.script = script

class Chapter:
    scenes:List[Scene]

    def __init__(self):
        self.scenes = list()
    
    def insert(self, scene):
        num = len(self.scenes)
        scene.order = num
        self.scenes.append(scene)

class Senario:
    def __init__(self, chapters, summary):
        self.chapters = chapters
        self.summary = summary
    
    def get_current_chapter(self):
        pass
    
    def get_previous_chapter(selfr):
        pass
    
    def get_next_chapter(self):
        pass

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
                print(self.model_config)
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
        print("Information: Single Speaker is selected.")
        if self.single_speaker_voice_config is not None:
            # GenerateContentConfigにはSpeechConfigオブジェクトを渡します
            return types.GenerateContentConfig(
                temperature = self.temperature,
                response_modalities = self.modalities,
                speech_config = types.SpeechConfig(
                    voice_config = self.single_speaker_voice_config.voice_config
                )
            )
        else:
            print("Warning: No speaker configuration provided. Using default content config.")
            return self._get_simple_config()
    
    def _get_multi_speaker_config(self):
        print("Information: Multi Speaker is selected.")
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
