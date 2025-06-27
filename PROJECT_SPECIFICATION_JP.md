# IoTデバイス Webクローラー - プロジェクト仕様書

**バージョン**: 2.0  
**最終更新**: 2025-03-05  
**プロジェクト状況**: 本番環境対応済み

---

## 📋 プロジェクト概要

### 目的
IoTデバイス（特にルーター）のWebインターフェースに対する包括的なセキュリティ分析とFuzzing事前準備を行う統合クローラーシステム。

### 対象デバイス
- **主要対象**: IoTルーター（Netgear、TP-Link、ASUS等）
- **副次対象**: IoTカメラ、スマートホーム機器
- **UI タイプ**: フレームセット型従来UI、モダンSPA両対応

### 開発環境
- **Python**: 3.8+
- **OS**: macOS、Linux（Windows対応済み）
- **ブラウザ**: Chrome + ChromeDriver
- **テスト環境**: http://127.0.0.1:8888（Netgearエミュレーター）

---

## 🏗️ システム構成

### コンポーネント概要
```
lab-clawler/
├── legacy_crawlers/           # 従来クローラー (v1.x)
│   ├── simple_crawler.py      # 基本HTTPクローラー
│   ├── authentication_crawler.py  # 認証強化クローラー
│   ├── new_web_get.py         # フレームエンドポイント探索
│   ├── fix_webdriver.py       # WebDriver設定修正
│   ├── requirements_legacy.txt # 従来クローラー依存関係
│   ├── README_legacy.md       # 従来クローラー説明書
│   ├── crawl_output/          # 従来クローラー出力
│   └── frames_html/           # フレーム出力
│
└── nextgen_crawler/           # 次世代IoTクローラー (v2.0)
    ├── iot_crawler/           # モジュラーアーキテクチャ
    │   ├── config.py          # 設定管理
    │   ├── authentication.py  # 認証エンジン
    │   ├── page_crawler.py    # ページクローリングエンジン
    │   ├── session_manager.py # セッション状態管理
    │   ├── structure_analyzer.py  # DOM/URL/セキュリティ分析
    │   ├── output_manager.py  # 出力生成
    │   └── main_crawler.py    # メインオーケストレーター
    ├── iot_crawler_cli.py     # コマンドラインインターフェース
    ├── test_iot_crawler.py    # テストファイル
    ├── requirements_nextgen.txt # 次世代クローラー依存関係
    ├── README_nextgen.md      # 次世代クローラー説明書
    └── iot_crawler_output/    # 次世代クローラー出力
```

## 🔧 技術仕様

### 核心技術
- **Web自動化**: Selenium WebDriver 4.15+
- **HTML解析**: BeautifulSoup 4.12+
- **HTTPクライアント**: Requests 2.31+
- **データ処理**: Dataclasses、JSON
- **設定管理**: 環境変数、YAML

### ブラウザ設定
```python
# 最適化されたChrome設定（動作確認済み）
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
# 安定性重視のシンプル設定
```

### タイムアウト設定
- **ページ読み込み**: 60秒
- **要素待機**: 10秒  
- **フレーム待機**: 10秒
- **セッション**: 環境変数で設定可能

---

## 🚀 機能仕様

### 1. 認証システム

#### サポート認証方式
- **フォームベース認証**（主要）
  - ユーザー名/パスワードフィールド自動検出
  - 複数セレクターパターン対応
  - フレーム対応認証

#### 自動検出パターン
```python
# ユーザー名フィールド検出
username_selectors = [
    (By.ID, "username"), (By.ID, "user"), (By.ID, "login"), 
    (By.NAME, "username"), (By.NAME, "user"), 
    (By.XPATH, "//input[@type='text']"), (By.XPATH, "//input[@type='email']")
]

# パスワードフィールド検出  
password_selectors = [
    (By.ID, "password"), (By.ID, "passwd"), (By.ID, "pass"),
    (By.NAME, "password"), (By.NAME, "passwd"),
    (By.XPATH, "//input[@type='password']")
]

# 送信ボタン検出
button_selectors = [
    (By.XPATH, "//input[@type='submit']"), (By.XPATH, "//button[@type='submit']"),
    (By.XPATH, "//input[@type='image']"), (By.XPATH, "//button[contains(text(), 'Login')]")
]
```

