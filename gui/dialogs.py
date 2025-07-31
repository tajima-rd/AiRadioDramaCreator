from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, # QMessageBox を追加（エラー表示用）
    QListWidget, QListWidgetItem, QInputDialog, QLabel, QComboBox # QListWidget, QListWidgetItem, QInputDialog を追加
)
from PyQt6.QtCore import Qt # QHeaderView.ResizeMode.Stretch のために必要
from PyQt6.QtGui import QFont # フォント変更のためにインポート
from typing import List, Dict, Optional # 型ヒントのためにインポート

AVAILABLE_VOICES = [
    "Achernar -- Soft(F)", 
    "Achird -- Friendly(M)", 
    "Algenib -- Gravelly(M)", 
    "Algieba -- Smooth(M)", 
    "Alnilam -- Firm(M)",
    "Aoede -- Breezy(F)", 
    "Autonoe -- Bright(F)", 
    "Callirrhoe -- Easy-going(F)",
    "Charon -- Informative(M)",
    "Despina -- Smooth(F)",
    "Enceladus -- Breathy(M)", 
    "Erinome -- Clear(F)",
    "Fenrir -- Excitable(M)", 
    "Gacrux -- Mature(F)", 
    "Iapetus -- Clear(M)",
    "Kore -- Firm(F)", 
    "Laomedeia -- Upbeat(F)", 
    "Leda -- Youthful(F)",
    "Orus -- Firm(M)", 
    "Puck -- Upbeat(M)", 
    "Pulcherrima -- Forward(M)",
    "Rasalgethi -- Informative(M)",
    "Sadachbia -- Lively(M)", 
    "Sadaltager -- Knowledgeable(M)", 
    "Schedar -- Even(M)", 
    "Sulafat -- Warm(F)",
    "Umbriel -- Easy-going(M)", 
    "Vindemiatrix -- Gentle(F)",
    "Zephyr -- Bright(F)",
    "Zubenelgenubi -- Casual(M)"
]

