"""
IoT Device Authentication Module
IoTデバイスの認証処理に特化したモジュール
"""

import time
from typing import Tuple, Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, 
    NoSuchFrameException, UnexpectedAlertPresentException
)

from .config import CrawlerConfig, CrawlerLogger

class IoTAuthenticator:
    """IoTデバイス認証クラス"""
    
    def __init__(self, driver: webdriver.Chrome, config: CrawlerConfig, logger: CrawlerLogger):
        self.driver = driver
        self.config = config
        self.logger = logger
        self.authenticated = False
        self.auth_data = {}
    
    def authenticate(self, url: str, username: str, password: str) -> bool:
        """メイン認証処理"""
        self.logger.info(f"Starting authentication for {url}")
        
        try:
            # ページロード
            self.driver.get(url)
            time.sleep(self.config.element_wait_timeout)
            
            # アラート処理
            self._handle_alerts()
            
            # 認証フォームの検出と実行
            if self._authenticate_main_page(username, password):
                self.authenticated = True
                self.logger.info("Authentication successful on main page")
                return True
            
            # フレーム内での認証試行
            if self._authenticate_in_frames(username, password):
                self.authenticated = True
                self.logger.info("Authentication successful in frames")
                return True
            
            self.logger.error("Authentication failed - no login form found")
            return False
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return False
    
    def _authenticate_main_page(self, username: str, password: str) -> bool:
        """メインページでの認証試行"""
        self.logger.debug("Trying authentication on main page")
        
        # デフォルトコンテンツに切り替え
        self.driver.switch_to.default_content()
        
        # ログイン要素の検出
        login_elements = self._find_login_elements()
        if not all(login_elements):
            self.logger.debug("Login elements not found on main page")
            return False
        
        username_field, password_field, submit_button = login_elements
        
        # 認証実行
        return self._perform_login(username_field, password_field, submit_button, username, password)
    
    def _authenticate_in_frames(self, username: str, password: str) -> bool:
        """フレーム内での認証試行"""
        self.logger.debug("Trying authentication in frames")
        
        # 優先フレームでの試行
        for frame_name in self.config.common_frame_names:
            if self._try_frame_authentication(frame_name, username, password):
                return True
        
        # 全フレームでの試行
        try:
            self.driver.switch_to.default_content()
            frames = self.driver.find_elements(By.TAG_NAME, 'frame')
            frames.extend(self.driver.find_elements(By.TAG_NAME, 'iframe'))
            
            for i, frame in enumerate(frames):
                frame_name = frame.get_attribute('name') or f'frame_{i}'
                if frame_name not in self.config.common_frame_names:
                    if self._try_frame_authentication(frame_name, username, password):
                        return True
        except Exception as e:
            self.logger.debug(f"Error enumerating frames: {str(e)}")
        
        return False
    
    def _try_frame_authentication(self, frame_name: str, username: str, password: str) -> bool:
        """指定フレームでの認証試行"""
        try:
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(frame_name)
            self.logger.debug(f"Switched to frame: {frame_name}")
            
            # ログイン要素の検出
            login_elements = self._find_login_elements()
            if not all(login_elements):
                return False
            
            username_field, password_field, submit_button = login_elements
            
            # 認証実行
            success = self._perform_login(username_field, password_field, submit_button, username, password)
            if success:
                self.auth_data['frame'] = frame_name
            
            return success
            
        except NoSuchFrameException:
            self.logger.debug(f"Frame not found: {frame_name}")
            return False
        except Exception as e:
            self.logger.debug(f"Error in frame {frame_name}: {str(e)}")
            return False
        finally:
            self.driver.switch_to.default_content()
    
    def _find_login_elements(self) -> Tuple[Optional[Any], Optional[Any], Optional[Any]]:
        """ログイン要素の検出"""
        username_field = None
        password_field = None
        submit_button = None
        
        # ユーザー名フィールド検索
        for selector in self.config.common_login_selectors['username']:
            try:
                if selector.startswith('input['):
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                else:
                    element = self._find_by_multiple_methods(selector)
                
                if element and element.is_displayed():
                    username_field = element
                    self.logger.debug(f"Found username field: {selector}")
                    break
            except NoSuchElementException:
                continue
        
        # パスワードフィールド検索
        for selector in self.config.common_login_selectors['password']:
            try:
                if selector.startswith('input['):
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                else:
                    element = self._find_by_multiple_methods(selector)
                
                if element and element.is_displayed():
                    password_field = element
                    self.logger.debug(f"Found password field: {selector}")
                    break
            except NoSuchElementException:
                continue
        
        # サブミットボタン検索
        for selector in self.config.common_login_selectors['submit']:
            try:
                if selector.startswith(('input[', 'button[')):
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                elif selector.startswith('button:contains'):
                    # XPath変換
                    text = selector.split('"')[1]
                    element = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                else:
                    element = self._find_by_multiple_methods(selector)
                
                if element and element.is_displayed():
                    submit_button = element
                    self.logger.debug(f"Found submit button: {selector}")
                    break
            except NoSuchElementException:
                continue
        
        return username_field, password_field, submit_button
    
    def _find_by_multiple_methods(self, selector: str):
        """複数の方法で要素を検索"""
        methods = [
            (By.ID, selector),
            (By.NAME, selector),
            (By.CSS_SELECTOR, selector),
            (By.XPATH, f"//*[@id='{selector}']"),
            (By.XPATH, f"//*[@name='{selector}']")
        ]
        
        for by, value in methods:
            try:
                return self.driver.find_element(by, value)
            except NoSuchElementException:
                continue
        
        return None
    
    def _perform_login(self, username_field, password_field, submit_button, username: str, password: str) -> bool:
        """ログイン実行"""
        try:
            # オーバーレイ削除
            self._remove_overlays()
            
            # 認証情報入力
            self.logger.debug(f"Entering credentials")
            username_field.clear()
            username_field.send_keys(username)
            
            password_field.clear()
            password_field.send_keys(password)
            
            # サブミット
            self.logger.debug("Clicking submit button")
            submit_button.click()
            
            # アラート処理
            self._handle_alerts()
            
            # 認証結果確認
            time.sleep(self.config.element_wait_timeout)
            return self._verify_authentication_success()
            
        except Exception as e:
            self.logger.debug(f"Login execution error: {str(e)}")
            return False
    
    def _remove_overlays(self):
        """オーバーレイ要素の削除"""
        overlay_selectors = [
            "modal_overlay", "overlay", "popup", "modal", "loading",
            "dialog", "lightbox", "backdrop", "mask"
        ]
        
        for overlay_id in overlay_selectors:
            try:
                self.driver.execute_script(f"""
                    var overlay = document.getElementById('{overlay_id}');
                    if (overlay) {{
                        overlay.style.display = 'none';
                        overlay.remove();
                    }}
                """)
            except Exception:
                continue
        
        # クラスベースのオーバーレイ削除
        try:
            self.driver.execute_script("""
                var overlays = document.querySelectorAll('.modal, .overlay, .popup, .backdrop');
                overlays.forEach(function(overlay) {
                    overlay.style.display = 'none';
                });
            """)
        except Exception:
            pass
    
    def _handle_alerts(self):
        """アラート処理"""
        try:
            WebDriverWait(self.driver, 1).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            self.logger.debug(f"Alert detected: {alert_text}")
            
            # セッション重複の場合は承諾
            if any(word in alert_text.lower() for word in ['session', 'active', 'terminate']):
                self.logger.info("Accepting session termination alert")
                alert.accept()
            else:
                self.logger.info("Dismissing alert")
                alert.dismiss()
                
        except TimeoutException:
            pass
        except Exception as e:
            self.logger.debug(f"Alert handling error: {str(e)}")
    
    def _verify_authentication_success(self) -> bool:
        """認証成功の確認"""
        success_indicators = [
            # 汎用的な成功指標
            (By.LINK_TEXT, "Logout"), (By.LINK_TEXT, "ログアウト"),
            (By.ID, "logout"), (By.CLASS_NAME, "logout"),
            (By.XPATH, "//a[contains(text(), 'Logout')]"),
            (By.XPATH, "//a[contains(text(), 'ログアウト')]"),
            
            # ダッシュボード・管理画面
            (By.ID, "dashboard"), (By.CLASS_NAME, "dashboard"),
            (By.XPATH, "//h1[contains(text(), 'Dashboard')]"),
            (By.XPATH, "//span[contains(text(), 'Admin')]"),
            
            # ユーザー情報
            (By.ID, "user-info"), (By.CLASS_NAME, "user-info"),
            (By.ID, "username-display")
        ]
        
        failure_indicators = [
            (By.XPATH, "//div[contains(text(), 'Invalid')]"),
            (By.XPATH, "//div[contains(text(), 'Error')]"),
            (By.XPATH, "//div[contains(text(), '無効')]"),
            (By.CLASS_NAME, "error"), (By.ID, "error")
        ]
        
        # 失敗指標の確認
        for by, selector in failure_indicators:
            try:
                element = self.driver.find_element(by, selector)
                if element.is_displayed():
                    self.logger.debug(f"Found failure indicator: {selector}")
                    return False
            except NoSuchElementException:
                continue
        
        # メインページでの成功指標確認
        self.driver.switch_to.default_content()
        for by, selector in success_indicators:
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((by, selector))
                )
                if element.is_displayed():
                    self.logger.debug(f"Found success indicator: {selector}")
                    return True
            except TimeoutException:
                continue
        
        # フレーム内での成功指標確認
        if self._check_success_in_frames(success_indicators):
            return True
        
        # IoTデバイス固有の確認方法
        return self._verify_iot_specific_success()
    
    def _check_success_in_frames(self, success_indicators) -> bool:
        """フレーム内での成功確認"""
        try:
            frames = self.driver.find_elements(By.TAG_NAME, 'frame')
            frames.extend(self.driver.find_elements(By.TAG_NAME, 'iframe'))
            
            for i, frame in enumerate(frames):
                try:
                    frame_name = frame.get_attribute('name') or f'frame_{i}'
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame(frame_name)
                    
                    for by, selector in success_indicators:
                        try:
                            element = WebDriverWait(self.driver, 1).until(
                                EC.presence_of_element_located((by, selector))
                            )
                            if element.is_displayed():
                                self.logger.debug(f"Found success indicator in frame {frame_name}: {selector}")
                                return True
                        except TimeoutException:
                            continue
                            
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Error checking frames for success: {str(e)}")
        
        finally:
            self.driver.switch_to.default_content()
        
        return False
    
    def _verify_iot_specific_success(self) -> bool:
        """IoTデバイス固有の成功確認"""
        # URL変化の確認
        current_url = self.driver.current_url
        if any(keyword in current_url.lower() for keyword in ['dashboard', 'admin', 'home', 'main']):
            self.logger.debug(f"Success detected by URL change: {current_url}")
            return True
        
        # タイトル変化の確認
        title = self.driver.title.lower()
        if any(keyword in title for keyword in ['dashboard', 'admin', 'home', 'main']):
            self.logger.debug(f"Success detected by title change: {self.driver.title}")
            return True
        
        # Netgear固有の確認
        if self._verify_netgear_success():
            return True
        
        self.logger.debug("Could not verify authentication success")
        return False
    
    def _verify_netgear_success(self) -> bool:
        """Netgear固有の成功確認"""
        try:
            # masterフレーム内のユーザー名フィールドが消失
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame("master")
            WebDriverWait(self.driver, 2).until(
                EC.invisibility_of_element_located((By.ID, "username"))
            )
            self.logger.debug("Success detected: username field disappeared in master frame")
            return True
        except (TimeoutException, NoSuchFrameException):
            pass
        
        try:
            # headerフレーム内のログアウト要素
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame("header")
            WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.ID, "logout"))
            )
            self.logger.debug("Success detected: logout element in header frame")
            return True
        except (TimeoutException, NoSuchFrameException):
            pass
        
        finally:
            self.driver.switch_to.default_content()
        
        return False
    
    def get_auth_data(self) -> Dict[str, Any]:
        """認証データの取得"""
        return {
            'authenticated': self.authenticated,
            'auth_method': self.auth_data.get('method', 'form'),
            'auth_frame': self.auth_data.get('frame'),
            'timestamp': time.time()
        }