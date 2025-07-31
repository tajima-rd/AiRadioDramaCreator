# AiRadioDramaCreator

## 概要

`AiRadioDramaCreator` は、Google Gemini API を活用してラジオドラマの台本から音声を自動生成するためのデスクトップアプリケーションです。テキストファイルで書かれた台本を読み込み、複数の話者にそれぞれ割り当てられたAIボイスで音声コンテンツを生成します。

本プロジェクトは、以下の主要な機能を提供します：
- プロジェクト設定の読み込みと管理
- 複数のAPIキーの管理と利用
- 複数の話者へのAIボイスの割り当て
- 台本（テキストファイル）からの音声（WAV/MP3）生成
- ファイル処理間の自動待機設定

## 機能

- **プロジェクト管理**: `project.json` ファイルを通じて、プロジェクト名、説明、作成者、API設定、話者設定、ファイルパスなどを一元的に管理します。
- **UIによる設定**: 専用のダイアログを通じて、APIキー、使用モデル、話者とそのボイスを視覚的に設定・変更し、設定ファイルに保存できます。
- **柔軟なパス設定**: プロジェクトのルートパスを設定するだけで、台本、音声出力、その他関連ファイルのディレクトリ構造を自動的に認識・作成します。
- **音声生成**: 選択されたテキストファイル（台本）の内容に基づき、各話者に割り当てられたAIボイスで音声を生成し、指定されたディレクトリに保存します。
- **MP3変換**: 生成されたWAVファイルを自動的にMP3形式に変換します。
- **進捗表示とログ**: 処理の進捗状況、エラー、警告をリアルタイムでログウィンドウに表示します。
- **処理中断機能**: 長時間の処理中でも、必要に応じて中断できます。
- **APIキーの循環利用**: 複数のAPIキーを設定することで、レートリミット対策としてキーを循環して利用できます（将来的にはこの機能が強化される可能性があります）。

## プロジェクト構造

主要なディレクトリとファイルの役割は以下の通りです：

AiRadioDramaCreator/
├── core/ # アプリケーションのコアロジック
│ ├── api_client.py # APIクライアント (ApiKeyManager, GeminiApiClient) の定義
│ ├── configs.py # 設定関連のクラス (Project, SpeechConfig, WriteConfig) の定義
│ ├── generators.py # 音声・テキスト生成のロジック (SpeechGenerator, TextGenerator)
│ ├── orchestrator.py # メインの処理フロー (process_drama_file など)
│ └── init.py
├── gui/ # グラフィカルユーザーインターフェース (GUI) 関連ファイル
│ ├── app_ui_setup.py # UI要素の構築ロジックを分離したファイル
│ ├── dialogs.py # 設定用ダイアログ (SettingsDialog, SpeakerDialog) の定義
│ ├── main_window.py # メインウィンドウのロジックとイベントハンドラ
│ └── run.py # GUIアプリケーションの起動スクリプト
├── utils/ # ユーティリティ関数
│ ├── project_loader.py # project.json の読み込み・保存ロジック
│ ├── ssml_utils.py # SSML変換関連のユーティリティ
│ └── text_processing.py # テキスト処理関連のユーティリティ
│ └── init.py
├── main.py # アプリケーションのエントリーポイント (CLI/GUIモード選択)
├── project.json # プロジェクトの設定ファイル (テンプレートとして使用)
└── requirements.txt # 依存関係ライブラリのリスト (未作成ですが、必要です)

## インストール

### 前提条件

