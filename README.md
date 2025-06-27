# IoTデバイス Webクローラープロジェクト

## プロジェクト概要
IoTデバイス（特にルーター）のWebインターフェースを自動クローリングし、セキュリティ分析とFuzzing準備を行う統合システムです。

## ディレクトリ構成

```
lab-clawler/
├── legacy_crawlers/           # 従来クローラー（v1.x系）
│   ├── simple_crawler.py      # 基本HTTPクローラー
│   ├── authentication_crawler.py  # 認証対応クローラー
│   ├── new_web_get.py         # フレームエンドポイント探索
│   ├── fix_webdriver.py       # WebDriver設定修正
│   ├── requirements_legacy.txt # 従来クローラー依存関係
│   ├── README_legacy.md       # 従来クローラー説明書
│   ├── crawl_output/          # 従来クローラー出力
│   └── frames_html/           # フレーム出力
│
├── nextgen_crawler/           # 次世代クローラー（v2.0）
│   ├── iot_crawler/           # コアモジュール
│   │   ├── config.py          # 設定管理
│   │   ├── authentication.py  # 認証エンジン
│   │   ├── page_crawler.py    # ページクローリング
│   │   ├── session_manager.py # セッション管理
│   │   ├── structure_analyzer.py # 構造分析
│   │   ├── output_manager.py  # 出力管理
│   │   └── main_crawler.py    # メインオーケストレーター
│   ├── iot_crawler_cli.py     # CLIインターフェース
│   ├── test_iot_crawler.py    # テストファイル
│   ├── requirements_nextgen.txt # 次世代クローラー依存関係
│   ├── README_nextgen.md      # 次世代クローラー説明書
│   └── iot_crawler_output/    # 次世代クローラー出力
│
├── PROJECT_SPECIFICATION.md   # 英語版技術仕様書
├── PROJECT_SPECIFICATION_JP.md # 日本語版技術仕様書
├── CLAUDE.md                  # Claude Code用プロジェクト指示
├── README.md                  # このファイル
└── requirements.txt           # 全体依存関係（共通）
```

## クローラー比較

### 従来クローラー（Legacy Crawlers）
- **特徴**: シンプル、軽量、単一ファイル構成
- **対象**: 特定デバイス（主にNetgear）
- **機能**: 基本的なHTMLクローリング
- **用途**: 小規模・簡単なクローリング作業
- **状況**: メンテナンスモード

### 次世代クローラー（Next-Gen Crawler）
- **特徴**: モジュラー、包括的、高機能
- **対象**: 汎用IoTデバイス（ルーター中心）
- **機能**: セキュリティ分析、Fuzzing準備、セッション管理
- **用途**: 本格的なセキュリティテスト準備
- **状況**: アクティブ開発・推奨

## クイックスタート

### 環境構築
```bash
# プロジェクトクローン
git clone <repository-url>
cd lab-clawler

# 従来クローラー使用の場合
cd legacy_crawlers
pip install -r requirements_legacy.txt

# 次世代クローラー使用の場合（推奨）
cd nextgen_crawler  
pip install -r requirements_nextgen.txt
```

### 基本使用法

#### 従来クローラー
```bash
cd legacy_crawlers

# 基本クローリング
python authentication_crawler.py http://192.168.1.1

# ログイン付きクローリング
python authentication_crawler.py http://192.168.1.1 --login --username admin --password password
```

#### 次世代クローラー（推奨）
```bash
cd nextgen_crawler

# 基本クローリング
python iot_crawler_cli.py crawl --url http://192.168.1.1 --user admin --pass password

# 詳細分析付きクローリング
python iot_crawler_cli.py --verbose crawl --url http://127.0.0.1:8888 --user admin --pass password
```

## テスト環境
```bash
# テスト用IoTエミュレーター（Netgear）
http://127.0.0.1:8888

# デフォルト認証情報
Username: admin
Password: password
```

## 出力データ

### 従来クローラー出力
- `crawl_output/` - HTMLファイル
- `frames_html/` - フレームファイル

### 次世代クローラー出力
- `iot_crawler_output/html/` - 生HTMLページ
- `iot_crawler_output/frames/` - フレームコンテンツ
- `iot_crawler_output/json/` - 構造化データ
- `iot_crawler_output/analysis/` - セキュリティ分析
- `iot_crawler_output/fuzzing/` - Fuzzing準備データ
- `iot_crawler_output/sessions/` - セッション再現データ
- `iot_crawler_output/logs/` - 実行ログ

## 環境変数

```bash
# 次世代クローラー設定例
export IOT_CRAWLER_TARGET_URL="http://192.168.1.1"
export IOT_CRAWLER_USERNAME="admin"
export IOT_CRAWLER_PASSWORD="password"
export IOT_CRAWLER_PAGE_TIMEOUT="60"
export IOT_CRAWLER_OUTPUT_DIR="./iot_crawler_output"
export IOT_CRAWLER_HEADLESS="true"
```

## 対応デバイス

### 確認済み対応
- Netgear ルーター （完全対応）
- TP-Link ルーター （基本対応）
- ASUS ルーター （基本対応）

### 対応予定
- Linksys ルーター
- D-Link ルーター
- IoTカメラ各種
- スマートホーム機器

## 開発履歴
- **v1.0** - 初期実装（simple_crawler.py）
- **v1.5** - 認証対応（authentication_crawler.py）
- **v2.0** - 次世代システム（iot_crawler/）

## ライセンス
このプロジェクトは研究・教育目的で開発されています。
対象システムへの使用前に適切な承認を取得してください。

## サポート
- **技術仕様**: PROJECT_SPECIFICATION_JP.md
- **従来クローラー**: legacy_crawlers/README_legacy.md
- **次世代クローラー**: nextgen_crawler/README_nextgen.md