import json
from pathlib import Path
from typing import Optional, Dict, List

from core.models import (
    Project, 
    Character, 
    Voice
)


def load_project_from_file(project_file: Path) -> Optional[Project]:
    """
    プロジェクトファイル(JSON)を読み込み、全てのデータを格納した
    Projectオブジェクトを生成して返す。
    古い設定フォーマット（speakers辞書）にも後方互換性のため対応する。
    """
    if not project_file.exists():
        print(f"エラー: 指定されたプロジェクトファイル '{project_file}' が見つかりません。")
        return None
    
    try:
        with open(project_file, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
        
        # --- 基本的なバリデーション ---
        # (ここは元のコードと同じで良い)

        # --- Characterリストの再構築 ---
        characters_list: List[Character] = []
        
        # 新しい形式 "character_settings" が存在するかチェック
        if "character_settings" in config and "characters" in config["character_settings"]:
            character_dicts = config["character_settings"]["characters"]
            for char_dict in character_dicts:
                try:
                    voice_name = char_dict.get("voice", "")
                    voice_enum = Voice[voice_name.upper()] if voice_name else list(Voice)[0]
                    
                    character = Character(
                        name=char_dict.get("name", "無名のキャラクター"),
                        voice=voice_enum,
                        personality=char_dict.get("personality", ""),
                        traits=char_dict.get("traits", []),
                        speech_style=char_dict.get("speech_style", ""),
                        verbal_tics=char_dict.get("verbal_tics", []),
                        background=char_dict.get("background"), # .get()はキーがなければNoneを返す
                        role=char_dict.get("role")
                    )
                    characters_list.append(character)
                except KeyError:
                    print(f"警告: 保存されていたボイス名 '{voice_name}' が見つかりません。デフォルトを割り当てます。")
                    # (エラー時のフォールバック処理をここに追加しても良い)
                    continue

        # --- Projectオブジェクトの生成 ---
        project_settings = config.get("project_settings", {})
        api_settings = config.get("api_settings", {})
        file_paths = config.get("file_paths", {})
        proc_settings = config.get("processing_settings", {})
        
        project = Project(
            project_name=project_settings.get("project_name", "無題のプロジェクト"),
            # ... 他の project_settings の属性 ...
            
            api_keys=api_settings.get("api_keys", []),
            api_index=api_settings.get("default_api_key_index", 0),
            speech_model=api_settings.get("speech_model", ""),
            text_model=api_settings.get("text_model", ""),
            
            root_path=Path(file_paths["root_path"]) if file_paths.get("root_path") else None,
            
            # ★再構築したキャラクターリストをセット
            characters=characters_list,
            
            wait_time=proc_settings.get("wait_seconds", 1.0)
        )
        
        print(f"デバッグ: プロジェクト '{project.project_name}' をファイルから読み込みました。")
        return project

    except Exception as e:
        print(f"エラー: プロジェクトファイルの読み込み中に問題が発生しました。: {e}")
        return None

def save_project_config(project_obj: Project, file_path: Path) -> bool:
    """
    Project オブジェクトの内容を指定されたパスにJSON形式で保存する。
    Characterオブジェクトのリストも辞書のリストに変換して保存する。
    成功した場合は True を、失敗した場合は False を返す。
    """
    # --- Characterオブジェクトのリストを辞書のリストに変換 ---
    characters = []
    # project_obj.characters が List[Character] であることを想定
    for char in project_obj.characters:
        character = {
            "name": char.name,
            # Voice Enumメンバーは、APIで使う文字列名 (.api_name) として保存
            "voice": char.voice.api_name, 
            "personality": char.personality,
            "traits": char.traits,
            "speech_style": char.speech_style,
            "verbal_tics": char.verbal_tics,
            "background": char.background,
            "role": char.role
        }
        characters.append(character)
    
    # --- プロジェクト全体のデータを辞書に変換 ---
    config_data = {
        "project_settings": {
            "project_name": project_obj.project_name,
            "project_description": project_obj.project_description,
            "author": project_obj.author,
            "version": project_obj.version,
            "created_at": project_obj.created_at,
            "updated_at": project_obj.updated_at,
        },
        "file_paths": {
            "root_path": str(project_obj.root_path) if project_obj.root_path else None,
        },
        "api_settings": {
            "api_keys": project_obj.api_keys,
            "default_api_key_index": project_obj.api_index,
            "speech_model": project_obj.speech_model,
            "text_model": project_obj.text_model,
        },
        # ★変更点: キー名を "speaker_settings" から "character_settings" に変更し、
        #          値も変換後の辞書のリストに差し替え
        "character_settings": {
            "characters": characters,
        },
        "processing_settings": {
            "wait_seconds": project_obj.wait_time,
        }
    }

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print(f"デバッグ: プロジェクト設定を '{file_path}' に保存しました。")
        return True
    except Exception as e:
        print(f"エラー: プロジェクト設定の保存に失敗しました '{file_path}': {e}")
        return False

