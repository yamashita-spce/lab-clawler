"""
IoT Device Crawler Configuration Module
設定管理とデフォルト値の定義
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class CrawlerConfig:
    """クローラー設定クラス"""
    
    # Basic Settings
    target_url: str
    username: str = "admin"
    password: str = "password"
    
    # Timeout Settings
    page_load_timeout: int = int(os.getenv('IOT_CRAWLER_PAGE_TIMEOUT', '3'))
    element_wait_timeout: int = int(os.getenv('IOT_CRAWLER_ELEMENT_TIMEOUT', '3'))
    frame_wait_timeout: int = int(os.getenv('IOT_CRAWLER_FRAME_TIMEOUT', '3'))
    
    # Output Settings
    output_dir: str = "iot_crawler_output"
    save_html: bool = True
    save_json: bool = True
    save_screenshots: bool = False
    
    # Browser Settings
    headless: bool = True
    window_width: int = 1920
    window_height: int = 1080
    
    # Crawling Settings
    max_depth: int = 10
    follow_external_links: bool = False
    crawl_frames: bool = True
    extract_forms: bool = True
    extract_links: bool = True
    
    # Session Management
    preserve_session: bool = True
    save_cookies: bool = True
    session_file: str = "session_data.json"
    
    # IoT Device Specific
    common_frame_names: List[str] = None
    common_login_selectors: Dict[str, List[str]] = None
    
    def __post_init__(self):
        """デフォルト値の設定"""
        if self.common_frame_names is None:
            self.common_frame_names = [
                'master', 'main', 'content', 'login', 'auth', 
                'header', 'footer', 'nav', 'menu', 'sidebar'
            ]
        
        if self.common_login_selectors is None:
            self.common_login_selectors = {
                'username': [
                    'input[name="username"]', 'input[id="username"]',
                    'input[name="user"]', 'input[id="user"]',
                    'input[name="login"]', 'input[id="login"]',
                    'input[type="text"]', 'input[type="email"]'
                ],
                'password': [
                    'input[name="password"]', 'input[id="password"]',
                    'input[name="passwd"]', 'input[id="passwd"]',
                    'input[name="pass"]', 'input[id="pass"]',
                    'input[type="password"]'
                ],
                'submit': [
                    'input[type="submit"]', 'button[type="submit"]',
                    'input[type="image"]', 'button[id="login"]',
                    'input[value*="Login"]', 'input[value*="ログイン"]',
                    'button:contains("Login")', 'button:contains("ログイン")'
                ]
            }

class CrawlerLogger:
    """ログ管理クラス"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logs = []
    
    def info(self, message: str):
        """情報ログ"""
        log_entry = f"[INFO] {message}"
        self.logs.append(log_entry)
        if self.verbose:
            print(log_entry)
    
    def error(self, message: str):
        """エラーログ"""
        log_entry = f"[ERROR] {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def warning(self, message: str):
        """警告ログ"""
        log_entry = f"[WARNING] {message}"
        self.logs.append(log_entry)
        if self.verbose:
            print(log_entry)
    
    def debug(self, message: str):
        """デバッグログ"""
        log_entry = f"[DEBUG] {message}"
        self.logs.append(log_entry)
        if self.verbose:
            print(log_entry)
    
    def get_logs(self) -> List[str]:
        """全ログの取得"""
        return self.logs.copy()
    
    def save_logs(self, filepath: str):
        """ログをファイルに保存"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for log in self.logs:
                f.write(log + '\n')

def load_config_from_env() -> CrawlerConfig:
    """環境変数から設定を読み込み"""
    return CrawlerConfig(
        target_url=os.getenv('IOT_CRAWLER_TARGET_URL', 'http://localhost:8888'),
        username=os.getenv('IOT_CRAWLER_USERNAME', 'admin'),
        password=os.getenv('IOT_CRAWLER_PASSWORD', 'password'),
        output_dir=os.getenv('IOT_CRAWLER_OUTPUT_DIR', 'iot_crawler_output'),
        headless=os.getenv('IOT_CRAWLER_HEADLESS', 'true').lower() == 'true',
        save_screenshots=os.getenv('IOT_CRAWLER_SCREENSHOTS', 'false').lower() == 'true'
    )