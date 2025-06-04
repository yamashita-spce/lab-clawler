# Firmfuzz クローラー改良版

このレポジトリは、Firmfuzzのクローラーを改良したモデルの検証を目的としています。

## プロジェクト概要

本プロジェクトは、IoTデバイスのWebインターフェースを効率的に走査するためのクローラーを開発・検証します。特に、認証が必要なページやJavaScriptを多用するモダンなWebアプリケーションへの対応を目指します。

## 使用方法

### シンプルクローラー

基本的なWebページ取得には `simple_crawler.py` を使用します。

```bash
python simple_crawler.py [対象URL]
```

例:
```bash
python simple_crawler.py http://localhost:8888/
```

### 認証クローラー

認証が必要なページやフレームセットを含むページには `authentication_crawler.py` を使用します。このスクリプトは、指定されたURLのページとフレームセット内のフレームのHTMLを取得・保存します。認証機能は現在開発中です。

```bash
python authentication_crawler.py [対象URL]
```

例:
```bash
python authentication_crawler.py http://localhost:8888/
```

## 環境構築

本プロジェクトを実行するには、以下の手順で環境を構築してください。

1. **Pythonのインストール**
   Python 3.8以上のバージョンが必要です。公式サイトからダウンロード・インストールしてください。

2. **依存ライブラリのインストール**
   以下のコマンドを実行し、必要なライブラリをインストールします。

   ```bash
   pip install -r requirements.txt
   ```

3. **ChromeDriverのインストール**
   Seleniumを使用するため、ChromeDriverが必要です。お使いのChromeブラウザのバージョンに合ったChromeDriverをダウンロードし、システムのPATHが通っている場所に配置してください。

## 今後の開発予定

- 認証機能の強化
- JavaScriptフレームワークへの対応
- プロキシ連携によるネットワークトラフィック監視
- DOM構造解析と類似度判定
- フォーム入力と送信処理
- レポート生成機能