#### 認証フロー
1. **メインページ認証**: 直接ログインフォーム検出
2. **優先フレーム認証**: ['master', 'main', 'content', 'login', 'auth']
3. **包括フレーム検索**: 検出された全フレーム
4. **成功検証**: 複数パターン成功検出

### 2. ページクローリングシステム

#### クローリング機能
- **再帰的リンク追跡**: 設定可能深度（デフォルト: 10）
- **フレーム処理**: 完全フレームセット対応
- **コンテンツ重複排除**: ハッシュベース重複検出
- **フォーム抽出**: 自動フォーム構造分析
- **リンクマッピング**: 完全URL関係マッピング

#### フレームサポート
```python
# フレーム処理ワークフロー
1. フレーム検出（frame + iframeタグ）
2. 動的ソース待機（JavaScript実行対応）
3. フレーム切替＆コンテンツ抽出
4. ネストフレーム処理
5. コンテキスト復元
```

#### コンテンツフィルター
- **含める**: HTMLページ、APIエンドポイント、設定ページ
- **除外する**: 静的リソース（画像、CSS、JS）、外部リンク
- **特別処理**: logout、reboot、resetエンドポイント（フラグ付き、クロール除外）

### 3. 構造分析エンジン

#### DOM分析
```python
@dataclass
class DOMElement:
    tag: str                    # HTMLタグ名
    attributes: Dict[str, str]  # 全属性
    text_content: str          # 内部テキスト
    xpath: str                 # 生成XPath
    css_selector: str          # 生成CSSセレクター
    is_interactive: bool       # ユーザー相互作用可能性
    security_relevant: bool    # セキュリティ重要度
```

#### URL分類
```python
@dataclass  
class URLStructure:
    endpoint_type: str         # 'config', 'status', 'action', 'data', 'unknown'
    is_api_endpoint: bool      # APIエンドポイント検出
    path_segments: List[str]   # URLパス要素
    query_params: Dict         # クエリパラメータ分析
    file_extension: str        # ファイルタイプ検出
```

#### セキュリティコンテキスト分析
- **CSRF保護**: トークン検出・分析
- **入力検証**: HTML5検証制約
- **脆弱性検出**: 自動セキュリティ問題識別
- **セッション管理**: クッキー・セッション分析

### 4. セッション管理

#### セッション状態キャプチャ
```python
@dataclass
class SessionState:
    target_url: str            # 対象デバイスURL
    authenticated: bool        # 認証状態
    cookies: List[Dict]        # ブラウザクッキー
    local_storage: Dict        # ブラウザローカルストレージ
    session_storage: Dict      # ブラウザセッションストレージ
    auth_frame: str           # 認証フレーム名
    timestamp: float          # キャプチャタイムスタンプ
```

#### 再現性機能
- **完全状態スナップショット**: 完全ブラウザ状態キャプチャ
- **アクション記録**: ステップバイステップクロールアクションログ
- **セッション再生**: 完全セッション再現機能
- **状態検証**: 認証状態検証

### 5. 出力管理

#### 出力ディレクトリ構造
```
nextgen_crawler/iot_crawler_output/
├── html/                  # 生HTMLページ
├── frames/                # 個別フレームコンテンツ
├── json/                  # 構造化クロールデータ
├── analysis/              # セキュリティ分析レポート
├── fuzzing/               # Fuzzing準備データ
├── sessions/              # セッション再現データ
├── screenshots/           # 視覚的ドキュメント（オプション）
└── logs/                  # 詳細実行ログ
```

#### 生成データタイプ
1. **HTMLファイル**: 完全ページ・フレームコンテンツ
2. **JSONデータ**: 構造化クロール結果
3. **分析レポート**: セキュリティ・構造分析
4. **Fuzzingデータ**: 攻撃対象・テスト準備
5. **セッションファイル**: 完全再現情報

---

## 🎯 Fuzzing統合仕様

### 攻撃対象分析
```python
fuzzing_data = {
    'target_info': {
        'url': target_url,
        'authentication': 'form_based',
        'session_management': 'cookie_based'
    },
    'endpoints': [...],        # 分類済みエンドポイント
    'parameters': [...],       # 入力パラメータ
    'forms': [...],           # フォーム構造
    'csrf_tokens': [...],     # CSRF保護データ
    'vulnerabilities': [...]   # 検出脆弱性
}
```

