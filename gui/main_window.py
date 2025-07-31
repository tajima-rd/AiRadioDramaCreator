import os, sys
import time
import shutil # ← この行を追加
from datetime import datetime
import traceback
from pathlib import Path
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit, QMessageBox,
    QFormLayout, QListWidget, QListWidgetItem, QAbstractItemView,
    QDialog
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal, Qt, QUrl
from PyQt6.QtGui import QAction, QColor, QTextCursor, QDesktopServices

from .app_ui_setup import setup_main_ui
from .dialogs import SettingsDialog, SpeakerDialog

try:
    from core.configs import Project
    from core.orchestrator import generate_dialog_from_script, generate_ssml_from_text, generate_audio_from_ssml
    from utils.project_loader import load_project_config, save_project_config
    from core.api_client import ApiKeyManager
    from core.api_client import GeminiApiClient
except ImportError as e:
    print(f"モジュールのインポートエラー: {e}")
    print("core/orchestrator.py, utils/project_loader.py, core/api_client.py がパス上に存在するか確認してください。")

STATUS_COLOR = {
    "WAITING": QColor("orange"), "PROCESSING": QColor("blue"),
    "SUCCESS": QColor("green"), "ERROR": QColor("red"),
    "INTERRUPTED": QColor("gray"), "DEFAULT": QColor("black")
}

project: Project = None
project_file_path = None
api_key_manager: ApiKeyManager = None 
speech_client: GeminiApiClient = None
text_client: GeminiApiClient = None

class DialogCreationWorker(QObject):
    """シナリオファイルから台本ファイルを生成するためのWorkerクラス"""
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    file_status_update = pyqtSignal(str, str)
    dialog_list_updated = pyqtSignal()

    def __init__(self, files_to_process: List[Path]):
        super().__init__()
        self.files_to_process = files_to_process
        self.is_running = True

    def run(self):
        """台本生成処理を実行します。"""
        global project, text_client
        try:
            if project is None or text_client is None:
                self.error.emit("エラー: プロジェクトまたはテキストAPIクライアントが初期化されていません。\n")
                return

            dialog_output_dir = (project.root_path / "dialog").resolve()
            self.progress.emit("--- 台本ファイルの生成を開始します ---\n")

            for i, script_file in enumerate(self.files_to_process):
                if not self.is_running:
                    self.file_status_update.emit(script_file.name, "INTERRUPTED")
                    break
                
                try:
                    self.progress.emit(f"\n[{i+1}/{len(self.files_to_process)}] 台本生成中: {script_file.name}\n")
                    self.file_status_update.emit(script_file.name, "PROCESSING")

                    # インポートしたバックエンド関数を呼び出す
                    saved_dialog_path = generate_dialog_from_script(
                        script_file,
                        dialog_output_dir,
                        project.speakers,
                        text_client
                    )

                    if saved_dialog_path:
                        self.progress.emit(f"台本生成成功: {saved_dialog_path.name}\n")
                        self.file_status_update.emit(script_file.name, "SUCCESS")
                    else:
                        self.error.emit(f"ファイル'{script_file.name}'の台本生成に失敗しました。\n")
                        self.file_status_update.emit(script_file.name, "ERROR")
                
                except Exception as e:
                    self.error.emit(f"台本生成中に予期せぬエラーが発生 ({script_file.name}): {e}\n{traceback.format_exc()}\n")
                    self.file_status_update.emit(script_file.name, "ERROR")

            self.progress.emit("\n選択されたファイルの台本生成処理が完了しました。\n")

        except Exception as e:
            self.error.emit(f"致命的なエラーが発生しました: {e}\n{traceback.format_exc()}\n")
        finally:
            self.dialog_list_updated.emit() # 完了後にダイアログリストの更新を通知
            self.finished.emit()

    def stop(self):
        """処理の中断を要求します。"""
        self.progress.emit("台本生成処理の中断命令を受け付けました。\n")
        self.is_running = False

