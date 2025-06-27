# 従来クローラー（Legacy Crawlers）

## 概要
従来のIoTデバイスWebクローラーシステムです。シンプルな単一ファイル構成で基本的なクローリング機能を提供します。

## ファイル構成

### クローラーファイル
- **simple_crawler.py** - HTTP requestsベースの基本クローラー
- **authentication_crawler.py** - Selenium使用の認証対応クローラー（汎用版）
- **new_web_get.py** - フレームエンドポイント探索特化クローラー
- **fix_webdriver.py** - WebDriverの設定修正テストファイル

### 出力ディレクトリ
- **crawl_output/** - authentication_crawler.pyの出力
- **frames_html/** - new_web_get.pyの出力

## 使用方法

### Simple Crawler
```bash
python simple_crawler.py [URL] [-o output_dir]
```

### Authentication Crawler
```bash
# 基本クローリング
python authentication_crawler.py [URL] [-o output_dir] [-w wait_seconds]

# ログイン付きクローリング
python authentication_crawler.py [URL] --login [--username USER] [--password PASS]
```

### Frame Endpoint Discovery
```bash
python new_web_get.py [URL] [-w wait_seconds] [-o output_dir]
```

## 依存関係
```bash
pip install requests selenium beautifulsoup4
```

## 特徴
- **シンプル**: 単一ファイル構成で理解しやすい
- **軽量**: 最小限の依存関係
- **実績**: 長期間使用されてきた安定システム
- **Netgear対応**: 特にNetgearデバイスで検証済み

## 制限事項
- 単一デバイス種別に特化
- セッション管理機能なし
- セキュリティ分析機能なし
- Fuzzing準備機能なし

## 移行について
より高機能な次世代クローラー（nextgen_crawler/）への移行を推奨します。
従来クローラーはメンテナンスモードとして保持されます。