### 脆弱性検出
- **XSSベクター**: eval()、innerHTML使用検出
- **CSRF問題**: トークン検証欠如
- **SQLインジェクション**: パラメータベース脆弱性パターン
- **パストラバーサル**: ファイルパラメータ検出
- **デフォルト認証情報**: 一般的認証情報パターン検出

### テスト推奨事項
- **優先対象**: 設定 > アクション > APIエンドポイント
- **パラメータFuzzing**: 入力検証バイパステスト
- **セッションテスト**: 認証・認可テスト
- **状態Fuzzing**: セッション状態操作テスト

---

## 📊 パフォーマンス仕様

### システム要件
- **メモリ**: 100-500MB（対象複雑度による）
- **CPU**: クローリング中は中程度負荷
- **ディスク**: クロールセッション当たり10-100MB
- **ネットワーク**: 対象応答時間に依存

### 拡張性
- **単一対象**: 徹底分析に最適化
- **セッション分離**: 複数同時セッション対応
- **リソース管理**: 自動クリーンアップ・メモリ管理

### 信頼性
- **エラー回復**: ネットワーク問題の優雅な処理
- **状態検証**: 継続的認証検証
- **タイムアウト管理**: 設定可能タイムアウトポリシー
- **ログ記録**: 包括的デバッグ・監査ログ

---

## 🔧 設定仕様

### 環境変数
```bash
# 核心設定
IOT_CRAWLER_TARGET_URL="http://192.168.1.1"
IOT_CRAWLER_USERNAME="admin"
IOT_CRAWLER_PASSWORD="password"

# タイムアウト設定  
IOT_CRAWLER_PAGE_TIMEOUT="60"
IOT_CRAWLER_ELEMENT_TIMEOUT="10"
IOT_CRAWLER_FRAME_TIMEOUT="10"

# 出力設定
IOT_CRAWLER_OUTPUT_DIR="./nextgen_crawler/iot_crawler_output"
IOT_CRAWLER_SCREENSHOTS="false"
IOT_CRAWLER_HEADLESS="true"
```

### 実行時設定
```python
@dataclass
class CrawlerConfig:
    # 基本設定
    target_url: str
    username: str = "admin"
    password: str = "password"
    
    # クローリング設定
    max_depth: int = 10
    crawl_frames: bool = True
    extract_forms: bool = True
    extract_links: bool = True
    
    # 出力設定
    save_html: bool = True
    save_json: bool = True
    save_screenshots: bool = False
```

---

## 🧪 テスト仕様

### テスト環境
- **対象**: http://127.0.0.1:8888（Netgearルーターエミュレーター）
- **認証情報**: admin/password
- **期待動作**: フレームセットベース認証・コンテンツ抽出

### 検証基準
1. **認証成功**: ログイン完了検証
2. **フレーム処理**: 全フレーム検出・処理
3. **コンテンツ抽出**: HTML・フォームデータキャプチャ
4. **セッション管理**: 状態キャプチャ・再現性
5. **出力生成**: 指定ファイルタイプ全作成

### 最新テスト結果
```
セッションID: 2e06ad6a-46ae-49d4-8ef1-4efb7c553c98
✅ 認証: 成功
✅ ページ発見: 1
✅ フレーム分析: 5  
✅ フォーム発見: 2
✅ セキュリティ分析: CSRF脆弱性検出
✅ Fuzzing準備度: 25/100（低 - 限定ページ発見による）
```

---

## 🚧 実装状況

### 完了機能 ✅
- [x] モジュラーアーキテクチャ設計
- [x] 汎用認証システム
- [x] フレーム対応ページクローリング
- [x] 完全セッション管理
- [x] DOM・セキュリティ分析
- [x] 包括的出力生成
- [x] コマンドラインインターフェース
- [x] 環境ベース設定
- [x] エラーハンドリング・ログ記録
- [x] 実環境テスト・検証

