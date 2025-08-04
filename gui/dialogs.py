from PyQt6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QMessageBox,
    QLabel, QComboBox, QInputDialog, QTextEdit, QListWidgetItem
)

from PyQt6.QtCore import Qt # QHeaderView.ResizeMode.Stretch のために必要
from PyQt6.QtGui import QFont # フォント変更のためにインポート
from typing import List, Dict, Optional # 型ヒントのためにインポート
from core.configs import Voice, Character

class CharacterEditDialog(QDialog):
    """
    一人のキャラクターの情報を編集するためのダイアログ。
    新規作成と既存キャラクターの編集の両方に対応します。
    """
    def __init__(self, character: Optional[Character] = None, parent=None):
        super().__init__(parent)
        self.character = character  # 編集対象のキャラクターオブジェクト

        # ダイアログのタイトルをモード（新規 or 編集）によって変更
        title = "キャラクターの編集" if self.character else "キャラクターの新規作成"
        self.setWindowTitle(title)
        self.setMinimumSize(500, 600)

        # --- UIウィジェットの初期化 ---
        self.name_input = QLineEdit()
        self.voice_combo = QComboBox()
        self.personality_input = QLineEdit()
        self.speech_style_input = QLineEdit()
        self.role_input = QLineEdit()
        self.background_input = QTextEdit()
        self.background_input.setAcceptRichText(False) # プレーンテキストのみを許容

        # 特性(traits)用のリストとボタン
        self.traits_list = QListWidget()
        self.add_trait_btn = QPushButton("追加")
        self.remove_trait_btn = QPushButton("削除")

        # 口癖(verbal_tics)用のリストとボタン
        self.tics_list = QListWidget()
        self.add_tic_btn = QPushButton("追加")
        self.remove_tic_btn = QPushButton("削除")
        
        # --- レイアウトの設定 ---
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows) # ラベルを長くしても改行されるように

        form_layout.addRow("名前*:", self.name_input)
        form_layout.addRow("ボイス:", self.voice_combo)
        form_layout.addRow("性格:", self.personality_input)
        form_layout.addRow("話し方のスタイル:", self.speech_style_input)
        form_layout.addRow("役割:", self.role_input)
        form_layout.addRow("背景設定:", self.background_input)
        
        # 特性(traits)のレイアウト
        traits_layout = self.create_list_edit_layout(
            self.traits_list, self.add_trait_btn, self.remove_trait_btn)
        form_layout.addRow("特性:", traits_layout)
        
        # 口癖(verbal_tics)のレイアウト
        tics_layout = self.create_list_edit_layout(
            self.tics_list, self.add_tic_btn, self.remove_tic_btn)
        form_layout.addRow("口癖:", tics_layout)

        main_layout.addLayout(form_layout)
        
        # OK/Cancelボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(button_box)

        # --- 初期値の設定と接続 ---
        self.setup_voice_combo()
        if self.character:
            self.populate_data()

        # 接続
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.add_trait_btn.clicked.connect(self.add_trait)
        self.remove_trait_btn.clicked.connect(self.remove_trait)
        self.add_tic_btn.clicked.connect(self.add_tic)
        self.remove_tic_btn.clicked.connect(self.remove_tic)
        
    def create_list_edit_layout(self, list_widget: QListWidget, add_btn: QPushButton, remove_btn: QPushButton) -> QVBoxLayout:
        """QListWidgetとAdd/Removeボタンからなる共通レイアウトを作成するヘルパーメソッド"""
        layout = QVBoxLayout()
        layout.addWidget(list_widget)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)
        return layout

    def setup_voice_combo(self):
        """Voice列挙型からQComboBoxをセットアップする"""
        for voice in Voice:
            display_text = f"{voice.api_name} -- {voice.description} ({voice.gender})"
            self.voice_combo.addItem(display_text, userData=voice)

    def populate_data(self):
        """既存のキャラクター情報でUIを埋める"""
        self.name_input.setText(self.character.name)
        
        # voice_combo で該当するボイスを選択
        index = self.voice_combo.findData(self.character.voice)
        if index >= 0:
            self.voice_combo.setCurrentIndex(index)
            
        self.personality_input.setText(self.character.personality)
        self.speech_style_input.setText(self.character.speech_style)
        self.role_input.setText(self.character.role or "")
        self.background_input.setText(self.character.background or "")
        
        self.traits_list.addItems(self.character.traits)
        self.tics_list.addItems(self.character.verbal_tics)

    # --- リスト編集用スロット ---
    def add_item_to_list(self, list_widget: QListWidget, title: str):
        """QInputDialogを使ってリストに項目を追加する共通メソッド"""
        text, ok = QInputDialog.getText(self, title, "追加する項目:")
        if ok and text.strip():
            list_widget.addItem(text.strip())
            
    def remove_item_from_list(self, list_widget: QListWidget):
        """リストから選択中の項目を削除する共通メソッド"""
        current_row = list_widget.currentRow()
        if current_row >= 0:
            list_widget.takeItem(current_row)

    def add_trait(self):
        self.add_item_to_list(self.traits_list, "特性の追加")

    def remove_trait(self):
        self.remove_item_from_list(self.traits_list)

    def add_tic(self):
        self.add_item_to_list(self.tics_list, "口癖の追加")

    def remove_tic(self):
        self.remove_item_from_list(self.tics_list)
        
    # --- ダイアログの結果を取得 ---
    def get_character(self) -> Character:
        """UIの現在の入力値からCharacterオブジェクトを生成して返す"""
        traits = [self.traits_list.item(i).text() for i in range(self.traits_list.count())]
        tics = [self.tics_list.item(i).text() for i in range(self.tics_list.count())]
        
        return Character(
            name=self.name_input.text().strip(),
            voice=self.voice_combo.currentData(),
            personality=self.personality_input.text().strip(),
            speech_style=self.speech_style_input.text().strip(),
            role=self.role_input.text().strip() or None,
            background=self.background_input.toPlainText().strip() or None,
            traits=traits,
            verbal_tics=tics
        )
        
    def accept(self):
        """OKボタンが押されたときのバリデーション"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "入力エラー", "キャラクターの名前は必須です。")
            return
        super().accept()

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
    """
    キャラクターの一覧を管理し、編集するためのダイアログ。
    """
    def __init__(self, characters: List[Character], parent=None):
        super().__init__(parent)
        self.setWindowTitle("キャラクター設定")
        self.setMinimumSize(400, 500)

        # 編集対象のキャラクターリストをインスタンス変数として保持
        # 元のリストを直接変更しないように、コピーを作成する
        self.characters = list(characters)

        # --- UIウィジェットの初期化 ---
        self.list_widget = QListWidget()
        self.list_widget.setToolTip("編集したいキャラクターをダブルクリックするか、選択して「編集」ボタンを押してください。")

        self.add_btn = QPushButton("キャラクターを追加...")
        self.edit_btn = QPushButton("選択したキャラクターを編集...")
        self.remove_btn = QPushButton("選択したキャラクターを削除")

        # --- レイアウトの設定 ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.remove_btn)
        main_layout.addLayout(btn_layout)

        # OK/Cancelボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(button_box)

        # --- 初期値の設定と接続 ---
        self.populate_list()

        # 接続
        self.add_btn.clicked.connect(self.add_character)
        self.edit_btn.clicked.connect(self.edit_character)
        self.remove_btn.clicked.connect(self.remove_character)
        
        # ダブルクリックでも編集できるようにする
        self.list_widget.itemDoubleClicked.connect(self.edit_character)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
    def populate_list(self):
        """インスタンスが持つキャラクターリストでUIを更新する"""
        self.list_widget.clear()
        for char in self.characters:
            # リストにはキャラクターの名前を表示
            self.list_widget.addItem(char.name)
            
    def add_character(self):
        """「追加」ボタンの処理。CharacterEditDialogを新規モードで開く"""
        dialog = CharacterEditDialog(parent=self)
        if dialog.exec():
            # OKが押されたら、新しいキャラクターを取得してリストに追加
            new_character = dialog.get_character()
            self.characters.append(new_character)
            self.populate_list() # UIを更新
            # 追加した項目を選択状態にする
            self.list_widget.setCurrentRow(len(self.characters) - 1)
            
    def edit_character(self):
        """「編集」ボタンの処理。CharacterEditDialogを編集モードで開く"""
        current_row = self.list_widget.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "情報", "編集したいキャラクターをリストから選択してください。")
            return
            
        character_to_edit = self.characters[current_row]
        
        dialog = CharacterEditDialog(character=character_to_edit, parent=self)
        if dialog.exec():
            # OKが押されたら、更新されたキャラクターでリストを置き換え
            updated_character = dialog.get_character()
            self.characters[current_row] = updated_character
            self.populate_list() # UIを更新
            # 編集した項目を選択状態に戻す
            self.list_widget.setCurrentRow(current_row)

    def remove_character(self):
        """「削除」ボタンの処理"""
        current_row = self.list_widget.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "情報", "削除したいキャラクターをリストから選択してください。")
            return
            
        character_to_remove = self.characters[current_row]
        reply = QMessageBox.question(
            self,
            "削除の確認",
            f"本当にキャラクター「{character_to_remove.name}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.characters[current_row]
            self.populate_list() # UIを更新
            
    def get_characters(self) -> List[Character]:
        """ダイアログの結果として、最終的なキャラクターリストを返す"""
        return self.characters
