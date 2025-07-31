

import re
from typing import Dict, List

# 循環参照を避けるため、型チェック時のみインポート
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.api_client import GeminiApiClient

from core.generators import TextGenerator
from core.configs import WriteConfig

def get_ordered_speakers(text: str, speakers_dict: Dict[str, str]) -> Dict[str, str]:
    """
    テキストを解析し、登場する話者を登場順に抽出し、
    話者名と声の設定を格納した新しい辞書を返します。
    SSML形式 (<voice name="...">) と 台本形式 (話者名:) の両方に対応します。
    """
    found_speakers_dict = {}
    seen = set()

    # ★変更ここから★
    # テキストがSSML形式かどうかを判定 (単純なチェック)
    is_ssml = text.strip().startswith("<speak>") and '<voice' in text

    if is_ssml:
        # SSML形式の場合: <voice> タグから 'name' 属性 (ボイス名) を抽出
        ssml_pattern = re.compile(r'<voice\s+name="([^"]+)">')
        matches = ssml_pattern.finditer(text)
        
        # ボイス名から話者名を探すための逆引き辞書を作成
        voice_to_speaker_map = {v: k for k, v in speakers_dict.items()}
        
        for match in matches:
            voice_name = match.group(1).strip() # 抽出されたボイス名 (例: "Charon")
            
            # ボイス名に対応する話者名を取得
            if voice_name in voice_to_speaker_map:
                speaker_name = voice_to_speaker_map[voice_name]
                
                # まだ登場していない話者であれば辞書に追加
                if speaker_name not in seen:
                    seen.add(speaker_name)
                    found_speakers_dict[speaker_name] = speakers_dict[speaker_name]
            else:
                print(f"警告: SSML内のボイス名 '{voice_name}' に対応する話者が見つかりません。")

    else:
        # 台本形式の場合: "話者名:" 形式を抽出
        script_pattern = re.compile(r'^\s*([^:]+):', re.MULTILINE)
        matches = script_pattern.finditer(text)
        
        for match in matches:
            speaker_name = match.group(1).strip() # 抽出された話者名 (例: "喜一")
            
            # まだ登場していない、かつ、元の辞書に存在する話者であれば処理
            if speaker_name not in seen and speaker_name in speakers_dict:
                seen.add(speaker_name)
                found_speakers_dict[speaker_name] = speakers_dict[speaker_name]
    # ★変更ここまで★

    print(f"Speakers found in order: {found_speakers_dict}")
    return found_speakers_dict

def add_ai_interjections(dialog_text: str, speakers_dict: Dict[str, str], text_model_client: 'GeminiApiClient') -> str:
    def get_text_generator(previous_speech: str) -> TextGenerator:
        prompt = f"""
                    あなたは会話の聞き手です。以下のセリフに対して、自然で短い相槌を一つだけ生成してください。
                    相槌は20文字以内で、肯定・同意・感心・簡単な質問のいずれかとします。
                    性別に依存せず、カジュアルで、自然な日本語の相槌を生成してください。
                    相槌のセリフそのものだけを出力し、話者名や引用符は含めないでください。

                    セリフ: 「{previous_speech}」
                    相槌:
                    """
        
        return TextGenerator(
            api_conn=text_model_client,
            write_config=WriteConfig(),
            prompt=prompt,
            parent=None,  # 親ディレクトリは不要
            basename=None  # ベース名は不要
        )

    lines = dialog_text.strip().split('\n')
    new_lines = []
    previous_speaker = None
    previous_speech = ""
    pattern = re.compile(r'^\s*([^:]+):\s*(.*)$')
    all_speakers = list(speakers_dict.keys())

    for line in lines:
        match = pattern.match(line)
        if match:
            current_speaker = match.group(1).strip()
            current_speech = match.group(2).strip()
            
            if previous_speaker and current_speaker == previous_speaker:
                print("  - Same speaker detected, interjection.")

                other_speakers = [s for s in all_speakers if s != current_speaker]
                if other_speakers:
                    interjecting_speaker = other_speakers[0]
                    
                    print(f"  - Generating interjection for '{previous_speech[:20]}...'")
                    response = get_text_generator(previous_speech).generate() 
                    
                    # response は既に文字列なので、.text は不要
                    generated_interjection = response.strip().replace('"', '').replace('「', '').replace('」', '')
                    
                    if 0 < len(generated_interjection) <= 40:
                            new_lines.append(f"{interjecting_speaker}: {generated_interjection}\n")
                    else:
                        print("  - AI response was unsuitable, using random interjection.")

            new_lines.append(line)
            previous_speaker = current_speaker
            previous_speech = current_speech
        else:
            # 「話者: 台詞」形式に一致しない行（空行など）も出力結果に含める
            new_lines.append(line)
            # ただし、その行が完全に空白でない場合（コメント行など）にのみ、
            # 会話の連続性を断ち切るために話者情報をリセットする。
            if line.strip(): # line.strip() は、行が空白のみだと False になる
                previous_speaker = None
                previous_speech = ""

    return "\n".join(new_lines)