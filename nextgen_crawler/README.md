# 次世代IoTクローラー（Next-Gen IoT Crawler）

## 概要
IoTデバイスのWebインターフェースに対する包括的なセキュリティ分析とFuzzing準備を行う次世代クローラーシステムです。フレームセット型UIや複雑な認証機構を持つIoTデバイスに特化した設計により、従来のクローラーでは困難だった深度の高い分析を実現します。

## ディレクトリ構成

### 🏗️ アーキテクチャ概要
```
nextgen_crawler/
├── iot_crawler/                    # コアエンジンモジュール
│   ├── __init__.py                 # モジュール初期化
│   ├── config.py                   # 設定管理・環境変数処理
│   ├── authentication.py          # 汎用認証エンジン（フレーム対応）
│   ├── page_crawler.py            # ページクローリングエンジン
│   ├── session_manager.py         # セッション状態管理・再現性保証
│   ├── structure_analyzer.py      # DOM/URL/セキュリティ分析
│   ├── output_manager.py          # 多形式出力生成管理
│   └── main_crawler.py            # メインオーケストレーター
├── fuzzing_page_crawler.py         # Fuzzing特化クローラー
├── visible_fuzzing_crawler.py      # デバッグ用可視化クローラー  
├── visualization_generator.py      # 結果可視化ツール
├── iot_crawler_cli.py             # 標準CLIインターフェース
├── test_iot_crawler.py            # テストファイル
├── test_login_simple.py           # 簡易ログインテスト
├── requirements_nextgen.txt        # 次世代クローラー専用依存関係
├── README.md                       # このファイル（次世代クローラー説明）
├── iot_crawler_output/            # 出力データディレクトリ
│   ├── html/                       # 生HTMLページ・フレーム
│   ├── frames/                     # 個別フレームコンテンツ
│   ├── json/                       # 構造化クロールデータ
│   ├── analysis/                   # セキュリティ分析結果
│   ├── fuzzing/                    # Fuzzing準備データ・レポート
│   ├── sessions/                   # セッション再現データ
│   └── logs/                       # 詳細実行ログ
└── [その他の出力ファイル]           # 実行時生成される結果ファイル
```

### 🔧 コアモジュール詳細（iot_crawler/）
- **config.py** 
  - 機能: 設定管理・環境変数処理・デフォルト値定義
  - クラス: CrawlerConfig, CrawlerLogger
  - 設定項目: URL, 認証情報, タイムアウト, 出力ディレクトリ等

- **authentication.py** 
  - 機能: 汎用認証エンジン（フレーム対応）
  - クラス: IoTAuthenticator
  - 機能: 多段階認証、要素検出、成功確認、IoT固有対応

- **page_crawler.py** 
  - 機能: ページクローリングエンジン
  - クラス: IoTPageCrawler, PageData, FrameData
  - 機能: BFS探索、フレーム処理、リンク抽出、フォーム分析

- **session_manager.py** 
  - 機能: セッション状態管理・再現性保証
  - クラス: IoTSessionManager, SessionState, CrawlSession
  - 機能: 状態キャプチャ、セッション復元、履歴記録

- **structure_analyzer.py** 
  - 機能: DOM/URL/セキュリティ分析
  - クラス: IoTStructureAnalyzer, DOMElement, URLStructure, SecurityContext
  - 機能: 構造分析、脆弱性検出、Fuzzing準備

- **output_manager.py** 
  - 機能: 多形式出力生成管理
  - クラス: IoTOutputManager
  - 機能: HTML/JSON/ログ保存、ファイル管理

- **main_crawler.py** 
  - 機能: メインオーケストレーター
  - クラス: IoTMainCrawler
  - 機能: 全体制御、コンポーネント統合、結果生成

### 🎯 専用クローラーファイル
- **fuzzing_page_crawler.py** 
  - 機能: Fuzzing準備に特化した包括的クローラー
  - クラス: FuzzingPageCrawler
  - 機能: 全ページ・エンドポイント網羅的発見、セキュリティコンテキスト分析、優先度付きFuzzing対象特定、完全セッション状態キャプチャ

- **visible_fuzzing_crawler.py** 
  - 機能: デバッグ・デモ用可視化クローラー
  - クラス: VisibleFuzzingCrawler
  - 機能: ブラウザ動作の実時間表示、ステップバイステップ実行、認証プロセスの可視化

- **iot_crawler_cli.py** 
  - 機能: 標準CLIインターフェース
  - 機能: コマンドライン操作、設定管理、バッチ実行

