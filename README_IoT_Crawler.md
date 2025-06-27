# IoT Device Crawler

IoTデバイスのWebインターフェースを自動クロールし、セキュリティ分析とFuzzing準備を行う専用ツールです。

## 🎯 主な機能

- **自動認証**: フォームベース認証の自動処理
- **フレーム対応**: 従来のIoTデバイスUIに多いフレームセット構造に対応
- **包括的クロール**: 全ページ・フレーム・フォームの自動発見
- **構造分析**: DOM構造・URL構造・セキュリティコンテキストの詳細分析
- **再現性保証**: Fuzzingで同じ状態を再現可能なセッション管理
- **Fuzzing準備**: 攻撃面分析と最適化されたFuzzingデータ生成

## 🏗️ アーキテクチャ

```
lab-clawler/
├── legacy_crawlers/       # 従来クローラー（v1.x）
│   ├── simple_crawler.py
│   ├── authentication_crawler.py
│   └── new_web_get.py
└── nextgen_crawler/       # 次世代クローラー（v2.0）
    ├── iot_crawler/
    │   ├── config.py              # 設定管理
    │   ├── authentication.py      # 認証処理
    │   ├── page_crawler.py        # ページクロール
    │   ├── session_manager.py     # セッション管理
    │   ├── structure_analyzer.py  # 構造分析
    │   ├── output_manager.py      # 出力管理
    │   ├── main_crawler.py        # メイン統合クローラー
    │   └── __init__.py            # パッケージ初期化
    └── iot_crawler_cli.py         # コマンドライン実行
```

## 🚀 クイックスタート

### 1. 環境準備

```bash
# 次世代クローラーディレクトリに移動
cd nextgen_crawler

# 依存関係のインストール
pip install -r requirements_nextgen.txt

# ChromeDriverのインストール（システムPATH設定）
# macOS: brew install chromedriver
# Ubuntu: sudo apt-get install chromium-chromedriver
```

### 2. 基本実行

```bash
# 次世代クローラーディレクトリで実行
cd nextgen_crawler

# 基本クロール
python iot_crawler_cli.py crawl --url http://192.168.1.1 --user admin --pass password

# 詳細出力モード
python iot_crawler_cli.py crawl -v --url http://localhost:8888 --user admin --pass password

# カスタム出力ディレクトリ
python iot_crawler_cli.py crawl --url http://192.168.1.1 -o /tmp/iot_analysis
```

### 3. 環境変数設定

```bash
export IOT_CRAWLER_TARGET_URL="http://192.168.1.1"
export IOT_CRAWLER_USERNAME="admin"
export IOT_CRAWLER_PASSWORD="password"
export IOT_CRAWLER_PAGE_TIMEOUT="3"
export IOT_CRAWLER_OUTPUT_DIR="./analysis_results"

# 環境変数使用でのクロール
python iot_crawler_cli.py crawl
```

## 📊 出力構造

```
nextgen_crawler/iot_crawler_output/
├── html/                  # 取得したHTMLファイル
├── frames/                # フレーム別HTMLファイル
├── json/                  # 構造化データ（JSON）
├── analysis/              # 構造分析結果
├── fuzzing/               # Fuzzing準備データ
├── sessions/              # セッション再現データ
├── screenshots/           # スクリーンショット（オプション）
└── logs/                  # 実行ログ
```

## 🔧 高度な使用方法

### セッション復元

```bash
# 次世代クローラーディレクトリで実行
cd nextgen_crawler

# 前回のセッションを復元
python iot_crawler_cli.py restore --session-file ./iot_crawler_output/sessions/session_abc123.json
```

### カスタマイズ実行

```bash
# 次世代クローラーディレクトリで実行
cd nextgen_crawler

# フレームクロール無効
python iot_crawler_cli.py crawl --url http://192.168.1.1 --no-frames

# 深度制限
python iot_crawler_cli.py crawl --url http://192.168.1.1 --max-depth 5

# スクリーンショット有効
python iot_crawler_cli.py crawl --url http://192.168.1.1 --screenshots

# ヘッドフル実行（デバッグ用）
python iot_crawler_cli.py crawl --url http://192.168.1.1 --headful
```

## 🐍 プログラム使用例

```python
# nextgen_crawler/ディレクトリ内で実行
import sys
sys.path.append('./iot_crawler')
from iot_crawler.main_crawler import create_iot_crawler

# クローラー作成
crawler = create_iot_crawler(
    target_url="http://192.168.1.1",
    username="admin", 
    password="password",
    verbose=True
)

# 初期化
if crawler.initialize():
    # 完全クロール実行
    results = crawler.run_full_crawl()
    
    # 結果確認
    print(f"Pages crawled: {results['crawl_summary']['total_pages']}")
    print(f"Fuzzing readiness: {results['fuzzing_readiness']['level']}")
```

## 🎯 Fuzzing連携

クローラーは以下のFuzzing準備データを生成します：

### 1. 攻撃面分析
- 入力ポイント（フォーム、パラメータ）
- エンドポイント分類（設定、アクション、API）
- CSRF保護状況
- 潜在的脆弱性

### 2. 再現データ
- 認証状態（Cookie、セッション）
- クロール経路
- フレーム構造
- フォーム情報

### 3. 最適化データ
- 優先度付きターゲット
- セキュリティコンテキスト
- 入力検証制約
- 推奨Fuzzing戦略

## 🔒 セキュリティ考慮事項

### 対象デバイス
- **推奨**: テスト環境・開発環境のIoTデバイス
- **注意**: 本番環境での使用は適切な許可を得てから実行

### 実行環境
- ネットワーク分離されたテスト環境での実行を推奨
- 認証情報の安全な管理
- 出力データの適切な保護

## 🐛 トラブルシューティング

### ChromeDriverエラー
```bash
# ChromeDriverのバージョン確認
chromedriver --version

# パス確認
which chromedriver
```

### 認証失敗
```bash
# 詳細ログで実行
python iot_crawler_cli.py crawl -v --url http://192.168.1.1

# ヘッドフル実行でデバッグ
python iot_crawler_cli.py crawl --headful --url http://192.168.1.1
```

### タイムアウトエラー
```bash
# タイムアウト延長
python iot_crawler_cli.py crawl --timeout 10 --url http://192.168.1.1
```

## 📈 パフォーマンス最適化

### 推奨設定
```bash
# 軽量実行（フレーム・スクリーンショット無効）
python iot_crawler_cli.py crawl --no-frames --url http://192.168.1.1

# 深度制限
python iot_crawler_cli.py crawl --max-depth 3 --url http://192.168.1.1
```

### リソース使用量
- **メモリ**: 100-500MB（対象サイトサイズに依存）
- **CPU**: 中程度（Selenium WebDriver使用）
- **ディスク**: 10-100MB（クロール規模に依存）

## 🔮 今後の拡張

- [ ] 並列クロール対応
- [ ] API自動発見強化
- [ ] 追加認証方式対応（Basic認証、トークン認証）
- [ ] Fuzzing結果フィードバック
- [ ] レポート生成機能
- [ ] Webダッシュボード

## 📄 ライセンス

このプロジェクトは研究・教育目的で開発されています。
商用利用時は適切な許可を得てください。

## 🤝 コントリビューション

プルリクエストやイシューレポートを歓迎します。
セキュリティ関連の発見は責任ある開示をお願いします。