class SettingsDialog(QDialog):
    """APIキーとモデル名を設定するためのダイアログ"""
    # ★変更: __init__ に default_index を追加
    def __init__(self, api_keys_list: List[str], default_index: int, speech_model: str, text_model: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("APIキーとモデルの設定")
        self.setMinimumSize(450, 300)
        
        # ★変更: default_index をインスタンス変数として保持
        self.default_index = default_index

        # Widgets
        self.api_key_list_widget = QListWidget()
        self.populate_api_keys(api_keys_list) # APIキーの表示をメソッドに分離

        self.add_key_btn = QPushButton("APIキーを追加")
        self.remove_key_btn = QPushButton("選択したAPIキーを削除")
        # ★追加: デフォルトキー設定ボタン
        self.set_default_btn = QPushButton("デフォルトとして設定")

        self.speech_model_input = QLineEdit(speech_model)
        self.text_model_input = QLineEdit(text_model)
        
        # Layout
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        api_key_layout = QVBoxLayout()
        api_key_layout.addWidget(QLabel("APIキー:"))
        api_key_layout.addWidget(self.api_key_list_widget)
        
        api_key_btn_layout = QHBoxLayout()
        api_key_btn_layout.addWidget(self.add_key_btn)
        api_key_btn_layout.addWidget(self.remove_key_btn)
        # ★追加: デフォルトキー設定ボタンをレイアウトに追加
        api_key_btn_layout.addWidget(self.set_default_btn)
        api_key_layout.addLayout(api_key_btn_layout)
        
        main_layout.addLayout(api_key_layout)

        form_layout.addRow("音声モデル名:", self.speech_model_input)
        form_layout.addRow("テキストモデル名:", self.text_model_input)
        main_layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        # Connections
        self.add_key_btn.clicked.connect(self.add_key)
        self.remove_key_btn.clicked.connect(self.remove_key)
        # ★追加: デフォルトキー設定ボタンの接続
        self.set_default_btn.clicked.connect(self.set_default_key)
        
    def populate_api_keys(self, api_keys_list: List[str]):
        """APIキーリストウィジェットを初期化し、デフォルトキーを太字で表示する"""
        self.api_key_list_widget.clear()
        for i, key in enumerate(api_keys_list):
            item = QListWidgetItem(key)
            # JSONの default_api_key_index は1始まり、リストのインデックスは0始まり
            # ここでは0始まりの default_index を受け取っていると仮定
            if i == self.default_index:
                font = QFont()
                font.setBold(True)
                item.setFont(font)
                item.setText(f"{key} (デフォルト)")
            self.api_key_list_widget.addItem(item)
    
    # ★追加: デフォルトキーを設定するメソッド
    def set_default_key(self):
        current_row = self.api_key_list_widget.currentRow()
        if current_row >= 0:
            self.default_index = current_row
            # APIキーリストの表示を更新して、新しいデフォルトを反映
            keys = [self.api_key_list_widget.item(i).text().split(' ')[0] for i in range(self.api_key_list_widget.count())]
            self.populate_api_keys(keys)
            # 新しいデフォルトキーを選択状態にする
            self.api_key_list_widget.setCurrentRow(self.default_index)

    def get_settings(self):
        """ダイアログで入力された設定値をタプルとして返す"""
        api_keys = [self.api_key_list_widget.item(i).text().split(' ')[0] # "(デフォルト)" を除去
                    for i in range(self.api_key_list_widget.count())
                    if self.api_key_list_widget.item(i).text().strip()]
        
        # ★変更: default_api_key_index を返すように変更 (1始まりのインデックス)
        return (
            api_keys,
            self.default_index,
            self.speech_model_input.text(),
            self.text_model_input.text()
        )

    def add_key(self):
        """APIキーをリストウィジェットに追加するダイアログを表示"""
        key, ok = QInputDialog.getText(self, "APIキーの追加", "新しいAPIキーを入力してください:")
        if ok and key.strip():
            self.api_key_list_widget.addItem(key.strip())
            self.api_key_list_widget.scrollToBottom()

    def remove_key(self):
        """選択したAPIキーをリストウィジェットから削除"""
        current_row = self.api_key_list_widget.currentRow()
        if current_row >= 0:
            # 削除されるキーがデフォルトキーだった場合、デフォルトを最初のキーに戻す
            if current_row == self.default_index:
                self.default_index = 0
            # 削除されるキーよりインデックスが小さいデフォルトキーはそのまま
            elif current_row < self.default_index:
                self.default_index -= 1
                
            self.api_key_list_widget.takeItem(current_row)
            
            # リストが空になった場合、default_indexをリセット
            if self.api_key_list_widget.count() == 0:
                self.default_index = 0
            
            # リストの表示を更新
            keys = [self.api_key_list_widget.item(i).text().split(' ')[0] for i in range(self.api_key_list_widget.count())]
            self.populate_api_keys(keys)

class SpeakerDialog(QDialog):
    """話者設定を行うためのダイアログ"""
    def __init__(self, speakers_dict: Dict[str, str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("話者の設定")
        self.setMinimumSize(450, 300)

        # Widgets
        self.speaker_table = QTableWidget()
        self.speaker_table.setColumnCount(2)
        self.speaker_table.setHorizontalHeaderLabels(["話者名", "ボイス名"])
        self.speaker_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.speaker_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.populate_table(speakers_dict)

        self.add_btn = QPushButton("話者を追加")
        self.remove_btn = QPushButton("選択した話者を削除")
        
        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.speaker_table)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        layout.addLayout(btn_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept_and_validate)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connections
        self.add_btn.clicked.connect(self.add_row)
        self.remove_btn.clicked.connect(self.remove_row)

    def populate_table(self, speakers_dict):
        """渡された辞書でテーブルを初期化する"""
        self.speaker_table.setRowCount(len(speakers_dict))
        for i, (name, voice) in enumerate(speakers_dict.items()):
            self.speaker_table.setItem(i, 0, QTableWidgetItem(name))
            
            voice_combo = QComboBox()
            voice_combo.addItems(AVAILABLE_VOICES) # 完全な表示名を追加

            # ★変更ここから★
            # JSONから来る 'voice' (例: "Charon") に対応する表示名 ("Charon -- Informative") を探して設定する
            found_display_name = ""
            for display_name in AVAILABLE_VOICES:
                if display_name.startswith(voice + " --"):
                    found_display_name = display_name
                    break
            
            if found_display_name:
                voice_combo.setCurrentText(found_display_name)
            else:
                # もしJSONから来たボイス名が AVAILABLE_VOICES に見つからない場合（例えば古い設定やカスタムボイス）
                # そのボイス名をコンボボックスの最初の項目として追加し、選択状態にする
                if voice:
                    voice_combo.insertItem(0, voice)
                    voice_combo.setCurrentIndex(0)
            # ★変更ここまで★
            
            self.speaker_table.setCellWidget(i, 1, voice_combo)

    def add_row(self):
        """テーブルに空の行を追加する"""
        row_count = self.speaker_table.rowCount()
        self.speaker_table.insertRow(row_count)
        
        self.speaker_table.setItem(row_count, 0, QTableWidgetItem("")) # 空のアイテムで初期化
        
        voice_combo = QComboBox()
        voice_combo.addItems(AVAILABLE_VOICES)
        # デフォルトで最初の項目を選択状態にする
        if AVAILABLE_VOICES:
            voice_combo.setCurrentIndex(0)
        self.speaker_table.setCellWidget(row_count, 1, voice_combo)

        self.speaker_table.setCurrentCell(row_count, 0)
        self.speaker_table.edit(self.speaker_table.currentIndex())

    def remove_row(self):
        """テーブルで選択されている行を削除する"""
        current_row = self.speaker_table.currentRow()
        if current_row >= 0:
            self.speaker_table.removeRow(current_row)

    def get_speakers(self):
        """現在のテーブルの内容を辞書として返す"""
        speakers = {}
        for row in range(self.speaker_table.rowCount()):
            name_item = self.speaker_table.item(row, 0)
            voice_combo_widget = self.speaker_table.cellWidget(row, 1)

            if name_item and name_item.text().strip() and voice_combo_widget:
                speaker_name = name_item.text().strip()
                selected_display_name = voice_combo_widget.currentText().strip() # コンボボックスの現在選択されている完全な表示名

                # ★変更ここから★
                # ' -- ' で分割し、ボイス名（最初の部分）のみを取得
                voice_name = selected_display_name.split(' -- ')[0]
                # ★変更ここまで★

                if speaker_name and voice_name:
                    speakers[speaker_name] = voice_name
        return speakers
    
    def accept_and_validate(self):
        """OKボタンが押されたときにバリデーションを行い、問題がなければダイアログを閉じる"""
        speakers = self.get_speakers()
        if not speakers:
            reply = QMessageBox.question(self, "話者設定の確認",
                                         "話者が一人も設定されていません。続行しますか？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
        super().accept()