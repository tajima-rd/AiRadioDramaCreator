# api_client.py

import sys # エラー警告出力のためにsysをインポート
from google import genai
from typing import List

class ApiKeyManager:
    def __init__(self, keys: List[str], default_index: int = 0):
        # 変数名を 'api_key_list' に統一
        self.api_key_list = [key for key in keys if key and not key.isspace()]

        if not self.api_key_list: # 変数名を修正
            raise ValueError("有効なAPIキーが一つも提供されていません。")
        
        # default_index がリストの範囲内にあるかを確認
        if not (0 <= default_index < len(self.api_key_list)): # 変数名を修正
            # Warning: Default index is invalid. Starting from key #1. のメッセージを維持しつつ、sys.stderrを使用
            print(f"Warning: Default index {default_index} is invalid or out of range. Starting from key #1.", file=sys.stderr)
            default_index = 0 # 無効な場合は0にフォールバック
        
        # ユーザーの指示に基づき、'default_api_key' 属性を追加
        self.default_api_key = self.api_key_list[default_index] # 変数名を修正
        
        # get_next_key メソッドの既存の振る舞いを維持するため、current_index も引き続き保持
        self.current_index = default_index 
        
        print(f"Default API key set to #{default_index}.")
        
    def get_next_key(self) -> str:
        # 変数名を 'api_key_list' に修正
        key = self.api_key_list[self.current_index]
        print(f"--- Using API Key #{self.current_index + 1} ---")
        # 変数名を 'api_key_list' に修正
        self.current_index = (self.current_index) % len(self.api_key_list)
        return key

class GeminiApiClient:
    def __init__(self, api_key, model_name):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)