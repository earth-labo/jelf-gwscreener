# 🌍環境表示解析ツール

EU指令の観点に基づくグリーンウォッシュスクリーニングシステム

## 概要

このツールは、EU消費者エンパワメント指令（Directive 2024/825）およびEUグリーンクレーム指令提案に基づいて、気候関連のグリーンウォッシュ（ClimateWash）に該当する可能性のある環境表示をスクリーニングします。

## 主な機能

### 🎯 診断機能
- **テキスト診断**: 文章から問題表現を検出
- **画像診断**: ビジュアル要素と画像内テキストを分析
- **PDF診断**: PDFドキュメント全体を解析
- **動画診断**: フレームごとの分析と音声テキスト化
- **Webサイト診断**: Webページ全体を包括的に評価

### ⚙️ 柔軟な設定
- **AIモデル選択**: Claude（Sonnet 4.5）/ ChatGPT（GPT-4）
- **指令選択**: エンパワメント指令のみ / 両指令適用
- **診断バージョン**: 完全版 / 重要項目版 / Climate特化版

### 📊 出力機能
- **画面表示**: 詳細な診断結果とビジュアル評価
- **PDFレポート**: プロフェッショナルな診断報告書
- **JSON出力**: 機械可読形式でのデータ出力
- **Googleスプレッドシート連携**: 自動的に結果を記録

### 💡 サポート機能
- **例文ライブラリ**: NG/OK表現の実例集
- **リアルタイムプレビュー**: 入力中の簡易チェック
- **診断履歴**: 過去の診断結果の一覧と統計

## インストール

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd climatewash-diagnosis
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. 必要なシステムパッケージ（動画・PDF処理用）

#### Ubuntu/Debian
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install poppler-utils
sudo apt-get install ffmpeg
```

#### macOS
```bash
brew install tesseract
brew install poppler
brew install ffmpeg
```

## 使い方

### ローカルで実行

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` にアクセスします。

### Streamlit Cloudでデプロイ

1. GitHubにリポジトリをプッシュ
2. [Streamlit Cloud](https://streamlit.io/cloud)にアクセス
3. "New app"をクリック
4. リポジトリを選択し、`app.py`を指定
5. デプロイ

## APIキーの設定

### Anthropic API（Claude）

1. [Anthropic Console](https://console.anthropic.com/)でAPIキーを取得
2. アプリのサイドバーに入力

### OpenAI API（ChatGPT）

1. [OpenAI Platform](https://platform.openai.com/)でAPIキーを取得
2. アプリのサイドバーに入力

## Googleスプレッドシート連携（オプション）

### 1. Google Cloud Projectの作成

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. Google Sheets APIとGoogle Drive APIを有効化

### 2. サービスアカウントの作成

1. 「IAMと管理」→「サービスアカウント」
2. 「サービスアカウントを作成」
3. JSONキーをダウンロード

### 3. Streamlit Secretsに設定

`.streamlit/secrets.toml`ファイルを作成：

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

Streamlit Cloudの場合は、アプリ設定の"Secrets"セクションに貼り付けます。

### 4. スプレッドシートの準備

1. Googleスプレッドシートを作成
2. サービスアカウントのメールアドレスに編集権限を付与
3. スプレッドシートIDをアプリのサイドバーに入力

## 診断基準バージョン

### Version 1: 完全版
すべての診断基準を適用。包括的な監査、法務レビューに最適。
- 項目数: 約35項目（両指令適用時）

### Version 2: 重要項目版
重要度の高い項目に絞った診断。マーケティング自己チェック、迅速スクリーニングに最適。
- 項目数: 約10-15項目

### Version 3: Climate特化版（推奨）
気候関連のみに集中。カーボンニュートラル主張、気候コミュニケーションのレビューに最適。
- 項目数: 約20-25項目（両指令適用時）

## 指令の選択

### エンパワメント指令のみ
- 法的拘束力あり（2026年9月27日施行）
- 最低限の法令遵守確認
- 診断時間が短い

### 両指令適用（推奨）
- エンパワメント指令 + グリーンクレーム指令提案
- より詳細な実証・検証要件
- ベストプラクティスへの準拠
- 将来的な規制動向への先行対応

## プロジェクト構造

```
climatewash-diagnosis/
├── app.py                          # メインアプリケーション
├── requirements.txt                # 依存パッケージ
├── README.md                       # このファイル
├── .streamlit/
│   └── config.toml                # Streamlit設定
├── config/
│   └── criteria.py                # 診断基準データ
├── modules/
│   ├── __init__.py
│   ├── ai_handler.py              # AIモデル切替・プロンプト管理
│   ├── text_analyzer.py           # テキスト診断
│   ├── image_analyzer.py          # 画像診断
│   ├── video_analyzer.py          # 動画診断
│   ├── pdf_analyzer.py            # PDF診断
│   ├── web_analyzer.py            # Webサイト診断
│   ├── evaluator.py               # 評価・点数計算
│   ├── sheets_exporter.py         # Googleスプレッドシート出力
│   └── pdf_reporter.py            # PDFレポート生成
├── prompts/
│   └── system_prompt.txt          # システムプロンプト
└── assets/
    └── criteria.md                # 診断基準（詳細版）
```

## 評価システム

診断結果は100点満点の減点方式で評価されます：

- **Compliant（86-100点）**: 適切。法的リスクは低い。
- **Low Risk（51-85点）**: 軽微な問題。情報追加により是正可能。
- **Medium Risk（16-50点）**: 中程度のClimateWash。早期の是正を推奨。
- **High Risk（0-15点）**: 重大なClimateWash。即座の是正が必要。法的リスクが極めて高い。

## 主要な診断項目

### 最重要項目（High Risk）
1. **オフセットベースの気候中立主張**（1.2）- 25-30点減点
2. **一般的・抽象的な環境主張**（1.1）- 20-30点減点
3. **未認証の持続可能性ラベル**（1.5）- 20-30点減点
4. **第三者検証の欠如**（2.4）- 25-30点減点

### 重要項目（Medium Risk）
5. **曖昧な削減表現**（3.1）- 10-15点減点
6. **ビジュアル要素の不適切使用**（4.1-4.4）- 5-25点減点

## トラブルシューティング

### APIエラー
- APIキーが正しいか確認
- APIの使用制限を確認
- ネットワーク接続を確認

### PDFが処理できない
- PDFが暗号化されていないか確認
- テキスト抽出可能なPDFか確認（スキャンPDFはOCRが必要）

### 動画が処理できない
- ファイル形式がmp4/mov/aviか確認
- ファイルサイズが200MB以下か確認
- codecs（ffmpeg）がインストールされているか確認

## ライセンス

このプロジェクトは環境保護と透明性のある企業コミュニケーションの促進を目的としています。

## お問い合わせ

質問や提案がある場合は、Issueを開いてください。

## 謝辞

このツールは以下に基づいて開発されました：
- EU消費者エンパワメント指令（Directive 2024/825）
- EUグリーンクレーム指令提案（COM(2023) 166）
- 日本環境弁護士連盟（JELF）の知見

---

**⚠️ 免責事項**: このツールは診断補助を目的としており、法的助言を提供するものではありません。正式な法的判断については、専門の弁護士にご相談ください。