### 既知制限事項 ⚠️
1. **シングルスレッド**: 並列クローリング非対応
2. **JavaScript多用サイト**: 動的コンテンツ対応限定
3. **複雑認証**: 高度認証方式未実装
4. **大規模サイト**: 大容量サイト向けメモリ最適化必要

### 将来拡張 🔮
- [ ] マルチスレッド対応
- [ ] 高度JavaScript描画
- [ ] 追加認証方式（Basic、Token、OAuth）
- [ ] 機械学習ベース脆弱性検出
- [ ] リアルタイムFuzzing統合
- [ ] Webダッシュボードインターフェース

---

## 🔒 セキュリティ考慮事項

### 対象環境
- **推奨**: テスト/開発環境のみ
- **注意**: 本番システム使用前に適切な承認取得
- **ネットワーク**: 可能な限り分離ネットワーク使用

### データ保護
- **認証情報**: 安全な保存・転送
- **出力データ**: 機密情報処理
- **セッションデータ**: 安全なセッション状態管理
- **ログ記録**: サニタイズ済みログ出力

### 倫理的使用
- **承認**: 全対象システムに対する承認必要
- **責任ある開示**: セキュリティ発見は責任を持って報告
- **法的遵守**: 適用法規制の遵守

---

## 📚 使用例

### 基本使用法
```bash
# 次世代クローラーディレクトリに移動
cd nextgen_crawler

# シンプルクロール
python iot_crawler_cli.py crawl --url http://192.168.1.1 --user admin --pass password

# 詳細出力・カスタム出力
python iot_crawler_cli.py --verbose crawl --url http://192.168.1.1 --timeout 10 -o /tmp/results

# 環境変数ベース実行
export IOT_CRAWLER_TARGET_URL="http://192.168.1.1"
python iot_crawler_cli.py crawl
```

### 高度使用法
```bash
# 次世代クローラーディレクトリ内で実行
cd nextgen_crawler

# セッション復元
python iot_crawler_cli.py restore --session-file ./iot_crawler_output/sessions/abc123/session.json

# カスタム設定
python iot_crawler_cli.py crawl --max-depth 5 --no-frames --screenshots --headful

# 状態監視
python iot_crawler_cli.py status
```

### プログラム使用法
```python
# nextgen_crawler/ディレクトリ内で実行
import sys
sys.path.append('./iot_crawler')
from iot_crawler.main_crawler import create_iot_crawler

# クローラー作成・設定
crawler = create_iot_crawler(
    target_url="http://192.168.1.1",
    username="admin",
    password="password", 
    verbose=True
)

# 初期化・実行
if crawler.initialize():
    results = crawler.run_full_crawl()
    print(f"Fuzzing準備度: {results['fuzzing_readiness']['level']}")
```

---

## 📝 バージョン履歴

### v2.0（現在）- 本番リリース
- 完全モジュラーアーキテクチャ
- 汎用IoTデバイス対応
- 高度セキュリティ分析
- 包括的Fuzzing準備
- 完全セッション管理
- 本番テスト完了

### v1.5 - 認証強化
- 汎用認証システム（Netgear特化から発展）
- 改良フレームハンドリング
- アラート処理
- 複数認証方式

### v1.0 - 初期実装  
- 基本ページクローリング
- Netgear特化認証
- シンプルHTML抽出
- 概念実証検証

---

## 🔧 メンテナンス

### 定期更新必要項目
- **ChromeDriver**: Chromeブラウザバージョンと同期維持
- **依存関係**: Pythonパッケージセキュリティ更新
- **テスト検証**: 対象デバイスに対する定期検証

### トラブルシューティング
- **WebDriverの問題**: ChromeDriverインストール・PATH確認
- **認証失敗**: 認証情報・対象アクセス性確認
- **タイムアウトエラー**: 低速ネットワーク向けタイムアウト設定調整
- **出力の問題**: ファイルシステム権限・ディスク容量確認

### サポート
- **ドキュメント**: README.md、README_IoT_Crawler.md
- **例**: コマンドライン・プログラム使用例
- **デバッグ**: 詳細ログ・詳細エラーメッセージ

---

**仕様書終了**

*この文書は、IoTデバイスWebクローラープロジェクトの完全技術仕様書として機能します。システムの発展と新機能追加に応じて更新される必要があります。*