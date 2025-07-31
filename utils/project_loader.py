import json
from pathlib import Path
from typing import Optional

from core.configs import Project # Project クラスをインポート


def load_project_config(project_file: Path) -> Optional[dict]:
    """
    プロジェクトファイル(JSON)を読み込み、設定を辞書として返す。
    """
    if not project_file.exists():
        print(f"エラー: 指定されたプロジェクトファイル '{project_file}' が見つかりません。")
        return None
    
    try:
        with open(project_file, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
        
        if "file_paths" not in config or "root_path" not in config["file_paths"]:
            print(f"エラー: '{project_file.name}' に 'file_paths' と 'root' の設定がありません。")
            return None
            
        api_keys = config.get("api_settings", {}).get("api_keys", [])
        if not any(key and not key.isspace() and "ここに" not in key for key in api_keys):
            print(f"警告!!: '{project_file.name}' に有効なAPIキーが設定されていません。")
            
        return config
    except Exception as e:
        print(f"エラー: プロジェクトファイルの読み込み中に問題が発生しました。: {e}")
        return None

def save_project_config(project_obj: Project, file_path: Path) -> bool:
    """
    Project オブジェクトの内容を指定されたパスにJSON形式で保存する。
    成功した場合は True を、失敗した場合は False を返す。
    """
    # Projectオブジェクトの属性をJSONにシリアライズ可能な辞書に変換
    config_data = {
        "project_settings": {
            "project_name": project_obj.project_name,
            "project_description": project_obj.project_description,
            "author": project_obj.author,
            "version": project_obj.version,
            "created_at": project_obj.created_at, # ISOフォーマット文字列
            "updated_at": project_obj.updated_at, # ISOフォーマット文字列
        },
        "file_paths": {
            # root_path は Path オブジェクトなので文字列に変換
            "root_path": str(project_obj.root_path) if project_obj.root_path else None, 
        },
        "api_settings": {
            "api_keys": project_obj.api_keys,
            "default_api_key_index": project_obj.api_index,
            "speech_model": project_obj.speech_model,
            "text_model": project_obj.text_model,
        },
        "speaker_settings": {
            "speakers": project_obj.speakers,
        },
        "processing_settings": {
            "wait_seconds": project_obj.wait_time,
        }
    }

    try:
        # ディレクトリが存在しない場合は作成
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False) # indentで整形、ensure_ascii=Falseで日本語表示
        print(f"デバッグ: プロジェクト設定を '{file_path}' に保存しました。")
        return True
    except Exception as e:
        print(f"エラー: プロジェクト設定の保存に失敗しました '{file_path}': {e}")
        return False