### 📊 分析・可視化ツール
- **visualization_generator.py** 
  - 機能: 包括的結果可視化システム
  - クラス: FuzzingVisualizationGenerator
  - 出力: ページ構造図、Fuzzing対象分析、脆弱性分布図、セキュリティダッシュボード、フレーム関係図、総合レポート

### 🧪 テストファイル
- **test_iot_crawler.py** 
  - 機能: 次世代クローラー総合テスト
  - 対象: コアモジュール全体の統合テスト

- **test_login_simple.py** 
  - 機能: 簡易ログインテスト
  - 対象: 認証機能の単体テスト

## 使用方法

### 🚀 クイックスタート

#### 1. 標準クローラー（基本分析）
```bash
# 次世代クローラーディレクトリに移動
cd nextgen_crawler

# 基本クロール
python iot_crawler_cli.py crawl --url http://192.168.1.1 --user admin --pass password

# 詳細出力
python iot_crawler_cli.py --verbose crawl --url http://192.168.1.1 --timeout 10 -o /tmp/results
```

#### 2. Fuzzing特化クローラー（推奨）
```bash
# 包括的Fuzzing準備クロール
python fuzzing_page_crawler.py --url http://127.0.0.1:8888 --username admin --password password

# カスタム出力ファイル（タイムスタンプ自動付与）
python fuzzing_page_crawler.py --url http://192.168.1.1 --output custom_analysis.json
```

#### 3. 結果可視化
```bash
# 自動タイムスタンプ付きフォルダで可視化
python visualization_generator.py --input fuzzing_results.json

# カスタム出力フォルダ
python visualization_generator.py --input fuzzing_results.json --output analysis_report
```

### 🔧 高度な使用法

#### デバッグ・デモ用可視化クローラー
```bash
# ブラウザ動作を見ながら実行（デバッグ用）
python visible_fuzzing_crawler.py --url http://127.0.0.1:8888

# 高速モード（スロー実行無効）
python visible_fuzzing_crawler.py --url http://127.0.0.1:8888 --fast
```

#### 標準クローラーの高度使用
```bash
# セッション復元
python iot_crawler_cli.py restore --session-file ./iot_crawler_output/sessions/abc123/session.json

# カスタム設定
python iot_crawler_cli.py crawl --max-depth 5 --no-frames --screenshots --headful

# 状態監視
python iot_crawler_cli.py status
```

#### 環境変数による設定
```bash
# 環境変数設定
export IOT_CRAWLER_TARGET_URL="http://192.168.1.1"
export IOT_CRAWLER_USERNAME="admin"
export IOT_CRAWLER_PASSWORD="password"
export IOT_CRAWLER_OUTPUT_DIR="./custom_output"

# 環境変数使用実行
python iot_crawler_cli.py crawl
python fuzzing_page_crawler.py
```

### 💻 プログラム使用法

#### 標準APIの使用
```python
# nextgen_crawler/ディレクトリ内で実行
import sys
sys.path.append('./iot_crawler')
from iot_crawler.main_crawler import create_iot_crawler

crawler = create_iot_crawler(
    target_url="http://192.168.1.1",
    username="admin",
    password="password", 
    verbose=True
)

if crawler.initialize():
    results = crawler.run_full_crawl()
    print(f"Fuzzing準備度: {results['fuzzing_readiness']['level']}")
```

#### Fuzzing特化クローラーの使用
```python
from fuzzing_page_crawler import FuzzingPageCrawler

crawler = FuzzingPageCrawler(
    target_url="http://192.168.1.1",
    username="admin",
    password="password"
)

if crawler.initialize():
    results = crawler.run_comprehensive_crawl()
    output_file = crawler.save_results("custom_results.json")
    print(f"Analysis saved to: {output_file}")
```

#### 可視化システムの使用
```python
from visualization_generator import FuzzingVisualizationGenerator

generator = FuzzingVisualizationGenerator("crawl_results.json")
output_dir = generator.generate_all_visualizations("custom_analysis")
print(f"Visualizations saved to: {output_dir}")
```

## 🔧 環境構築

### 依存関係のインストール
```bash
# 次世代クローラー専用の依存関係
pip install -r requirements_nextgen.txt

# または手動インストール
pip install selenium webdriver-manager beautifulsoup4 lxml requests dataclasses-json python-dotenv pyyaml matplotlib networkx pandas seaborn
```

### ChromeDriverの設定
```bash
# macOS
brew install chromedriver

# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# 手動インストール
# ChromeDriverをダウンロードしてPATHに追加
```

## 🎯 主要機能

