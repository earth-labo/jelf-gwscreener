# 🚀 ClimateWash診断ツール - セットアップガイド

## 📦 完成した内容

Phase 1-3の全機能を実装した完全版アプリケーションです！

### ✅ 実装済み機能

#### コア機能
- ✅ テキスト診断
- ✅ 画像診断（OCR + ビジュアル分析）
- ✅ PDF診断（テキスト + 画像抽出）
- ✅ 動画診断（フレーム抽出 + 音声分析）
- ✅ Webサイト診断（HTML解析 + 画像分析）

#### 設定機能
- ✅ AI選択（Claude Sonnet 4.5 / ChatGPT GPT-4）
- ✅ 指令選択（エンパワメント指令のみ / 両指令）
- ✅ バージョン選択（V1完全版 / V2重要項目 / V3 Climate特化）

#### 出力機能
- ✅ 詳細な画面表示
- ✅ PDFレポート自動生成
- ✅ JSON出力
- ✅ Googleスプレッドシート連携

#### UX強化機能
- ✅ 例文ライブラリ（NG/OK表現集）
- ✅ リアルタイムプレビュー（クイックチェック）
- ✅ 診断履歴ダッシュボード

---

## 🛠️ セットアップ手順

### Step 1: 環境準備

#### 1.1 Pythonのインストール
Python 3.9以上が必要です。

```bash
# バージョン確認
python --version
```

#### 1.2 プロジェクトのセットアップ

```bash
# ディレクトリに移動
cd climatewash-diagnosis

# 仮想環境を作成（推奨）
python -m venv venv

# 仮想環境を有効化
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

#### 1.3 システムパッケージのインストール

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils ffmpeg
```

**macOS:**
```bash
brew install tesseract poppler ffmpeg
```

**Windows:**
- Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Poppler: https://github.com/oschwartz10612/poppler-windows/releases
- FFmpeg: https://ffmpeg.org/download.html

### Step 2: APIキーの取得

#### 2.1 Anthropic API（Claude）

1. https://console.anthropic.com/ にアクセス
2. アカウント作成・ログイン
3. "API Keys" → "Create Key"
4. キーをコピー（後でアプリで使用）

#### 2.2 OpenAI API（ChatGPT）

1. https://platform.openai.com/ にアクセス
2. アカウント作成・ログイン
3. "API Keys" → "Create new secret key"
4. キーをコピー（後でアプリで使用）

**💡 どちらか一方のAPIキーがあればOKです！**

### Step 3: ローカルで実行

```bash
streamlit run app.py
```

ブラウザが自動的に開きます（または http://localhost:8501 にアクセス）

### Step 4: APIキーの入力

アプリが起動したら：
1. サイドバーの「🔑 API Key」セクションにAPIキーを貼り付け
2. 診断を開始！

---

## 🌐 Streamlit Cloudにデプロイ（推奨）

### Step 1: GitHubにプッシュ

```bash
# Gitリポジトリを初期化
git init
git add .
git commit -m "Initial commit: ClimateWash診断ツール"

# GitHubリポジトリを作成して、URLを取得

# リモートを追加してプッシュ
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 2: Streamlit Cloudでデプロイ

1. https://streamlit.io/cloud にアクセス
2. GitHubアカウントでログイン
3. "New app" をクリック
4. リポジトリを選択
5. Branch: `main`
6. Main file path: `app.py`
7. "Deploy!" をクリック

**数分で公開URLが生成されます！**

---

## 📊 Googleスプレッドシート連携（オプション）

診断結果を自動的にスプレッドシートに記録できます。

### Step 1: Google Cloud Projectの作成

1. https://console.cloud.google.com/ にアクセス
2. 新しいプロジェクトを作成
3. 左メニュー → "APIとサービス" → "ライブラリ"
4. 以下を検索して有効化：
   - Google Sheets API
   - Google Drive API

### Step 2: サービスアカウントの作成

1. "APIとサービス" → "認証情報"
2. "認証情報を作成" → "サービスアカウント"
3. 名前を入力（例: climatewash-diagnosis）
4. 作成したサービスアカウントをクリック
5. "キー" タブ → "鍵を追加" → "新しい鍵を作成"
6. JSON形式を選択 → "作成"
7. JSONファイルがダウンロードされます

### Step 3: Streamlit Secretsに設定

#### ローカル実行の場合:

1. `.streamlit/secrets.toml` を作成
2. ダウンロードしたJSONの内容を以下の形式で貼り付け：

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

#### Streamlit Cloudの場合:

1. アプリのダッシュボードで "Settings" → "Secrets"
2. 上記と同じ内容を貼り付け
3. "Save" をクリック

### Step 4: スプレッドシートの準備

1. Googleスプレッドシートを新規作成
2. サービスアカウントのメールアドレス（`xxx@xxx.iam.gserviceaccount.com`）に**編集権限**を付与
3. スプレッドシートのURLから **ID** をコピー
   - URL: `https://docs.google.com/spreadsheets/d/{この部分がID}/edit`
