import sys
from pathlib import Path

# 新しいモジュールをインポート
from core.orchestrator import run_project_processing
from utils.project_loader import load_project_from_file
from core.api_client import ApiKeyManager
from gui.run import run_gui

def main():
    """
    アプリケーションのエントリーポイント。
    引数に応じて CLI モードか GUI モードかを判断し、処理を委譲する。
    """
    if len(sys.argv) > 1:
        # --- CLI モード ---
        project_file_path = Path(sys.argv[1])
        config = load_project_config(project_file_path)
        if not config:
            sys.exit(1) # 設定読み込み失敗

        try:
            api_settings = config["api_settings"]
            default_index = api_settings.get("default_api_key_index", 1) - 1
            key_manager = ApiKeyManager(api_settings["api_keys"], default_index)
            
            # 処理の実行をオーケストレーターに委譲
            run_project_processing(config, key_manager)
            
        except Exception as e:
            print(f"エラー: 処理の準備中に問題が発生しました。 {e}")
            sys.exit(1)

    else:
        # --- GUI モード ---
        # GUIの起動をgui.runに委譲
        run_gui()

if __name__ == "__main__":
    main()