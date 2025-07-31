# AiRadioDramaCreator/utils/ssml_utils.py

import re
from typing import Dict

def convert_dialog_to_ssml(text: str, speakers_dict: dict) -> str:
    """
    "話者: 台詞" 形式のテキストを、<voice>タグを使ったSSMLに変換する。
    """
    processed_lines = []
    pattern = re.compile(r'^\s*([^:]+):\s*(.*)$')

    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if match:
            speaker = match.group(1).strip()
            speech = match.group(2).strip()
            voice_name = speakers_dict.get(speaker)
            if voice_name:
                # 特殊文字をエスケープ
                speech = speech.replace("&", "&").replace("<", "<").replace(">", ">")
                processed_lines.append(f'\t<p><voice name="{voice_name}">{speech}</voice><break time="0.1s"/></p>\n\n')
            else:
                print(f"警告: 話者 '{speaker}' に対応する声が設定されていません。スキップします。")
        else:
            print(f"警告: 書式が不正な行をスキップしました: '{line}'")
    # 全体を<speak>タグで囲む
    
    return f"<speak>\n{''.join(processed_lines)}\n</speak>"