4. アプリのサイドバーの「Google Sheets設定」にIDを貼り付け

---

## 💻 使い方

### 1. テキスト診断

1. "📝 テキスト" タブを選択
2. 診断したいテキストを入力
3. "🔍 診断開始" をクリック
4. 結果を確認

### 2. 画像診断

1. "🖼️ 画像" タブを選択
2. 画像ファイルをドラッグ&ドロップ
3. "🔍 診断開始" をクリック
4. ビジュアル要素とテキストが分析されます

### 3. PDF診断

1. "📄 PDF" タブを選択
2. PDFファイルをアップロード
3. "🔍 診断開始" をクリック
4. 全ページが自動的に分析されます

### 4. 動画診断

1. "🎬 動画" タブを選択
2. 動画ファイル（最大60秒）をアップロード
3. "🔍 診断開始" をクリック
4. フレームごとに分析されます

### 5. Webサイト診断

1. "🌐 Webサイト" タブを選択
2. URLを入力（例: https://example.com/sustainability）
3. "🔍 診断開始" をクリック
4. ページ全体が分析されます

---

## 🎯 推奨設定

### 初めての方
- **AIモデル**: Claude（より詳細な分析）
- **指令**: 両指令適用（包括的診断）
- **バージョン**: Version 3 - Climate特化版

### クイックチェック用
- **指令**: エンパワメント指令のみ
- **バージョン**: Version 2 - 重要項目版

### 法務レビュー用
- **指令**: 両指令適用
- **バージョン**: Version 1 - 完全版

---

## 🐛 トラブルシューティング

### エラー: "Module not found"
```bash
pip install -r requirements.txt
```

### エラー: "API key invalid"
- APIキーが正しくコピーされているか確認
- 有効なAPIキーか確認（Anthropic/OpenAIのコンソールで）

### PDFが読めない
- 暗号化されていないPDFか確認
- テキスト抽出可能なPDF（スキャンPDFではない）か確認

### 動画が処理できない
- ファイル形式が mp4/mov/avi か確認
- ファイルサイズが200MB以下か確認
- ffmpegがインストールされているか確認

### スプレッドシート出力エラー
- サービスアカウントにスプレッドシートの編集権限があるか確認
- スプレッドシートIDが正しいか確認
- secrets.tomlの形式が正しいか確認

---

## 📝 よくある質問

### Q: APIの料金はどのくらい？
A: 
- Claude: $3 per million input tokens, $15 per million output tokens
- ChatGPT: 使用量に応じて変動（詳細はOpenAIのpricing参照）
- 1回の診断で数セント〜数十セント程度

### Q: 診断結果の精度は？
A: EU指令の条文に基づいてAIが評価しますが、最終的な法的判断は専門の弁護士に相談することを推奨します。

### Q: オフラインで使える？
A: いいえ。AIによる分析にはインターネット接続とAPIキーが必要です。

### Q: 日本語以外の言語にも対応している？
A: 現在は日本語に特化していますが、EU指令の原文は英語ベースなので、英語のテキストも診断可能です。

### Q: 複数ファイルを一度に診断できる？
A: 現バージョンでは1ファイルずつですが、将来的に一括診断機能を追加予定です。

---

## 🎉 完成！

これでClimateWash診断ツールが使えるようになりました！

何か問題があれば、READMEを参照するか、Issueを作成してください。

**Happy diagnosing! 🌍✨**