### 🔐 認証・セッション管理
- **フレーム対応認証**: 複雑なフレームセット型UIの自動ログイン
- **セッション状態管理**: 完全な認証状態キャプチャと再現
- **アラート処理**: モーダルダイアログやJavaScriptアラートの自動処理
- **CSRF対応**: セキュリティトークンの自動検出と管理

### 🕷️ 包括的クローリング
- **深度優先探索**: 設定可能な最大深度でのページ発見
- **フレーム完全対応**: ネストしたフレーム構造の自動解析
- **動的コンテンツ**: JavaScript生成リンクの自動発見
- **コンテンツフィルタ**: 危険なエンドポイント（logout, reboot等）の自動回避

### 🔍 セキュリティ分析
- **脆弱性検出**: CSRF, XSS, SQL Injection等の脆弱性指標自動検出
- **入力フィールド分析**: 全入力要素の詳細分析とFuzzing優先度付け
- **セキュリティトークン**: CSRF トークン等のセキュリティ機構の検出
- **攻撃対象分類**: エンドポイントタイプ別の自動分類

### 📊 Fuzzing準備
- **優先度付きターゲット**: リスクベースの攻撃対象優先順位付け
- **完全な再現性**: セッション状態・ナビゲーションパスの完全記録
- **パラメータ分析**: 各入力パラメータの詳細特性分析
- **攻撃面マッピング**: 包括的な攻撃対象の可視化

### 📈 結果可視化
- **6種類の専門グラフ**: 構造図、脆弱性分布、Fuzzing分析等
- **セキュリティダッシュボード**: リスクスコア、推奨事項等の統合表示
- **総合レポート**: エグゼクティブサマリー付きの包括的分析レポート
- **自動出力管理**: タイムスタンプ付きディレクトリの自動生成

## 🎯 対応デバイス・環境

### 確認済み対応デバイス
- **Netgear ルーター** - 完全対応（フレームセット型UI）
- **TP-Link ルーター** - 基本対応
- **ASUS ルーター** - 基本対応
- **汎用IoTデバイス** - フレームセット・フォーム認証対応

### テスト環境
```bash
# ローカルテスト環境
python fuzzing_page_crawler.py --url http://127.0.0.1:8888 --username admin --password password

# 実機テスト
python fuzzing_page_crawler.py --url http://192.168.1.1 --username admin --password admin

# 可視化テスト
python visible_fuzzing_crawler.py --url http://127.0.0.1:8888
```

### 実行例・ベンチマーク
```bash
# 典型的な実行結果例
Target: http://127.0.0.1:8888
Pages discovered: 6
Fuzzing targets: 2 (High-priority: 2)
Security findings: 3 vulnerability types
Execution time: ~30-60 seconds
```

## ⚡ パフォーマンス仕様

### システム要件
- **メモリ**: 100-500MB（対象の複雑度による）
- **CPU**: 中程度負荷（クローリング中）
- **ディスク**: 10-100MB/セッション
- **ネットワーク**: 対象レスポンス時間に依存

### スケーラビリティ
- **単一ターゲット**: 徹底的分析に最適化
- **セッション分離**: 複数同時実行対応
- **出力管理**: 自動タイムスタンプ管理
- **リソース管理**: 自動クリーンアップ

### 信頼性
- **エラー回復**: ネットワーク・WebDriver問題の優雅な処理
- **状態検証**: 継続的な認証状態確認
- **タイムアウト管理**: 設定可能なタイムアウトポリシー
- **完全ログ**: デバッグ・監査用の詳細ログ記録

## 🏆 従来システムとの比較

| 特徴 | 従来クローラー | 次世代クローラー |
|------|-------------|----------------|
| 認証方式 | Netgear特化 | 汎用フレーム対応 |
| 出力形式 | HTML のみ | HTML/JSON/可視化 |
| Fuzzing準備 | なし | 完全対応 |
| セッション管理 | 基本 | 完全再現性 |
| 脆弱性検出 | なし | 自動検出 |
| 可視化 | なし | 6種類のグラフ |
| モジュール性 | 単一ファイル | 8モジュール構成 |

## 🔒 セキュリティ考慮事項

### 使用上の注意
- **承認**: 対象システムの事前承認必要
- **環境**: テスト・開発環境での使用推奨
- **ネットワーク**: 可能な限り分離ネットワークで実行
- **データ保護**: 認証情報・出力データの適切な管理

### 倫理的使用
- **責任ある開示**: 発見された脆弱性の適切な報告
- **法的遵守**: 適用法規制・ポリシーの遵守
- **目的限定**: セキュリティ向上目的での使用限定