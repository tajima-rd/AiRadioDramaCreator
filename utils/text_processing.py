import re, os, sys
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

def split_markdown_to_files(in_file_path: str, output_folder_path: str, indent_num: int):
    """
    Markdownファイルを指定された見出しレベルで分割し、個別のテキストファイルとして保存する。

    Args:
        in_file_path (str): 分割対象のMarkdownファイルのパス。
        output_folder_path (str): 生成したファイルを保存するフォルダのパス。
        indent_num (int): 分割の基準となる見出しのレベル（`#`の数）。
    """
    # --- 引数のバリデーション ---
    if not os.path.exists(in_file_path):
        print(f"エラー: 入力ファイルが見つかりません: '{in_file_path}'")
        sys.exit(1) # エラーでプログラムを終了
    if indent_num < 1:
        print(f"エラー: indent_numは1以上の整数で指定してください。")
        sys.exit(1)

    # --- 1. 入力ファイルの読み込み ---
    try:
        with open(in_file_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        print(f"入力ファイルを読み込みました: '{in_file_path}'")
    except Exception as e:
        print(f"エラー: ファイルの読み込み中に問題が発生しました。 {e}")
        sys.exit(1)

    # --- 2. 保存先フォルダの準備 ---
    os.makedirs(output_folder_path, exist_ok=True)
    print(f"保存先フォルダ: '{output_folder_path}'")

    # --- 3. 動的に分割パターンを生成 ---
    split_pattern = f'\n(?={"#" * indent_num} )'
    heading_marker_to_remove = "#" * indent_num
    sections = re.split(split_pattern, markdown_text)
    
    # 最初の要素が見出しで始まらない場合（導入部など）の調整
    if sections and not sections[0].strip().startswith('#'):
        intro_text = sections.pop(0).strip()
        if intro_text:
            print(f"\n--- 導入部が見つかりました（この部分はファイル分割されません）---\n{intro_text}\n---------------------------------------------------------")

    file_counter = 1
    created_files = []

    # --- 4. 分割されたセクションごとにファイルを生成 ---
    for section in sections:
        section = section.strip()
        if not section:
            continue

        lines = section.split('\n')
        title_line = lines[0].replace(heading_marker_to_remove, '').strip()
        content = '\n'.join(lines[1:]).strip()

        sanitized_title = re.sub(r'[\s\\/:\*\?"<>\|・]', '_', title_line)
        sanitized_title = (sanitized_title[:50] + '..') if len(sanitized_title) > 50 else sanitized_title

        file_name = f"{file_counter:03d}_{sanitized_title}.txt"
        file_path = os.path.join(output_folder_path, file_name)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            created_files.append(file_name)
            file_counter += 1
        except IOError as e:
            print(f"エラー: ファイル '{file_name}' の書き込みに失敗しました。 {e}")

    # --- 5. 処理結果の表示 ---
    print("\n処理が完了しました。")
    if not created_files:
        print("指定された見出しレベルに一致するセクションが見つからなかったため、ファイルは生成されませんでした。")
    else:
        print(f"{len(created_files)}個のファイルが生成されました:")
        for name in sorted(created_files):
            print(f"- {name}")

def create_dialog(script_text: str, speakers_dict: Dict[str, str], text_model_client: 'GeminiApiClient') -> str:
    """
    LLMを使用して、シナリオのテキストから会話形式の台本を生成する。
    """
    def get_text_generator(script: str, speakers: Dict[str, str], client: 'GeminiApiClient') -> TextGenerator:
        # 出力形式のサンプルを作成
        speakers_list = ""
        sample_text = ""
        for character in speakers.keys():
            # 正しい改行コード `\n` を使用
            sample_text += f"{character}: （ここにセリフが入ります）\n\n"
            speakers_list += f"{character}\n"
        
        print(speakers_list)

        prompt = f"""
            あなたは、渡されたシナリオと登場人物リストに基づき、カジュアルな会話台本を生成するアシスタントです。

            ### 絶対的なルール
            - **必ず指定された登場人物名だけを使用してください。** 他の名前（「話者A」など）は絶対に使用してはいけません。
            - **登場人物**: {speakers_list.strip()}
            - 出力は、必ず「名前: セリフ」の形式にしてください。
            - ト書き、情景描写、効果音など、セリフ以外の要素は一切含めないでください。
            - 各セリフの間には、必ず空行を1行入れてください。
            - 同じ話者が連続して話さないようにしてください。

            ### シナリオ
            {script}

            ### 台本
            """
        
        return TextGenerator(
            api_conn=client,
            write_config=WriteConfig(), # 必要に応じてWriteConfigのパラメータを調整
            prompt=prompt,
            parent=None,
            basename=None
        )

    # --- ↓ ここが修正箇所です ↓ ---
    # 先に改行をスペースに置換したプレビュー用の文字列を作成する
    log_preview = script_text[:30].replace('\n', ' ')
    print(f"INFO: Generating dialog from script starting with '{log_preview}...'")
    # --- ↑ ここが修正箇所です ↑ ---

    try:
        # TextGeneratorインスタンスを作成し、.generate()を呼び出してAPIにリクエスト
        generator = get_text_generator(script_text, speakers_dict, text_model_client)
        dialog_text = generator.generate()
        return dialog_text
    except Exception as e:
        print(f"ERROR: An error occurred during dialog generation: {e}")
        return "" # エラーが発生した場合は空文字列を返す

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