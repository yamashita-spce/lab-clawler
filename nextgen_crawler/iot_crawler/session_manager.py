"""
IoT Device Session Management Module
セッション状態の保存・復元とFuzzing再現性の確保
"""

import json
import pickle
import time
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.common.by import By

from .config import CrawlerConfig, CrawlerLogger

@dataclass
class SessionState:
    """セッション状態データクラス"""
    target_url: str
    username: str
    authenticated: bool
    auth_frame: Optional[str]
    cookies: List[Dict[str, Any]]
    local_storage: Dict[str, str]
    session_storage: Dict[str, str]
    current_url: str
    page_title: str
    timestamp: float
    browser_state: Optional[bytes] = None  # pickled browser state

@dataclass
class CrawlSession:
    """クロールセッションデータクラス"""
    session_id: str
    config: Dict[str, Any]
    auth_state: SessionState
    visited_urls: List[str]
    crawl_path: List[Dict[str, Any]]  # URL, timestamp, actionの履歴
    final_state: Dict[str, Any]
    created_at: float
    completed_at: Optional[float] = None

class IoTSessionManager:
    """IoTデバイス用セッション管理クラス"""
    
    def __init__(self, driver: webdriver.Chrome, config: CrawlerConfig, logger: CrawlerLogger):
        self.driver = driver
        self.config = config
        self.logger = logger
        self.current_session: Optional[CrawlSession] = None
        self.session_file = os.path.join(config.output_dir, config.session_file)
        
    def create_session(self, session_id: str) -> CrawlSession:
        """新しいクロールセッションの作成"""
        self.logger.info(f"Creating new crawl session: {session_id}")
        
        self.current_session = CrawlSession(
            session_id=session_id,
            config=self._serialize_config(),
            auth_state=None,  # 認証後に設定
            visited_urls=[],
            crawl_path=[],
            final_state={},
            created_at=time.time()
        )
        
        return self.current_session
    
    def capture_auth_state(self, target_url: str, username: str, authenticated: bool, 
                          auth_frame: Optional[str] = None) -> SessionState:
        """認証状態のキャプチャ"""
        self.logger.debug("Capturing authentication state")
        
        try:
            # Cookie取得
            cookies = self.driver.get_cookies()
            
            # ローカルストレージ取得
            local_storage = {}
            try:
                local_storage = self.driver.execute_script("""
                    var storage = {};
                    for (var i = 0; i < localStorage.length; i++) {
                        var key = localStorage.key(i);
                        storage[key] = localStorage.getItem(key);
                    }
                    return storage;
                """)
            except Exception as e:
                self.logger.debug(f"Could not access localStorage: {str(e)}")
            
            # セッションストレージ取得
            session_storage = {}
            try:
                session_storage = self.driver.execute_script("""
                    var storage = {};
                    for (var i = 0; i < sessionStorage.length; i++) {
                        var key = sessionStorage.key(i);
                        storage[key] = sessionStorage.getItem(key);
                    }
                    return storage;
                """)
            except Exception as e:
                self.logger.debug(f"Could not access sessionStorage: {str(e)}")
            
            # 現在の状態
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            auth_state = SessionState(
                target_url=target_url,
                username=username,
                authenticated=authenticated,
                auth_frame=auth_frame,
                cookies=cookies,
                local_storage=local_storage or {},
                session_storage=session_storage or {},
                current_url=current_url,
                page_title=page_title,
                timestamp=time.time()
            )
            
            # 現在のセッションに認証状態を設定
            if self.current_session:
                self.current_session.auth_state = auth_state
            
            self.logger.info("Authentication state captured successfully")
            return auth_state
            
        except Exception as e:
            self.logger.error(f"Error capturing auth state: {str(e)}")
            raise
    
    def restore_auth_state(self, auth_state: SessionState) -> bool:
        """認証状態の復元"""
        self.logger.info("Restoring authentication state")
        
        try:
            # ターゲットURLにアクセス
            self.driver.get(auth_state.target_url)
            time.sleep(self.config.element_wait_timeout)
            
            # Cookie復元
            self.driver.delete_all_cookies()
            for cookie in auth_state.cookies:
                try:
                    # domain と path が正しく設定されているかチェック
                    cookie_to_add = {k: v for k, v in cookie.items() 
                                   if k in ['name', 'value', 'domain', 'path', 'secure', 'httpOnly']}
                    self.driver.add_cookie(cookie_to_add)
                except Exception as e:
                    self.logger.debug(f"Could not restore cookie {cookie.get('name')}: {str(e)}")
            
            # ページリロード（Cookie適用のため）
            self.driver.refresh()
            time.sleep(self.config.element_wait_timeout)
            
            # ローカルストレージ復元
            if auth_state.local_storage:
                try:
                    for key, value in auth_state.local_storage.items():
                        self.driver.execute_script(f"localStorage.setItem('{key}', '{value}');")
                except Exception as e:
                    self.logger.debug(f"Could not restore localStorage: {str(e)}")
            
            # セッションストレージ復元
            if auth_state.session_storage:
                try:
                    for key, value in auth_state.session_storage.items():
                        self.driver.execute_script(f"sessionStorage.setItem('{key}', '{value}');")
                except Exception as e:
                    self.logger.debug(f"Could not restore sessionStorage: {str(e)}")
            
            # 認証状態確認
            if self._verify_restored_auth_state(auth_state):
                self.logger.info("Authentication state restored successfully")
                return True
            else:
                self.logger.warning("Authentication state restoration may have failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restoring auth state: {str(e)}")
            return False
    
    def _verify_restored_auth_state(self, auth_state: SessionState) -> bool:
        """復元された認証状態の確認"""
        try:
            # 基本的な状態確認
            current_cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
            expected_cookies = {cookie['name']: cookie['value'] for cookie in auth_state.cookies}
            
            # 主要なCookieが存在するかチェック
            auth_cookies = ['PHPSESSID', 'session', 'auth', 'token']
            has_auth_cookie = any(cookie_name in current_cookies for cookie_name in auth_cookies)
            
            if has_auth_cookie:
                return True
            
            # IoTデバイス固有の確認方法
            return self._verify_iot_auth_state(auth_state)
            
        except Exception as e:
            self.logger.debug(f"Auth state verification error: {str(e)}")
            return False
    
    def _verify_iot_auth_state(self, auth_state: SessionState) -> bool:
        """IoTデバイス固有の認証状態確認"""
        try:
            # フレーム内の認証状態確認
            if auth_state.auth_frame:
                try:
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame(auth_state.auth_frame)
                    
                    # ログインフォームが存在しないことを確認
                    login_elements = self.driver.find_elements(By.ID, "username")
                    if not login_elements:
                        return True
                        
                except Exception:
                    pass
                finally:
                    self.driver.switch_to.default_content()
            
            # ログアウト要素の存在確認
            logout_selectors = [
                (By.ID, "logout"), (By.LINK_TEXT, "Logout"),
                (By.XPATH, "//a[contains(text(), 'Logout')]")
            ]
            
            for by, selector in logout_selectors:
                try:
                    elements = self.driver.find_elements(by, selector)
                    if elements and any(elem.is_displayed() for elem in elements):
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def record_crawl_action(self, action_type: str, url: str, details: Dict[str, Any] = None):
        """クロールアクションの記録"""
        if not self.current_session:
            return
        
        action_record = {
            'action_type': action_type,  # 'navigate', 'click', 'form_submit', 'frame_switch'
            'url': url,
            'timestamp': time.time(),
            'details': details or {}
        }
        
        self.current_session.crawl_path.append(action_record)
        self.logger.debug(f"Recorded action: {action_type} on {url}")
    
    def add_visited_url(self, url: str):
        """訪問済みURLの追加"""
        if self.current_session and url not in self.current_session.visited_urls:
            self.current_session.visited_urls.append(url)
    
    def save_session(self, final_state: Dict[str, Any] = None) -> bool:
        """セッション状態の保存"""
        if not self.current_session:
            self.logger.error("No active session to save")
            return False
        
        try:
            # 最終状態の設定
            if final_state:
                self.current_session.final_state = final_state
            
            self.current_session.completed_at = time.time()
            
            # セッションデータの準備
            session_data = {
                'session': asdict(self.current_session),
                'metadata': {
                    'crawler_version': '1.0',
                    'save_timestamp': time.time(),
                    'driver_info': {
                        'name': 'chrome',
                        'version': self._get_browser_version()
                    }
                }
            }
            
            # ファイル保存
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Session saved to: {self.session_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving session: {str(e)}")
            return False
    
    def load_session(self, session_file: str = None) -> Optional[CrawlSession]:
        """セッション状態の読み込み"""
        session_file = session_file or self.session_file
        
        try:
            if not os.path.exists(session_file):
                self.logger.warning(f"Session file not found: {session_file}")
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # セッションオブジェクトの再構築
            session_dict = session_data['session']
            
            # SessionStateの再構築
            if session_dict.get('auth_state'):
                auth_state_dict = session_dict['auth_state']
                auth_state = SessionState(**auth_state_dict)
                session_dict['auth_state'] = auth_state
            
            session = CrawlSession(**session_dict)
            
            self.logger.info(f"Session loaded from: {session_file}")
            return session
            
        except Exception as e:
            self.logger.error(f"Error loading session: {str(e)}")
            return None
    
    def replay_session(self, session: CrawlSession) -> bool:
        """セッションの再現"""
        self.logger.info(f"Replaying session: {session.session_id}")
        
        try:
            # 認証状態の復元
            if session.auth_state:
                if not self.restore_auth_state(session.auth_state):
                    self.logger.error("Failed to restore authentication state")
                    return False
            
            # クロールパスの再現
            for action in session.crawl_path:
                try:
                    self._replay_action(action)
                    time.sleep(self.config.element_wait_timeout)
                except Exception as e:
                    self.logger.warning(f"Could not replay action {action['action_type']}: {str(e)}")
                    continue
            
            self.logger.info("Session replay completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error replaying session: {str(e)}")
            return False
    
    def _replay_action(self, action: Dict[str, Any]):
        """個別アクションの再現"""
        action_type = action['action_type']
        url = action['url']
        details = action.get('details', {})
        
        if action_type == 'navigate':
            self.driver.get(url)
        elif action_type == 'frame_switch':
            frame_name = details.get('frame_name')
            if frame_name:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(frame_name)
        elif action_type == 'click':
            # クリック要素の特定と実行（簡略化）
            selector = details.get('selector')
            if selector:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    element.click()
                except Exception:
                    pass
        # 他のアクションタイプも必要に応じて追加
    
    def _serialize_config(self) -> Dict[str, Any]:
        """設定のシリアライズ"""
        return {
            'target_url': self.config.target_url,
            'username': self.config.username,
            'page_load_timeout': self.config.page_load_timeout,
            'element_wait_timeout': self.config.element_wait_timeout,
            'frame_wait_timeout': self.config.frame_wait_timeout,
            'max_depth': self.config.max_depth,
            'crawl_frames': self.config.crawl_frames,
            'extract_forms': self.config.extract_forms,
            'extract_links': self.config.extract_links
        }
    
    def _get_browser_version(self) -> str:
        """ブラウザバージョンの取得"""
        try:
            return self.driver.capabilities.get('browserVersion', 'unknown')
        except Exception:
            return 'unknown'
    
    def create_reproducible_snapshot(self) -> Dict[str, Any]:
        """再現可能なスナップショットの作成"""
        """Fuzzing用の完全な状態スナップショット"""
        if not self.current_session:
            return {}
        
        try:
            snapshot = {
                'session_id': self.current_session.session_id,
                'timestamp': time.time(),
                'auth_state': asdict(self.current_session.auth_state) if self.current_session.auth_state else None,
                'current_url': self.driver.current_url,
                'page_source': self.driver.page_source,
                'cookies': self.driver.get_cookies(),
                'window_size': self.driver.get_window_size(),
                'crawl_path': self.current_session.crawl_path.copy(),
                'visited_urls': self.current_session.visited_urls.copy(),
                'browser_logs': self._get_browser_logs()
            }
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Error creating snapshot: {str(e)}")
            return {}
    
    def _get_browser_logs(self) -> List[Dict[str, Any]]:
        """ブラウザログの取得"""
        try:
            logs = self.driver.get_log('browser')
            return logs
        except Exception:
            return []