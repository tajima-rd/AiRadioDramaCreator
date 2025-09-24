def convert_speaker_dict_to_character(data: Any) -> List[Character]:
    """
    話者・キャラクターデータを正規化し、必ず新しい形式(List[Character])で返す。

    この関数は、古い形式(Dict[str, str])と新しい形式(List[Character])の
    両方のデータ入力を受け付け、互換性を維持します。

    Args:
        data: 設定ファイルなどから読み込んだキャラクターデータ。
              以下のいずれかの形式を想定:
              - 新: List[Character]
              - 旧: Dict[str, str] (例: {'名前': 'ボイス名'})
              - それ以外 (None, 空の辞書/リストなど)

    Returns:
        必ず List[Character] 形式に変換されたデータ。
        変換不可能な場合や入力が空の場合は、空のリストを返す。
    """
    # 1. データが既に新しい形式 (List[Character]) の場合
    if isinstance(data, list):
        # リストが空であるか、最初の要素がCharacterインスタンスなら、新しい形式と判断
        if not data or isinstance(data[0], Character):
            return data

    # 2. データが古い形式 (Dict[str, str]) の場合
    if isinstance(data, dict):
        new_character_list: List[Character] = []
        default_voice = list(Voice)[0] # 不明なボイス名の場合のフォールバック

        for name, voice_name in data.items():
            try:
                # 文字列のボイス名から、対応するVoice Enumメンバーを取得
                # .upper()で大文字に統一し、堅牢性を高める
                voice_enum = Voice[voice_name.upper()]
            except (KeyError, AttributeError):
                # 設定ファイル上のボイス名がEnumに存在しない場合
                print(f"警告: ボイス名 '{voice_name}' が見つかりません。デフォルトのボイスを割り当てます。")
                voice_enum = default_voice

            # 新しいCharacterオブジェクトを生成。
            # 古い形式には存在しない属性は、空のデフォルト値で初期化。
            character = Character(
                name=name,
                voice=voice_enum,
                personality="",
                traits=[],
                speech_style="",
                verbal_tics=[]
                # background と role はデフォルトで None になる
            )
            new_character_list.append(character)
        
        return new_character_list

    # 3. 予期しない形式やNoneの場合は、空のリストを返す
    return []