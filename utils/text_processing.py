import re, os, sys
from typing import Dict, List

# 循環参照を避けるため、型チェック時のみインポート
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.api_client import GeminiApiClient

from core.generators import TextGenerator
from core.models import WriteConfig, Character

import re
from typing import List, Dict

def get_ordered_characters(text: str, all_characters: List[Character]) -> List[Character]:
    """
    テキストを解析し、登場するキャラクターを登場順に抽出し、
    Characterオブジェクトのリストとして返します。
    SSML形式 (<voice name="...">) と 台本形式 (話者名:) の両方に対応します。

    Args:
        text (str): 解析対象のテキスト（台本やSSML）。
        all_characters (List[Character]): プロジェクトに登録されている全キャラクターのリスト。

    Returns:
        List[Character]: テキストに登場した順に並べられたCharacterオブジェクトのリスト。
    """
    # 効率的な検索のために、名前とボイス名からCharacterオブジェクトを引ける辞書を作成
    name_to_char_map = {char.name: char for char in all_characters}
    voice_to_char_map = {char.voice.api_name: char for char in all_characters}

    found_characters: List[Character] = []
    seen_names = set()

    # テキストがSSML形式かどうかを判定
    is_ssml = text.strip().startswith("<speak>") and '<voice' in text

    if is_ssml:
        # SSML形式の場合: <voice> タグから 'name' 属性 (ボイス名) を抽出
        ssml_pattern = re.compile(r'<voice\s+name="([^"]+)">')
        matches = ssml_pattern.finditer(text)
        
        for match in matches:
            voice_name = match.group(1).strip()
            
            # ボイス名に対応するキャラクターを取得
            character = voice_to_char_map.get(voice_name)
            
            if character:
                # まだ登場していないキャラクターであればリストに追加
                if character.name not in seen_names:
                    seen_names.add(character.name)
                    found_characters.append(character)
            else:
                print(f"警告: SSML内のボイス名 '{voice_name}' に対応するキャラクターが見つかりません。")

    else:
        # 台本形式の場合: "話者名:" 形式を抽出
        script_pattern = re.compile(r'^\s*([^:]+):', re.MULTILINE)
        matches = script_pattern.finditer(text)
        
        for match in matches:
            speaker_name = match.group(1).strip()
            
            # 話者名に対応するキャラクターを取得
            character = name_to_char_map.get(speaker_name)

            if character:
                # まだ登場していないキャラクターであればリストに追加
                if character.name not in seen_names:
                    seen_names.add(character.name)
                    found_characters.append(character)

    # ログ出力用にキャラクター名のリストを作成
    found_names = [char.name for char in found_characters]
    print(f"テキストから検出されたキャラクター（登場順）: {found_names}")
    
    return found_characters

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
    def get_text_generator(script: str, characters: List[Character], client: 'GeminiApiClient') -> TextGenerator:
        """
        キャラクター情報とシナリオから、セリフ生成用のTextGeneratorを生成します。
        (リファクタリング後)
        """
        # 各キャラクターオブジェクトにプロンプトの生成を依頼し、結果を結合する
        character_profiles_list = [char.get_character_prompt() for char in characters]
        character_profiles = "".join(character_profiles_list)

        # --- AIへの指示プロンプトを作成 ---
        prompt = f"""
            あなたは、プロの脚本家です。渡されたシナリオと詳細な登場人物紹介に基づき、生き生きとした自然な会話台本を生成してください。

            ### 絶対的なルール（最重要・厳守）
            1.  **登場人物の名前は、以下に示すフルネームを【一字一句、完全なまま】使用してください。** 勝手に短縮したり、変更したりすることは絶対に許可しません。（例: 「Character A」は常に「Character A」と表記し、「A」などにしてはいけません）
            2.  **出力形式の厳守:** 必ず「名前: セリフ」の形式で出力してください。（例: `Character A: こんにちは。`）
            3.  **セリフ以外の要素は含めない:** ト書き、情景描写、効果音（「笑」など）は一切含めないでください。
            4.  **空行のルール:** 各セリフの間には、必ず空行を1行だけ入れてください。
            5.  **登場順のルール:** 登場人物のセリフは必ず交互になるようにしてください。同じ人物が連続することは絶対に許可しません。

            ---

            ### 登場人物紹介
            {character_profiles.strip()}

            ---

            ### シナリオの要約
            {script}

            ---

            ### 生成する台本
            """
        
        # TextGeneratorインスタンスを生成して返す
        return TextGenerator(
            api_conn=client,
            write_config=WriteConfig(),
            prompt=prompt,
            parent=None,
            basename=None
        )

    # 先に改行をスペースに置換したプレビュー用の文字列を作成する
    log_preview = script_text[:30].replace('\n', ' ')
    print(f"INFO: Generating dialog from script starting with '{log_preview}...'")

    try:
        # TextGeneratorインスタンスを作成し、.generate()を呼び出してAPIにリクエスト
        generator = get_text_generator(script_text, speakers_dict, text_model_client)
        dialog_text = generator.generate()
        return dialog_text
    except Exception as e:
        print(f"ERROR: An error occurred during dialog generation: {e}")
        return "" # エラーが発生した場合は空文字列を返す

