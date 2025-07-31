import time
from pathlib import Path
import traceback
import sys

# 必要なモジュールをインポート
# ... (既存のインポート文はそのまま) ...
try:
    from .configs import SpeechConfig # SpeechConfig をインポート
    from .generators import SpeechGenerator
    from .api_client import ApiKeyManager
    from utils.ssml_utils import convert_dialog_to_ssml
    from utils.text_processing import get_ordered_speakers, add_ai_interjections
except ImportError as e:
    print(f"モジュールのインポートエラー: {e}")

def generate_ssml_from_text(txt_file: Path, ssml_output_dir: Path, speakers_dict: dict, text_client) -> Path | None:
    """
    台本ファイルからSSMLを生成し、ファイルに保存する。
    成功した場合はSSMLファイルのPathオブジェクトを、失敗した場合は None を返す。
    """
    print(f"DEBUG: Entering generate_ssml_from_text for {txt_file.name}")

    try:
        with open(txt_file, 'r', encoding='utf-8-sig') as f:
            original_dialog = f.read()
    except Exception as e:
        print(f"File read error: {e}")
        return None

    print("check and insert interjections...")
    dialog_with_interjections = add_ai_interjections(original_dialog, speakers_dict, text_client)
    print("\n--- Script with Interjections ---\n" + dialog_with_interjections + "\n---------------------------------\n")

    print("ordering speakers...")
    ordered_speaker_dict = get_ordered_speakers(dialog_with_interjections, speakers_dict)
    if not ordered_speaker_dict:
        print("No known speakers found in the text. Aborting.")
        return None
    
    print("converting dialog to ssml...")
    ssml_dialog = convert_dialog_to_ssml(dialog_with_interjections, ordered_speaker_dict)
    print(ssml_dialog)

    if not ssml_dialog or not ssml_dialog.strip('<speak></speak>\n '):
        print(f"SSML generation resulted in empty content for {txt_file.name}.")
        return None

    # ★追加: SSMLをファイルに保存するロジック
    try:
        # 出力先のSSMLファイルパスを定義
        ssml_output_path = ssml_output_dir / txt_file.with_suffix(".ssml").name
        
        # ディレクトリが存在しない場合は作成
        ssml_output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(ssml_output_path, 'w', encoding='utf-8') as f:
            f.write(ssml_dialog)
        
        print(f"SSML content saved to: {ssml_output_path}")
        return ssml_output_path # 成功したらファイルパスを返す

    except Exception as e:
        print(f"Error saving SSML file: {e}")
        return None

def generate_audio_from_ssml(
    ssml_file_path: Path, # ★変更: SSML文字列の代わりにファイルパスを受け取る
    audio_output_dir: Path,
    speakers_dict: dict, 
    speech_client
    ):
    """
    SSMLファイルから音声ファイルを生成する。
    """
    print(f"DEBUG: Entering generate_audio_from_ssml for {ssml_file_path.name}")
    
    # ★追加: SSMLファイルを読み込むロジック
    try:
        with open(ssml_file_path, 'r', encoding='utf-8') as f:
            ssml_dialog_content = f.read()
    except Exception as e:
        print(f"Error reading SSML file '{ssml_file_path}': {e}")
        return

    # SSMLの内容から話者リストを再生成
    ordered_speaker_dict_for_audio = get_ordered_speakers(ssml_dialog_content, speakers_dict)
    if not ordered_speaker_dict_for_audio:
        print("No known speakers found in the SSML. Aborting audio generation.")
        return

    speech_config = SpeechConfig(speakers=ordered_speaker_dict_for_audio)

    dialog_generator = SpeechGenerator(
        api_conn=speech_client, 
        speech_config=speech_config,
        ssml_dialog=ssml_dialog_content, # ★変更: 読み込んだ内容を渡す
        parent=audio_output_dir, 
        basename=ssml_file_path.stem # ★変更: SSMLファイルのステムをbasenameとして使用
    )

    print("generate sound dialog...")
    dialog_generator.generate()

def run_project_processing(config: dict, key_manager: ApiKeyManager):
    """プロジェクト全体を処理するCLIのメインフロー"""
    project_name = config.get("project_settings", {}).get("project_name", "Untitled Project")
    print(f"\nプロジェクト '{project_name}' の処理を開始します。")

    try:
        file_paths = config["file_paths"]
        root_path = Path(file_paths["root"])
        dialog_path = (root_path / file_paths.get("dialog", "../dialog")).resolve()
        audio_path = (root_path / file_paths.get("audio", "../audio")).resolve()
        
        print(f"Project Root: {root_path}")
        print(f"Dialogs from: {dialog_path}")
        print(f"Audio output to: {audio_path}")
        
        dialog_path.mkdir(parents=True, exist_ok=True)
        audio_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"エラー: プロジェクトのパス解決中に問題が発生しました。: {e}")
        return

    text_files = list(dialog_path.glob("*.txt"))
    if not text_files:
        print(f"エラー: 入力フォルダ '{dialog_path}' が空です。台本(.txt)ファイルを配置してください。")
        return

    for txt_file in text_files:
        current_api_key = key_manager.get_next_key()
        process_drama_file(txt_file, audio_path, config, current_api_key)
        
        wait_seconds = config.get("processing_settings", {}).get("wait_seconds", 30)
        print(f"\nWaiting {wait_seconds} seconds before processing next file...")
        time.sleep(wait_seconds)
    
    print(f"\nプロジェクト '{project_name}' の処理が完了しました。")