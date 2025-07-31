# gui/app_ui_setup.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget, QAbstractItemView, QTextEdit
)
from PyQt6.QtGui import QAction # QAction はメニューバーのアクション作成に必要
from PyQt6.QtCore import Qt # Qt.ItemDataRole.UserRole などに必要

def setup_main_ui(main_window_instance):
    """
    AppGUI の主要なUI要素を構築し、設定する関数。
    main_window_instance は AppGUI クラスのインスタンスを指します。
    この関数はUI要素を main_window_instance の属性として設定します。
    """
    # メニューバーのセットアップ
    menu_bar = main_window_instance.menuBar()
    file_menu = menu_bar.addMenu("プロジェクト")
    
    # QAction はここで作成し、AppGUIインスタンスに直接追加（返り値として渡す）
    new_action = QAction("プロジェクトの新規作成...", main_window_instance)
    file_menu.addAction(new_action)

    open_action = QAction("プロジェクトを開く...", main_window_instance)
    file_menu.addAction(open_action)

    # "インポート" メニュー
    import_menu = menu_bar.addMenu("インポート")

    import_scenario_action = QAction("シナリオのインポート...", main_window_instance)
    import_menu.addAction(import_scenario_action)

    import_md_scenario_action = QAction("シナリオの分割インポート...", main_window_instance)
    import_menu.addAction(import_md_scenario_action)

    # 設定メニュー
    settings_menu = menu_bar.addMenu("設定")
    settings_api_action = QAction("API/モデル設定...", main_window_instance)
    settings_speaker_action = QAction("話者設定...", main_window_instance)
    settings_menu.addAction(settings_api_action)
    settings_menu.addAction(settings_speaker_action)
    
    # メインウィジェットとレイアウトのセットアップ
    main_widget = QWidget()
    main_window_instance.setCentralWidget(main_widget)
    main_layout = QVBoxLayout(main_widget)
    
    # プロジェクト名表示ラベル
    main_window_instance.project_name_label = QLabel("プロジェクトが選択されていません")
    main_window_instance.project_name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
    main_layout.addWidget(main_window_instance.project_name_label)

    # プロジェクトパス表示ラインエディット
    main_window_instance.project_path_label = QLineEdit()
    main_window_instance.project_path_label.setReadOnly(True)
    main_layout.addWidget(main_window_instance.project_path_label)

    # 新しいファイルリストウィジェットとレイアウトの定義
    file_lists_container_layout = QVBoxLayout() # 全体のコンテナを垂直レイアウトに

    # 上段のファイルリスト (シナリオとダイヤログ)
    top_row_file_lists_layout = QHBoxLayout()

    # 左上: 処理対象のシナリオファイル一覧
    scenario_files_layout = QVBoxLayout()
    scenario_files_layout.addWidget(QLabel("処理対象のシナリオファイル一覧:"))
    main_window_instance.scenario_file_list_widget = QListWidget()
    main_window_instance.scenario_file_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    scenario_files_layout.addWidget(main_window_instance.scenario_file_list_widget)

    dialog_action_layout = QHBoxLayout()
    main_window_instance.start_dialog_creation_btn = QPushButton("選択したファイルの台本生成を開始")
    main_window_instance.stop_dialog_creation_btn = QPushButton("処理を中断")
    main_window_instance.start_dialog_creation_btn.setEnabled(False) # 初期状態では無効
    main_window_instance.stop_dialog_creation_btn.setEnabled(False) # 初期状態では無効
    dialog_action_layout.addWidget(main_window_instance.start_dialog_creation_btn)
    dialog_action_layout.addWidget(main_window_instance.stop_dialog_creation_btn)
    scenario_files_layout.addLayout(dialog_action_layout)
    top_row_file_lists_layout.addLayout(scenario_files_layout)

    # 右上: 処理対象のダイヤログファイル一覧 (これがWorkerの主入力となる想定)
    dialog_files_layout = QVBoxLayout()
    dialog_files_layout.addWidget(QLabel("処理対象のダイヤログファイル一覧 (複数選択可):"))
    main_window_instance.dialog_file_list_widget = QListWidget() # 既存のfile_list_widgetをこれに置き換える
    main_window_instance.dialog_file_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    dialog_files_layout.addWidget(main_window_instance.dialog_file_list_widget)

    ssml_action_layout = QHBoxLayout()
    main_window_instance.start_ssml_creation_btn = QPushButton("選択したファイルのSSML生成を開始")
    main_window_instance.stop_ssml_creation_btn = QPushButton("処理を中断")
    main_window_instance.start_ssml_creation_btn.setEnabled(False) # 初期状態では無効
    main_window_instance.stop_ssml_creation_btn.setEnabled(False) # 初期状態では無効
    ssml_action_layout.addWidget(main_window_instance.start_ssml_creation_btn)
    ssml_action_layout.addWidget(main_window_instance.stop_ssml_creation_btn)
    dialog_files_layout.addLayout(ssml_action_layout)
    top_row_file_lists_layout.addLayout(dialog_files_layout)

    file_lists_container_layout.addLayout(top_row_file_lists_layout) # 上段の2つのリストを追加

    # 下段のファイルリスト (SSMLと音声)
    bottom_row_file_lists_layout = QHBoxLayout()

    # 左下: 処理対象のSSMLファイル一覧 (中間生成物または再処理用)
    ssml_files_layout = QVBoxLayout()
    ssml_files_layout.addWidget(QLabel("処理対象のSSMLファイル一覧:"))
    main_window_instance.ssml_file_list_widget = QListWidget()
    main_window_instance.ssml_file_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    ssml_files_layout.addWidget(main_window_instance.ssml_file_list_widget)

    audio_action_layout = QHBoxLayout()
    main_window_instance.start_audio_creation_btn = QPushButton("選択したファイルの音声生成を開始")
    main_window_instance.stop_audio_creation_btn = QPushButton("処理を中断")
    main_window_instance.start_audio_creation_btn.setEnabled(False) # 初期状態では無効
    main_window_instance.stop_audio_creation_btn.setEnabled(False) # 初期状態では無効
    audio_action_layout.addWidget(main_window_instance.start_audio_creation_btn)
    audio_action_layout.addWidget(main_window_instance.stop_audio_creation_btn)
    ssml_files_layout.addLayout(audio_action_layout)
    bottom_row_file_lists_layout.addLayout(ssml_files_layout)

    # 右下: 処理後の音声ファイル一覧 (既存のaudio_file_list_widget)
    audio_files_layout = QVBoxLayout()
    audio_files_layout.addWidget(QLabel("処理後の音声ファイル一覧:"))
    main_window_instance.audio_file_list_widget = QListWidget()
    audio_files_layout.addWidget(main_window_instance.audio_file_list_widget)
    bottom_row_file_lists_layout.addLayout(audio_files_layout)

    project_action_layout = QHBoxLayout()
    main_window_instance.open_project_btn = QPushButton("プロジェクトフォルダを開く")
    project_action_layout.addWidget(main_window_instance.open_project_btn)
    audio_files_layout.addLayout(project_action_layout)

    file_lists_container_layout.addLayout(bottom_row_file_lists_layout) # 下段の2つのリストを追加
    main_layout.addLayout(file_lists_container_layout) # メインレイアウトに横並びレイアウトを追加

    # ログ表示ボックス
    main_window_instance.log_box = QTextEdit()
    main_window_instance.log_box.setReadOnly(True)
    main_layout.addWidget(QLabel("ログ:"))
    main_layout.addWidget(main_window_instance.log_box)

    # 接続が必要な QAction のリストを返す（AppGUI内で接続するため）
    return {
        "new_action": new_action,
        "open_action": open_action,
        "import_scenario_action": import_scenario_action,
        "import_md_scenario_action": import_md_scenario_action, 
        "settings_api_action": settings_api_action,     # ここを追加
        "settings_speaker_action": settings_speaker_action # ここを追加
    }