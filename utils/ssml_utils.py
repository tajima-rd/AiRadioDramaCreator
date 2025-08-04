# AiRadioDramaCreator/utils/ssml_utils.py

import re
from typing import Dict

# AiRadioDramaCreator/utils/ssml_utils.py

import re
from typing import List
from core.models import Character
 

# from core.character import Character # Characterクラスをインポート

def convert_dialog_to_ssml(text: str, ordered_characters: List[Character]) -> str:
    """
    "話者: 台詞" 形式のテキストを、<voice>タグを使ったSSMLに変換する。
    引数として、テキストに登場する順に並んだCharacterオブジェクトのリストを受け取る。
    """
    # 効率的な検索のため、キャラクター名をキーにした辞書を作成
    # 値はCharacterオブジェクトそのもの
    character_map = {char.name: char for char in ordered_characters}
    
    processed_lines = []
    # "話者:" という行のパターン
    pattern = re.compile(r'^\s*([^:]+):\s*(.*)$')

    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
            
        match = pattern.match(line)
        if match:
            speaker_name = match.group(1).strip()
            speech_text = match.group(2).strip()
            
            # 話者名からCharacterオブジェクトを取得
            character = character_map.get(speaker_name)
            
            if character:
                # Characterオブジェクトからボイス名を取得
                voice_name = character.voice.api_name
                
                # SSMLで特別な意味を持つ文字をエスケープ
                # & -> &, < -> <, > -> >
                speech_text = speech_text.replace("&", "&").replace("<", "<").replace(">", ">")
                
                # <voice>タグを生成
                processed_lines.append(f'\t<p><voice name="{voice_name}">{speech_text}</voice><break time="0.1s"/></p>\n\n')
            else:
                # このケースは、上流の get_ordered_characters でフィルタリングされているため
                # 基本的には発生しないはずだが、念のため警告を残す
                print(f"警告: 話者 '{speaker_name}' に対応するキャラクター情報が見つかりません。スキップします。")
        else:
            # "話者:" 形式でない行は、そのままテキストとして扱うか、無視するかを選択
            # ここでは無視する（警告を出力）
            print(f"警告: 書式が不正な行をスキップしました: '{line}'")
            
    # 全体を<speak>タグで囲んで返す
    return f"<speak>\n{''.join(processed_lines)}</speak>"
