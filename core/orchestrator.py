import time
from pathlib import Path
import traceback
import sys
from typing import Dict, List


try:
    from .models import (
        SpeechConfig, 
        Character
    )
    from .generators import SpeechGenerator
    from .api_client import ApiKeyManager
    from utils.ssml_utils import convert_dialog_to_ssml
    from utils.text_processing import (
        create_dialog, 
        get_ordered_characters, 
        add_ai_interjections
    )
except ImportError as e:
    print(f"モジュールのインポートエラー: {e}")

def generate_dialog_from_script(
        txt_file: Path, 
        dialog_output_dir: Path, 
        characters: List[Character], 
        text_client: 'GeminiApiClient') -> Path | None:
    """
    シナリオファイルから台本を生成し、ファイルに保存する。
    """
    print(f"INFO: Converting script '{txt_file.name}' to dialog...")

    try:
        with open(txt_file, 'r', encoding='utf-8-sig') as f:
            original_text = f.read()
    except Exception as e:
        print(f"ERROR: File read error: {e}")
        return None
    
    # create_dialog関数を呼び出し、text_clientを渡す
    script_dialog = create_dialog(original_text, characters, text_client)
    
    # 生成された内容が空でないかチェック
    if not script_dialog:
        print("ERROR: Dialog generation failed or returned empty content.")
        return None
        
    print("INFO: Dialog generation successful. Saving to file...")
    # print(script_dialog) # デバッグ用に生成内容を表示したい場合はコメントを外す

    try:
        # 出力先のファイルパスを定義
        dialog_output_path = dialog_output_dir / txt_file.name
        
        # ディレクトリが存在しない場合は作成
        dialog_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 正しい変数 `script_dialog` を使って書き込む
        with open(dialog_output_path, 'w', encoding='utf-8') as f:
            f.write(script_dialog)
        
        print(f"INFO: Dialog content saved to: {dialog_output_path}")
        return dialog_output_path # 成功したらファイルパスを返す

    except Exception as e:
        print(f"ERROR: Error saving Dialog file: {e}")
        return None

def generate_ssml_from_text(txt_file: Path, ssml_output_dir: Path, characters: List[Character], text_client) -> Path | None:
    """
    台本ファイルからSSMLを生成し、ファイルに保存する。
    Characterオブジェクトのリストを扱うように修正されています。
    成功した場合はSSMLファイルのPathオブジェクトを、失敗した場合は None を返す。
    """

    print("\n" + "="*50)
    print(f"--- DEBUG: generate_ssml_from_text に渡されたキャラクターリスト ---")
    if characters:
        for char in characters:
            print(f"  - 名前: {char.name}, ボイス: {char.voice.api_name}")
    else:
        print("  キャラクターリストが空またはNoneです。")
    print("="*50 + "\n")

    try:
        with open(txt_file, 'r', encoding='utf-8-sig') as f:
            original_dialog = f.read()
    except Exception as e:
        print(f"File read error: {e}")
        return None

    # --- 依存するヘルパー関数の呼び出しを、新しい形式に統一 ---

    # # 注意: add_ai_interjections 関数も List[Character] を受け取れるように修正が必要です
    # print("相槌・間を挿入しています...")
    # dialog_with_interjections = add_ai_interjections(original_dialog, characters, text_client)
    # print("\n--- 相槌挿入後の台本 ---\n" + dialog_with_interjections + "\n---------------------------------\n")

    dialog_with_interjections = original_dialog

    # 以前修正した get_ordered_characters を使用
    print("話者の登場順を特定しています...")
    ordered_characters = get_ordered_characters(dialog_with_interjections, characters)
    if not ordered_characters:
        print("テキストから既知のキャラクターが見つかりませんでした。処理を中断します。")
        return None
    
    # 注意: convert_dialog_to_ssml 関数も List[Character] を受け取れるように修正が必要です
    print("台本をSSMLに変換しています...")
    ssml_dialog = convert_dialog_to_ssml(dialog_with_interjections, ordered_characters)
    print(ssml_dialog)

    if not ssml_dialog or not ssml_dialog.strip('<speak></speak>\n '):
        print(f"SSMLの生成結果が空です ({txt_file.name})。")
        return None

    # --- SSMLをファイルに保存するロジック (この部分は変更不要) ---
    try:
        ssml_output_path = ssml_output_dir / txt_file.with_suffix(".ssml").name
        ssml_output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(ssml_output_path, 'w', encoding='utf-8') as f:
            f.write(ssml_dialog)
        
        print(f"SSMLをファイルに保存しました: {ssml_output_path}")
        return ssml_output_path

    except Exception as e:
        print(f"エラー: SSMLファイルの保存に失敗しました: {e}")
        return None

def generate_audio_from_ssml(
    ssml_file_path: Path,
    audio_output_dir: Path,
    characters: List[Character], # ★引数を speakers_dict から characters に変更
    speech_client
    ):
    """
    SSMLファイルから音声ファイルを生成する。
    Characterオブジェクトのリストを扱うように修正されています。
    """
    print(f"DEBUG: Entering generate_audio_from_ssml for {ssml_file_path.name}")
    
    try:
        with open(ssml_file_path, 'r', encoding='utf-8') as f:
            ssml_dialog_content = f.read()
    except Exception as e:
        print(f"エラー: SSMLファイル '{ssml_file_path}' の読み込みに失敗しました: {e}")
        return

    # ★変更点: SSMLの内容から「Characterオブジェクト」の登場順リストを再生成
    ordered_characters_for_audio = get_ordered_characters(ssml_dialog_content, characters)
    
    if not ordered_characters_for_audio:
        print("SSMLから既知のキャラクターが見つかりませんでした。音声生成を中断します。")
        return
    
    speakers_for_audio = {char.name: char.voice.api_name for char in ordered_characters_for_audio}
    print(speakers_for_audio)
    speech_config = SpeechConfig(speakers=speakers_for_audio)

    # SpeechGeneratorの呼び出し
    dialog_generator = SpeechGenerator(
        api_conn=speech_client, 
        speech_config=speech_config,
        ssml_dialog=ssml_dialog_content,
        parent=audio_output_dir, 
        basename=ssml_file_path.stem
    )

    print("音声を生成しています...")
    dialog_generator.generate()
    print(f"音声ファイルの生成が完了しました: {ssml_file_path.stem}.mp3")

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