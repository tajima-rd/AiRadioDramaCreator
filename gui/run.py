import sys
from PyQt6.QtWidgets import QApplication
from .main_window import AppGUI

def run_gui():
    """GUIモードでアプリケーションを起動する"""
    print("GUIモードで起動します...")
    app = QApplication(sys.argv)
    gui = AppGUI()
    gui.show()
    sys.exit(app.exec())