- Python 3.9 以上
- pip (Pythonのパッケージインストーラー)
- **FFmpeg**: MP3形式の音声ファイルを生成するために必要です。お使いのOSに合ったFFmpegをダウンロードし、システムPATHに追加してください。
    - [FFmpeg 公式サイト](https://ffmpeg.org/download.html)

### セットアップ手順

1.  **リポジトリをクローンする**:
    ```bash
    git clone https://github.com/YourUsername/AiRadioDramaCreator.git # あなたのリポジトリURLに置き換えてください
    cd AiRadioDramaCreator
    ```

2.  **Pythonの依存関係をインストールする**:
    `requirements.txt` ファイルに記載されているライブラリをインストールします。
    ```bash
    pip install -r requirements.txt
    ```
    (もし `requirements.txt` がまだない場合は、以下のライブラリを手動でインストールしてください: `PyQt6`, `google-generativeai`, `pydub`)

## 使い方

### 1. プロジェクト設定ファイル (`project.json`) の準備

アプリケーションを起動する前に、`project.json` ファイルを設定してください。

- `project_settings`: プロジェクトの基本情報。
- `file_paths.root_path`: プロジェクトの基準となるルートディレクトリの絶対パスを指定します。このパスの下に `audio`, `dialog` などのサブディレクトリが自動的に作成されます。
- `api_settings.api_keys`: Google Gemini API のAPIキーをリストとして設定します。
- `api_settings.default_api_key_index`: デフォルトで使用するAPIキーのインデックス（1から始まる）。
- `api_settings.speech_model`: 音声生成に使用するGeminiモデル名（例: `gemini-2.5-flash-preview-tts`）。
- `api_settings.text_model`: テキスト処理（相槌生成など）に使用するGeminiモデル名（例: `gemini-2.5-flash`）。
- `speaker_settings.speakers`: `{"話者名": "ボイス名"}` の形式で、話者とそのボイス名をマッピングします。ボイス名はUIで選択可能なプリビルドボイスリストから選べます。
- `processing_settings.wait_seconds`: ファイル処理間の待機時間（秒）。

### 2. アプリケーションの起動

CLIモードまたはGUIモードでアプリケーションを起動できます。

-   **GUIモード (推奨)**:
    ```bash
    python main.py
    ```
    または、もし `main.py` が実行可能ファイルとして設定されていれば
    ```bash
    ./main.py
    ```

-   **CLIモード (テスト用)**:
    ```bash
    python main.py <path/to/your/project.json>
    ```

### 3. GUIアプリケーションの使用 (GUIモード)

1.  **プロジェクトを開く**: アプリケーション起動後、「ファイル」メニューから「プロジェクトファイルを開く...」を選択し、準備した `project.json` ファイルを選択します。
2.  **UIの更新**: プロジェクトが読み込まれると、プロジェクト名、パス、台本ファイルリスト、音声ファイルリストが更新されます。
3.  **設定の変更**: 「設定」メニューから「API/モデル設定...」または「話者設定...」を選択し、ダイアログを通じて設定を変更・保存できます。変更は `project.json` に反映されます。
4.  **音声生成の開始**: 「処理対象のテキストファイル一覧」から、音声生成したい台本ファイル（複数選択可）を選択し、「選択したファイルの音声生成を開始」ボタンをクリックします。
5.  **ログの確認**: 下部のログウィンドウで処理の進捗やエラーを確認できます。
6.  **音声ファイルの確認**: 処理が完了すると、「処理後の音声ファイル一覧」が更新され、生成された音声ファイルが表示されます。

## APIキーの管理とセキュリティに関する注意

-   APIキーは非常に機密性の高い情報です。**絶対にGitリポジトリに直接コミットしないでください。**
-   ベストプラクティスとしては、APIキーを環境変数として設定するか、`.env` ファイルに保存し、プログラムから読み込む方法を採用してください（このプロジェクトではまだ実装されていませんが、将来的な改善点として推奨されます）。
-   現在、`project.json` にAPIキーを直接記述する形式を採用していますが、GitHubに公開する際は、`project.json` を `.gitignore` に追加し、`project.json.template` を作成して公開することをお勧めします。

## 貢献

バグ報告、機能リクエスト、コードの改善など、あらゆる貢献を歓迎します。

## ライセンス

[LICENSE](LICENSE) ファイルを参照してください。 (ここにライセンス情報を記載します。例: MIT License)