class SsmlCreationWorker(QObject):
    """ダイヤログファイルからSSMLファイルを生成するためのWorkerクラス"""
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    file_status_update = pyqtSignal(str, str) # 処理対象のファイル名とステータスを通知
    ssml_list_updated = pyqtSignal()          # 処理完了時にSSMLリストの更新を通知

    def __init__(self, files_to_process: List[Path]):
        super().__init__()
        self.files_to_process = files_to_process
        self.is_running = True

    def run(self):
        """SSML生成処理を実行します。"""
        global project, text_client
        try:
            if project is None or text_client is None:
                self.error.emit("エラー: プロジェクトまたはテキストAPIクライアントが初期化されていません。\n")
                return

            ssml_output_dir = (project.root_path / "ssml").resolve()
            self.progress.emit("\n--- SSMLファイルの生成を開始します ---\n")

            for i, txt_file in enumerate(self.files_to_process):
                if not self.is_running:
                    self.file_status_update.emit(txt_file.name, "INTERRUPTED")
                    break
                
                try:
                    self.progress.emit(f"\n[{i+1}/{len(self.files_to_process)}] SSML生成中: {txt_file.name}\n")
                    self.file_status_update.emit(txt_file.name, "PROCESSING")

                    saved_ssml_path = generate_ssml_from_text(
                        txt_file, ssml_output_dir, project.speakers, text_client
                    )

                    if saved_ssml_path:
                        self.progress.emit(f"SSML生成成功: {saved_ssml_path.name}\n")
                        self.file_status_update.emit(txt_file.name, "SUCCESS")
                    else:
                        self.error.emit(f"ファイル'{txt_file.name}'のSSML生成に失敗しました。\n")
                        self.file_status_update.emit(txt_file.name, "ERROR")
                
                except Exception as e:
                    self.error.emit(f"SSML生成中に予期せぬエラーが発生 ({txt_file.name}): {e}\n{traceback.format_exc()}\n")
                    self.file_status_update.emit(txt_file.name, "ERROR")
            
            self.progress.emit("\n選択されたファイルのSSML生成処理が完了しました。\n")

        except Exception as e:
            self.error.emit(f"致命的なエラーが発生しました: {e}\n{traceback.format_exc()}\n")
        finally:
            self.ssml_list_updated.emit() # 完了後にリスト更新を通知
            self.finished.emit()

    def stop(self):
        """処理の中断を要求します。"""
        self.is_running = False

class AudioCreationWorker(QObject):
    """SSMLファイルから音声ファイルを生成するためのWorkerクラス"""
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    file_status_update = pyqtSignal(str, str) # 処理対象のファイル名とステータスを通知
    audio_list_updated = pyqtSignal()         # ファイルごとの処理完了時に音声リストの更新を通知

    def __init__(self, files_to_process: List[Path]):
        super().__init__()
        self.files_to_process = files_to_process
        self.is_running = True

    def run(self):
        """音声生成処理を実行します。"""
        global project, speech_client
        try:
            if project is None or speech_client is None:
                self.error.emit("エラー: プロジェクトまたは音声APIクライアントが初期化されていません。\n")
                return

            audio_output_dir = (project.root_path / "audio").resolve()
            self.progress.emit("\n--- 音声ファイルの生成を開始します ---\n")

            for i, ssml_file in enumerate(self.files_to_process):
                if not self.is_running:
                    self.file_status_update.emit(ssml_file.name, "INTERRUPTED")
                    break
                
                status = "ERROR"
                try:
                    self.progress.emit(f"\n[{i+1}/{len(self.files_to_process)}] 音声生成中: {ssml_file.name}\n")
                    self.file_status_update.emit(ssml_file.name, "PROCESSING")

                    generate_audio_from_ssml(
                        ssml_file, audio_output_dir, project.speakers, speech_client
                    )
                    status = "SUCCESS"
                except Exception as e:
                    self.error.emit(f"音声生成中に予期せぬエラーが発生 ({ssml_file.name}): {e}\n{traceback.format_exc()}\n")
                    status = "ERROR"
                finally:
                    if not self.is_running: status = "INTERRUPTED"
                    self.file_status_update.emit(ssml_file.name, status)
                    self.audio_list_updated.emit()

                wait_seconds = project.wait_time
                if not isinstance(wait_seconds, (int, float)):
                    self.error.emit(f"警告: 'wait_seconds' の値が数値ではありません。デフォルト値 (30秒) を使用します。\n")
                    wait_seconds = 30

                if i < len(self.files_to_process) - 1 and self.is_running:
                    self.progress.emit(f"{wait_seconds}秒待機します...\n")
                    for _ in range(int(wait_seconds)):
                        if not self.is_running: break
                        time.sleep(1)

            self.progress.emit("\n選択されたファイルの音声生成処理が完了しました。\n")
        except Exception as e:
            self.error.emit(f"致命的なエラーが発生しました: {e}\n{traceback.format_exc()}\n")
        finally:
            self.finished.emit()

    def stop(self):
        """処理の中断を要求します。"""
        self.is_running = False

class AppGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ai Radio Drama Creator")
        self.setGeometry(100, 100, 800, 700)
        self.worker = None
        self.thread = None
        self.init_ui()

    def init_ui(self):
        """
        GUIの主要なUI要素を初期化し、イベントハンドラを接続します。
        """
        ui_elements_dict = setup_main_ui(self)

        # メニューのアクション
        ui_elements_dict["new_action"].triggered.connect(self.new_project)
        ui_elements_dict["open_action"].triggered.connect(self.open_project_file)
        ui_elements_dict["settings_api_action"].triggered.connect(self.show_settings_dialog)
        ui_elements_dict["settings_speaker_action"].triggered.connect(self.show_speaker_dialog)
        ui_elements_dict["import_scenario_action"].triggered.connect(self.import_scenario_files)

        # 各処理ステージのボタンにメソッドを接続
        self.start_dialog_creation_btn.clicked.connect(self.start_dialog_creation)
        self.stop_dialog_creation_btn.clicked.connect(self.stop_processing)

        self.start_ssml_creation_btn.clicked.connect(self.start_ssml_creation)
        self.stop_ssml_creation_btn.clicked.connect(self.stop_processing)

        self.start_audio_creation_btn.clicked.connect(self.start_audio_creation)
        self.stop_audio_creation_btn.clicked.connect(self.stop_processing)
        self.open_project_btn.clicked.connect(self.open_project_folder)

    def save_project_config_to_file(self):
        global project, project_file_path # グローバル変数を参照

        if project is None or project_file_path is None:
            self.update_log("警告: プロジェクト情報またはファイルパスが未設定のため、設定を保存できません。\n")
            return False

        # 現在の日時でupdated_atを更新
        from datetime import datetime
        project.updated_at = datetime.now().isoformat()

        if save_project_config(project, project_file_path):
            self.update_log(f"デバッグ: プロジェクト設定を '{project_file_path.name}' に保存しました。\n")
            return True
        else:
            self.update_log(f"エラー: プロジェクト設定の保存に失敗しました '{project_file_path.name}'。\n")
            QMessageBox.critical(self, "保存エラー", "プロジェクト設定の保存に失敗しました。")
            return False

    def show_settings_dialog(self):
        global project, api_key_manager, speech_client, text_client

        if project is None:
            QMessageBox.warning(self, "設定エラー", "プロジェクトが読み込まれていません。API設定を表示できません。")
            return

        # ダイアログの初期値を現在のプロジェクト設定から取得
        initial_api_keys = project.api_keys
        default_index = project.api_index
        initial_speech_model = project.speech_model
        initial_text_model = project.text_model

        dialog = SettingsDialog(initial_api_keys, default_index, initial_speech_model, initial_text_model, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_api_keys, new_default_index, new_speech_model, new_text_model = dialog.get_settings()
            
            # project グローバル変数を更新
            project.api_keys = new_api_keys
            project.api_index = new_default_index
            project.speech_model = new_speech_model
            project.text_model = new_text_model

            self.save_project_config_to_file()

            self.update_log("デバッグ: API/モデル設定が更新されました。\n")
            # APIキーやモデルが変更された場合、APIクライアントを再初期化
            self.initialize_api_clients()
            
            # 設定変更がプロジェクト名ラベルに影響しないが、ログに出力
            self.update_log(f"APIキー: {new_api_keys}\n音声モデル: {new_speech_model}\nテキストモデル: {new_text_model}\n")

    def show_speaker_dialog(self):
        global project

        if project is None:
            QMessageBox.warning(self, "設定エラー", "プロジェクトが読み込まれていません。話者設定を表示できません。")
            return

        # ダイアログの初期値を現在のプロジェクト設定から取得
        initial_speakers = project.speakers

        dialog = SpeakerDialog(initial_speakers, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_speakers = dialog.get_speakers()

            # project グローバル変数を更新
            project.speakers = new_speakers

            self.update_log("デバッグ: 話者設定が更新されました。\n")
            # 話者設定はAPIクライアントの再初期化には通常影響しない
            # ただし、process_drama_file は project.speakers を参照する。
            self.update_log(f"更新された話者: {new_speakers}\n")

    def initialize_api_clients(self):
        global project, api_key_manager, speech_client, text_client # グローバル変数を変更するためにglobal宣言

        if project is None:
            self.update_log("エラー: Project設定が初期化されていません。APIクライアントを初期化できません。\n")
            return

        try:
            # ProjectインスタンスからAPIキーとモデル名を取得
            api_keys_list = project.api_keys
            default_index = project.api_index
            speech_model_name = project.speech_model
            text_model_name = project.text_model

            if not api_keys_list:
                self.update_log("警告: APIキーが設定されていません。APIクライアントを初期化できません。\n")
                return

            # ApiKeyManagerをインスタンス化（これによりdefault_api_keyが設定される）
            api_key_manager = ApiKeyManager(api_keys_list, default_index)
            
            # デフォルトAPIキーを取得
            default_api_key_str = api_key_manager.default_api_key
            self.update_log(f"デバッグ: initialize_api_clients: デフォルトAPIキー文字列: '{default_api_key_str[:5]}...' (隠蔽)\n")

            # GeminiApiClientのインスタンスを生成し、グローバル変数に代入
            speech_client = GeminiApiClient(default_api_key_str, speech_model_name)
            text_client = GeminiApiClient(default_api_key_str, text_model_name)

            self.update_log(f"デバッグ: グローバルな speech_client (型: {type(speech_client)}) と text_client (型: {type(text_client)}) を初期化しました。\n")
        except Exception as e:
            self.update_log(f"エラー: グローバルAPIクライアントの初期化中に問題が発生しました: {e}\n")
            self.update_log(f"詳細エラー情報:\n{traceback.format_exc()}\n")
            # 初期化失敗時はNoneに戻す
            speech_client = None
            text_client = None        

    def new_project(self):
        global project, project_file_path

        self.update_log("新規プロジェクトの作成を開始します。\n")
        
        # ユーザーに新しいプロジェクトのルートディレクトリを選択させる (または作成させる)
        # デフォルトのパスをユーザーのホームディレクトリに設定
        project_root_str = QFileDialog.getExistingDirectory(
            self,
            "新規プロジェクトの保存先フォルダを選択または作成してください",
            str(Path.home()) 
        )

        if not project_root_str:
            self.update_log("新規プロジェクトの作成がキャンセルされました。\n")
            return
        
        project_root_dir = Path(project_root_str)
        # プロジェクトファイルは選択されたフォルダの直下に "project.json" として作成
        new_project_json_path = project_root_dir / "project.json"

        # 必要なサブフォルダを作成 (dialog, ssml, audio)
        try:
            dialog_dir = project_root_dir / "dialog"
            ssml_dir = project_root_dir / "ssml"
            audio_dir = project_root_dir / "audio"
            persona_dir = project_root_dir / "persona"
            script_dir = project_root_dir / "script"

            dialog_dir.mkdir(parents=True, exist_ok=True)
            ssml_dir.mkdir(parents=True, exist_ok=True)
            audio_dir.mkdir(parents=True, exist_ok=True)
            persona_dir.mkdir(parents=True, exist_ok=True)
            script_dir.mkdir(parents=True, exist_ok=True)
            self.update_log(f"プロジェクトフォルダ '{project_root_dir.name}' と必要なサブフォルダを作成しました。\n")
        except Exception as e:
            QMessageBox.critical(self, "フォルダ作成エラー", f"必要なフォルダの作成に失敗しました: {e}")
            self.update_log(f"エラー: フォルダ作成失敗: {e}\n")
            return

        # デフォルトのProjectオブジェクトを作成し、グローバル変数に代入
        now_iso = datetime.now().isoformat()
        default_project = Project(
            project_name=project_root_dir.name, # フォルダ名をプロジェクト名とする
            project_description="新しいAi Radio Dramaプロジェクト",
            author="unknown",
            version="1.0.0",
            api_keys=[], # APIキーは後で設定ダイアログで入力してもらう
            api_index=None, 
            speech_model="gemini-2.5-flash-preview-tts", # デフォルトのモデル名
            text_model="gemini-2.5-flash",   # デフォルトのモデル名
            created_date=now_iso,
            updated_date=now_iso,
            root_path=project_root_dir, # Projectオブジェクトのroot_pathは選択されたディレクトリ
            speakers={}, # 話者設定は後で設定ダイアログで入力してもらう
            wait_time=30
        )

        # グローバル変数を更新
        project = default_project
        project_file_path = new_project_json_path
        
        # 新しいプロジェクト設定をファイルに保存
        if self.save_project_config_to_file():
            self.update_log(f"新規プロジェクト '{project.project_name}' を作成し、'{project_file_path.name}' に保存しました。\n")
            # GUIを新しいプロジェクト情報で更新 (ファイルリストなどもリフレッシュされる)
            self.load_project_info()
        else:
            self.update_log("エラー: 新規プロジェクトの保存に失敗しました。\n")
            QMessageBox.critical(self, "エラー", "新規プロジェクト設定の保存に失敗しました。")

    def open_project_file(self):
        global project_file_path

        # プログラムの実行パスを取得
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(sys.argv[0]))

        # QFileDialogを開く際のデフォルトディレクトリとして、取得したパスを設定
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "プロジェクトファイルを選択",
            application_path,
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            project_file_path = Path(file_path)
            self.load_project_info()
        else:
            self.update_log("プロジェクトファイルの選択がキャンセルされました。\n")

    def load_project_info(self):
        """
        プロジェクト情報を設定ファイルから読み込み、GUIコンポーネントを更新します。
        グローバル変数 `project` をインスタンス化し、関連情報を設定します。
        """
        global project

        self.log_box.clear()
        self.start_audio_creation_btn.setEnabled(False)
        self.start_dialog_creation_btn.setEnabled(False)
        self.start_ssml_creation_btn.setEnabled(False)
        self.start_audio_creation_btn.setEnabled(False)

        global project_file_path # グローバル変数を参照
        if project_file_path is None:
            self.update_log("エラー: プロジェクトファイルパスが設定されていません。\n")
            QMessageBox.critical(self, "エラー", "プロジェクトファイルパスが未設定です。")
            self.start_audio_creation_btn.setEnabled(True)
            return
        json_config = load_project_config(project_file_path)

        if not json_config:
            self.update_log("エラー: プロジェクト設定が読み込まれていません。\n")
            QMessageBox.critical(self, "エラー", "プロジェクトファイルの読み込みに失敗しました。") # エラーメッセージの表示
            self.start_audio_creation_btn.setEnabled(True)
            return

        # --- グローバル変数 `project` のインスタンス化と初期化 ---
        # configからProjectコンストラクタに必要なデータを抽出
        project_settings = json_config.get("project_settings", {})
        file_paths_conf = json_config.get("file_paths", {})
        api_settings = json_config.get("api_settings", {})
        speaker_settings = json_config.get("speaker_settings", {})
        processing_settings = json_config.get("processing_settings", {})

        try:
            global project # projectグローバル変数を変更するためにglobal宣言
            project = Project(
                project_name=project_settings.get("project_name", "名称未設定"),
                project_description=project_settings.get("project_description", ""),
                author=project_settings.get("author", ""),
                version=project_settings.get("version", ""),
                api_keys=api_settings.get("api_keys", []),
                api_index=api_settings.get("default_api_key_index"),
                speech_model=api_settings.get("speech_model"),
                text_model=api_settings.get("text_model"),
                created_date=project_settings.get("created_at"),
                updated_date=project_settings.get("updated_at"),
                root_path=file_paths_conf.get("root_path", ""), # 文字列として渡す
                speakers=speaker_settings.get("speakers", {}),
                wait_time=processing_settings.get("wait_seconds", 30)
            )
            self.update_log("デバッグ: グローバル変数 'project' が正常にインスタンス化されました。\n")
            self.update_log(f"デバッグ: Project.root_path: {project.root_path} (型: {type(project.root_path)})\n")

        except Exception as e:
            self.update_log(f"エラー: プロジェクト情報のインスタンス化中に問題が発生しました: {e}\n")
            self.update_log(f"詳細エラー情報:\n{traceback.format_exc()}\n")
            self.start_audio_creation_btn.setEnabled(True)
            return

        # GUIコンポーネントの更新 (すべて Project インスタンスから値を取得)
        self.project_name_label.setText(project.project_name)
        self.project_path_label.setText(str(project_file_path.name)) 

        # ファイルパス設定の読み込み（Project インスタンスから取得）
        current_root_path = project.root_path # Projectインスタンスから取得
        
        if not current_root_path: # Projectインスタンスのroot_pathがNoneの場合
            self.update_log("エラー: プロジェクト設定に有効な 'root_path' がありません。プロジェクトを読み込めません。\n")
            self.start_audio_creation_btn.setEnabled(True)
            return

        # root_pathはProjectクラスでPathオブジェクトになっていることを想定
        if not current_root_path.is_dir():
            self.update_log(f"警告: 設定されたルートパス '{current_root_path}' が存在しないか、ディレクトリではありません。\n")

        # ファイルリストの更新 (dialog_pathが有効な場合のみ)
        self.update_file_list(current_root_path / "script", self.scenario_file_list_widget, file_type="text", label="シナリオ")
        self.update_file_list(current_root_path / "dialog", self.dialog_file_list_widget, file_type="text", label="台本")
        self.update_file_list(current_root_path / "ssml", self.ssml_file_list_widget, file_type="ssml", label="SSML")
        self.update_file_list(current_root_path / "audio", self.audio_file_list_widget, file_type="audio", label="音声")
        
        # プロジェクトが正常に読み込めたらボタンを有効化
        self.start_dialog_creation_btn.setEnabled(True)
        self.start_ssml_creation_btn.setEnabled(True)
        self.start_audio_creation_btn.setEnabled(True)
        
        self.update_log(f"プロジェクト '{project.project_name}' を読み込みました。\n")
        self.initialize_api_clients()

    def open_project_folder(self):
        """
        現在開いているプロジェクトのルートフォルダをファイルエクスプローラーで開きます。
        """
        global project
        if project and project.root_path:
            if project.root_path.is_dir():
                # QDesktopServicesを使ってクロスプラットフォームに対応した形でフォルダを開く
                url = QUrl.fromLocalFile(str(project.root_path.resolve()))
                if QDesktopServices.openUrl(url):
                    self.update_log(f"プロジェクトフォルダ '{project.root_path}' を開きました。\n")
                else:
                    log_msg = f"エラー: プロジェクトフォルダ '{project.root_path}' を開けませんでした。\n"
                    self.update_log(log_msg)
                    QMessageBox.critical(self, "オープンエラー", log_msg)
            else:
                log_msg = f"エラー: プロジェクトフォルダのパス '{project.root_path}' が見つかりません。\n"
                self.update_log(log_msg)
                QMessageBox.warning(self, "パスエラー", log_msg)
        else:
            log_msg = "プロジェクトが読み込まれていないため、フォルダを開けません。\n"
            self.update_log(log_msg)
            QMessageBox.warning(self, "エラー", "先にプロジェクトを開いてください。")

    def import_scenario_files(self):
        """
        ファイルダイアログを開き、選択されたTXTファイルをプロジェクトのscriptフォルダにコピーする。
        """
        global project
        if not project:
            QMessageBox.warning(self, "インポートエラー", "プロジェクトが読み込まれていません。先にプロジェクトを開いてください。")
            return

        script_dir = project.root_path / "script"
        if not script_dir.is_dir():
            QMessageBox.critical(self, "エラー", f"プロジェクトのシナリオフォルダが見つかりません:\n{script_dir}")
            return

        # ファイルダイアログを開いて複数のファイルを選択させる
        file_paths_list, _ = QFileDialog.getOpenFileNames(
            self,
            "インポートするシナリオファイルを選択（複数選択可）",
            str(Path.home()),  # 初期ディレクトリをユーザーのホームに設定
            "テキストファイル (*.txt);;すべてのファイル (*)"
        )

        if not file_paths_list:
            # ファイルが選択されなかった（キャンセルされた）場合
            return

        imported_count = 0
        for src_path_str in file_paths_list:
            try:
                src_path = Path(src_path_str)
                dest_path = script_dir / src_path.name
                
                # ファイルをコピー (shutil.copy2 はメタデータもできるだけ保持する)
                shutil.copy2(src_path, dest_path)
                
                self.update_log(f"シナリオ '{src_path.name}' をインポートしました。\n")
                imported_count += 1
            except Exception as e:
                self.update_log(f"エラー: '{src_path.name}' のインポートに失敗しました: {e}\n")

        if imported_count > 0:
            self.update_log(f"--- {imported_count}件のシナリオファイルをインポートしました ---\n")
            # インポート後にシナリオファイルリストを更新
            self.update_scenario_list()

    def update_file_list(self, dir_path: Path, list_widget: QListWidget, file_type: str = "text", label: str = "ファイル"):
        list_widget.clear()
        if dir_path.is_dir():
            if file_type == "text":
                files = sorted([f for f in dir_path.glob("*.txt") if f.is_file()])
                suffix_label = f".txt {label}"
            elif file_type == "ssml":
                files = sorted([f for f in dir_path.glob("*.ssml") if f.is_file()])
                suffix_label = f".ssml {label}"
            elif file_type == "audio":
                files = sorted([f for f in dir_path.glob("*.mp3") if f.is_file()] + [f for f in dir_path.glob("*.wav") if f.is_file()])
                suffix_label = f".mp3/.wav {label}"
            else:
                files = []
                suffix_label = label

            if files:
                for f_path in files:
                    item = QListWidgetItem(f_path.name)
                    item.setData(Qt.ItemDataRole.UserRole, f_path)
                    list_widget.addItem(item)
            else:
                list_widget.addItem(f"（このフォルダに {suffix_label} はありません）")
        else:
            list_widget.addItem(f"（フォルダ '{dir_path.name}' が見つかりません）")

    def update_file_status(self, list_widget: QListWidget, file_path_name: str, status: str):
        """指定されたリストウィジェット内のアイテムの表示ステータスを更新する"""
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            path_data = item.data(Qt.ItemDataRole.UserRole)
            if path_data and path_data.name == file_path_name:
                status_text = {
                    "WAITING": "[待機中...]", "PROCESSING": "[処理中...]",
                    "SUCCESS": "[✔ 完了]", "ERROR": "[❌ エラー]",
                    "INTERRUPTED": "[⏹ 中断]",
                }.get(status, "")
                item.setText(f"{file_path_name} {status_text}")
                item.setForeground(STATUS_COLOR.get(status, STATUS_COLOR["DEFAULT"]))
                break

    def _start_worker_thread(self, worker_class, files_to_process, source_list_widget):
        """Workerスレッドを開始するための共通ロジック"""
        if not files_to_process:
            QMessageBox.warning(self, "選択エラー", "処理するファイルをリストから選択してください。")
            return

        if not project:
            QMessageBox.critical(self, "エラー", "プロジェクトが読み込まれていません。")
            return

        self.log_box.clear()
        self.set_processing_state(True) # すべての操作を無効化

        # 処理対象のアイテムのステータスを「待機中」に更新
        for file_path in files_to_process:
            self.update_file_status(source_list_widget, file_path.name, "WAITING")

        self.thread = QThread()
        self.worker = worker_class(files_to_process)
        self.worker.moveToThread(self.thread)

        # シグナルとスロットを接続
        self.worker.file_status_update.connect(
            lambda name, status: self.update_file_status(source_list_widget, name, status)
        )
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.update_log)
        self.worker.error.connect(self.update_log)
        self.thread.finished.connect(lambda: self.set_processing_state(False))

        # Workerの種類に応じて、リスト更新用のシグナルを接続
        if isinstance(self.worker, DialogCreationWorker):
            self.worker.dialog_list_updated.connect(self.update_dialog_list)
        elif isinstance(self.worker, SsmlCreationWorker):
            self.worker.ssml_list_updated.connect(self.update_ssml_list)
        elif isinstance(self.worker, AudioCreationWorker):
            # AudioCreationWorkerはファイルごとにリスト更新シグナルを出す
            self.worker.audio_list_updated.connect(self.update_audio_list)

        self.thread.start()

    def start_dialog_creation(self):
        selected_items = self.scenario_file_list_widget.selectedItems()
        files_to_process = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items if item.data(Qt.ItemDataRole.UserRole)]
        self._start_worker_thread(DialogCreationWorker, files_to_process, self.scenario_file_list_widget)

    def start_ssml_creation(self):
        selected_items = self.dialog_file_list_widget.selectedItems()
        files_to_process = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items if item.data(Qt.ItemDataRole.UserRole)]
        self._start_worker_thread(SsmlCreationWorker, files_to_process, self.dialog_file_list_widget)

    def start_audio_creation(self):
        selected_items = self.ssml_file_list_widget.selectedItems()
        files_to_process = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items if item.data(Qt.ItemDataRole.UserRole)]
        self._start_worker_thread(AudioCreationWorker, files_to_process, self.ssml_file_list_widget)

    def stop_processing(self):
        if self.worker and self.thread and self.thread.isRunning():
            self.worker.stop()
            self.update_log("\n中断命令を送信しました。現在の処理が終わり次第停止します。\n")
            # 中断ボタン自体も無効化し、二重クリックを防ぐ
            self.stop_dialog_creation_btn.setEnabled(False)
            self.stop_ssml_creation_btn.setEnabled(False)
            self.stop_audio_creation_btn.setEnabled(False)

    def set_processing_state(self, is_processing):
        """処理中のUIの状態を一括で設定する"""
        enabled = not is_processing
        # すべての開始ボタンの状態を設定
        self.start_dialog_creation_btn.setEnabled(enabled)
        self.start_ssml_creation_btn.setEnabled(enabled)
        self.start_audio_creation_btn.setEnabled(enabled)
        # すべての中断ボタンの状態を設定
        self.stop_dialog_creation_btn.setEnabled(is_processing)
        self.stop_ssml_creation_btn.setEnabled(is_processing)
        self.stop_audio_creation_btn.setEnabled(is_processing)
        # メニューバーの操作を制御
        self.menuBar().setEnabled(enabled)

    def update_scenario_list(self):
        """シナリオファイルリストを更新するスロット"""
        if project and project.root_path:
            scenario_path = project.root_path / "script"
            self.update_file_list(scenario_path, self.scenario_file_list_widget, file_type="text", label="シナリオ")
            self.update_log("シナリオファイルリストを更新しました。\n")

    def update_dialog_list(self):
        """台本ファイルリストを更新するスロット"""
        if project and project.root_path:
            dialog_path = project.root_path / "dialog"
            self.update_file_list(dialog_path, self.dialog_file_list_widget, file_type="text", label="台本")
            self.update_log("台本ファイルリストを更新しました。\n")

    def update_ssml_list(self):
        """SSMLファイルリストを更新するスロット"""
        if project and project.root_path:
            ssml_path = project.root_path / "ssml"
            self.update_file_list(ssml_path, self.ssml_file_list_widget, file_type="ssml", label="SSML")
            self.update_log("SSMLファイルリストを更新しました。\n")

    def update_audio_list(self):
        """音声ファイルリストを更新するスロット"""
        if project and project.root_path:
            audio_path = project.root_path / "audio"
            self.update_file_list(audio_path, self.audio_file_list_widget, file_type="audio", label="音声")
            self.update_log("音声ファイルリストを更新しました。\n")

    def update_log(self, text):
        self.log_box.moveCursor(QTextCursor.MoveOperation.End)
        self.log_box.insertPlainText(text)
    
    def stop_processing(self):
        if self.worker and self.thread and self.thread.isRunning():
            self.worker.stop()
            self.update_log("\n中断命令を送信しました。現在の処理が終わり次第停止します。\n")
            self.stop_audio_creation_btn.setEnabled(False)

    def set_controls_enabled(self, enabled):
        self.start_audio_creation_btn.setEnabled(enabled)
        self.stop_audio_creation_btn.setEnabled(not enabled)
        actions = self.menuBar().findChildren(QAction)
        if actions:
            actions[0].setEnabled(enabled)

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            self.stop_processing()
            self.thread.quit()
            self.thread.wait(2000)
        event.accept()