def add_ai_interjections(dialog_text: str, characters: List[Character], text_model_client: 'GeminiApiClient') -> str:
    """
    同じ話者が連続する場合、他のキャラクターによる短い相槌をAIに生成させて挿入する。
    Characterオブジェクトのリストを扱うように修正されています。
    """
    
    # --- ヘルパー関数: キャラクターの個性を反映した相槌生成器 ---
    def get_interjection_generator(previous_speech: str, character: Character) -> TextGenerator:
        """指定されたキャラクターになりきって、相槌を生成するためのTextGeneratorを返す。"""
        
        # 相槌を打つキャラクターのプロフィールをプロンプト用に生成
        character_name = character.name
        character_profile = character.get_character_prompt()

        # AIへの指示プロンプト
        prompt = f"""
            あなたは「{character_name}」という人物です。
            以下の「あなたの設定」を忠実に守り、会話の聞き手として応答してください。

            ### あなたの設定
            {character_profile.strip()}
            
            ### 指示
            以下の「相手のセリフ」に対して、あなたの性格や話し方を反映した、自然で短い相槌を一つだけ生成してください。

            ### ルール
            - 相槌は20文字以内にしてください。
            - 肯定、同意、感心、簡単な質問のいずれかの内容にしてください。
            - 相槌のセリフそのものだけを出力し、あなたの名前や他の記号（引用符など）は絶対に含めないでください。

            ### 相手のセリフ
            「{previous_speech}」

            ### あなたの相槌
            """
            
        return TextGenerator(
            api_conn=text_model_client,
            write_config=WriteConfig(),
            prompt=prompt,
            parent=None,
            basename=None
        )

    # --- メインロジック ---
    lines = dialog_text.strip().split('\n')
    new_lines = []
    previous_speaker_name = None
    previous_speech = ""
    pattern = re.compile(r'^\s*([^:]+):\s*(.*)$')

    for line in lines:
        match = pattern.match(line)
        if match:
            current_speaker_name = match.group(1).strip()
            current_speech = match.group(2).strip()
            
            # 前の話者と同じ話者が連続して話した場合
            if previous_speaker_name and current_speaker_name == previous_speaker_name:
                
                # 相槌を打つ、別のキャラクターを探す
                other_characters = [c for c in characters if c.name != current_speaker_name]
                if other_characters:
                    # ここでは単純に最初の「他のキャラクター」を選ぶ
                    # (より高度なロジックも可能: 例 ランダムに選ぶ、直前に話していない人を選ぶなど)
                    interjecting_character = other_characters[0]
                    
                    print(f"  - {interjecting_character.name}が相槌を生成中... (前のセリフ: '{previous_speech[:20]}...')")
                    
                    # 強化されたジェネレーターを呼び出す
                    response = get_interjection_generator(previous_speech, interjecting_character).generate()
                    
                    generated_interjection = response.strip().replace('"', '').replace('「', '').replace('」', '')
                    
                    if 0 < len(generated_interjection) <= 40: # 長すぎる応答は無視
                            new_lines.append(f"{interjecting_character.name}: {generated_interjection}\n")
                    else:
                        print(f"  - AIの応答が不適切でした: '{generated_interjection}'")

            new_lines.append(line)
            previous_speaker_name = current_speaker_name
            previous_speech = current_speech
        else:
            # 「話者: 台詞」形式に一致しない行（空行など）もそのまま保持
            new_lines.append(line)
            if line.strip(): 
                previous_speaker_name = None
                previous_speech = ""

    return "\n".join(new_lines)

