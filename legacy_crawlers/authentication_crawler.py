import os
import time
import argparse
from urllib.parse import urlparse, urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchFrameException, TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait # 明示的な待機のためインポート
from selenium.webdriver.support import expected_conditions as EC # 期待する条件のためインポート

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def sanitize_filename(url: str) -> str:
    """
    URLからファイル名として安全な文字列を生成する
    """
    p = urlparse(url)
    name = p.netloc + p.path
    # ファイル名に使えない文字をアンダ
    # ースコアに置換
    return name.strip('/').replace('/', '_').replace(':', '_').replace('?', '_').replace('=', '_').replace('&', '_')

def wait_for_frame_src(driver, frame_element, max_wait_time=10):
    """
    フレーム要素のsrc属性が設定されるまで待機
    """
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        # src属性を取得
        src = frame_element.get_attribute("src")

        # srcが存在し、空でない場合
        if src and src.strip():
            print(f"Frame src detected: {src}")
            return src

        print("Frame src not ready, waiting 1 second...")
        time.sleep(1)

        # フレーム要素を再取得（DOM更新対応）
        try:
            frame_name = frame_element.get_attribute("name")
            if frame_name:
                # デフォルトコンテンツに戻ってから要素を再取得
                driver.switch_to.default_content()
                frame_element = driver.find_element(By.NAME, frame_name)
        except:
            pass

    print(f"Frame src not set within {max_wait_time} seconds")
    return None


class AuthenticationCrawler:
    def __init__(self, base_url: str, output_dir: str = "crawl_output", wait_time: int = 10): # 待機時間を10秒に変更
        self.base_url = base_url
        self.output_dir = output_dir
        self.wait_time = wait_time
        self.driver = None

        ensure_dir(os.path.join(self.output_dir, "auth_html"))

        # Selenium WebDriverの初期化
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        # 必要に応じてプロキシ設定などを追加
        # chrome_options.add_argument(f'--proxy-server=http://127.0.0.1:{proxy_port}')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(60) # ページロードのタイムアウト
        except WebDriverException as e:
            print(f"Error initializing WebDriver: {e}")
            self.driver = None # 初期化失敗時はNoneとする

    def __del__(self):
        """
        オブジェクト破棄時にWebDriverを終了する
        """
        if self.driver:
            self.driver.quit()

    def fetch_and_save_frames(self, url: str):
        """
        指定されたURLのページと、そのフレームセット内のフレームのHTMLを取得・保存する
        """
        if not self.driver:
            print("WebDriver is not initialized. Cannot fetch frames.")
            return

        print(f"Fetching page and frames for: {url}")
        try:
            self.driver.get(url)
            time.sleep(self.wait_time) # JavaScript実行待機

            # メインページのHTMLを保存
            main_html = self.driver.page_source
            main_filename = sanitize_filename(url) + "_main.html"
            main_filepath = os.path.join(self.output_dir, "auth_html", main_filename)
            with open(main_filepath, "w", encoding="utf-8") as f:
                f.write(main_html)
            print(f"Saved main page HTML to {main_filepath}")

            print(f"Saved main page HTML to {main_filepath}")

            # フレームセット内のフレームを処理
            # フレーム要素のリストをループ内で毎回取得することで、DOMの変化に対応
            print(f"[+] Processing frames")

            # フレームの数を事前に取得（これは目安であり、ループ内で再取得する）
            initial_frames = self.driver.find_elements(By.TAG_NAME, 'frame') + self.driver.find_elements(By.TAG_NAME, 'iframe')
            initial_frames_count = len(initial_frames)
            print(f"  - Initial frame count: {initial_frames_count}")


            # フレーム要素のリストをループ内で毎回取得することで、DOMの変化に対応
            print(f"[+] Processing frames")

            # フレームの数を事前に取得（これは目安であり、ループ内で再取得する）
            initial_frames = self.driver.find_elements(By.TAG_NAME, 'frame') + self.driver.find_elements(By.TAG_NAME, 'iframe')
            initial_frames_count = len(initial_frames)
            print(f"  - Initial frame count: {initial_frames_count}")

            for index in range(initial_frames_count):
                self.driver.switch_to.default_content() # デフォルトコンテンツに戻る
                try:
                    # フレームに切り替える直前にフレーム要素を再取得
                    current_frames = self.driver.find_elements(By.TAG_NAME, 'frame') + self.driver.find_elements(By.TAG_NAME, 'iframe')
                    if index >= len(current_frames):
                        print(f"  - Frame at index {index} no longer exists, skipping.")
                        continue # フレームが存在しない場合はスキップ

                    # フレーム要素を取得
                    frame_element = current_frames[index]
                    frame_name = frame_element.get_attribute("name") # name属性を取得

                    print(f"  - Processing frame at index {index} (name: {frame_name if frame_name else 'N/A'})")

                    # フレームのsrc属性が設定されるまで待機
                    frame_src = wait_for_frame_src(self.driver, frame_element, max_wait_time=self.wait_time)

                    if frame_src:
                        frame_url = urljoin(url, frame_src) # 絶対URLに変換
                        print(f"  - Frame src confirmed: {frame_url}")

                        # src属性を使用してフレームに切り替え
                        # src属性による切り替えはSeleniumの標準機能ではないため、
                        # name属性または要素自体を使用して切り替える
                        if frame_name:
                            self.driver.switch_to.frame(frame_name)
                            print(f"  - Switched to frame by name: {frame_name}")
                        else:
                            # name属性がない場合は要素自体を使用して試す
                            self.driver.switch_to.frame(frame_element)
                            print(f"  - Switched to frame by element at index: {index}")

                        # フレーム内の要素がロードされるまで待機 (より具体的な要素を待つ)
                        WebDriverWait(self.driver, self.wait_time).until(
                            EC.presence_of_element_located((By.TAG_NAME, "html")) # htmlタグが出現するまで待機
                        )
                        print(f"  - Waited for frame content to load.")

                        frame_html = self.driver.page_source

                        # フレームのHTMLを保存 (ユニークなファイル名を使用)
                        frame_filename = sanitize_filename(frame_url) + f"_frame_{index}.html" # インデックスをファイル名に追加
                        frame_filepath = os.path.join(self.output_dir, "auth_html", frame_filename)
                        with open(frame_filepath, "w", encoding="utf-8") as f:
                            f.write(frame_html)
                        print(f"  - Saved frame HTML to {frame_filepath}")
                    else:
                        print(f"  - Frame src not available for frame at index {index} within timeout, skipping.")

                except NoSuchFrameException:
                    print(f"  - Could not switch to frame at index {index}")
                except WebDriverException as e:
                    print(f"  - WebDriver error in frame at index {index}: {e}")
                except Exception as e:
                    print(f"  - An error occurred in frame at index {index}: {e}")
                finally:
                    self.driver.switch_to.default_content() # 必ずデフォルトコンテンツに戻る

        except TimeoutException:
            print(f"Page load timed out for {url}")
        except WebDriverException as e:
            print(f"WebDriver error during fetching {url}: {e}")
        except Exception as e:
            print(f"An error occurred during fetching {url}: {e}")

    def find_login_elements(self):
        """
        ログインフォーム要素を自動検出する
        """
        username_selectors = [
            (By.ID, "username"), (By.ID, "user"), (By.ID, "login"), (By.ID, "userid"),
            (By.NAME, "username"), (By.NAME, "user"), (By.NAME, "login"), (By.NAME, "userid"),
            (By.XPATH, "//input[@type='text']"), (By.XPATH, "//input[@type='email']")
        ]
        
        password_selectors = [
            (By.ID, "password"), (By.ID, "passwd"), (By.ID, "pass"), (By.ID, "pwd"),
            (By.NAME, "password"), (By.NAME, "passwd"), (By.NAME, "pass"), (By.NAME, "pwd"),
            (By.XPATH, "//input[@type='password']")
        ]
        
        button_selectors = [
            (By.XPATH, "//input[@type='submit']"), (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//input[@type='image']"), (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.XPATH, "//button[contains(text(), 'ログイン')]"), (By.XPATH, "//input[@value='Login']"),
            (By.XPATH, "//input[@value='ログイン']"), (By.ID, "login"), (By.ID, "submit")
        ]
        
        username_field = None
        password_field = None
        login_button = None
        
        # ユーザー名フィールドを検索
        for selector in username_selectors:
            try:
                username_field = self.driver.find_element(*selector)
                if username_field.is_displayed():
                    print(f"Found username field using: {selector}")
                    break
                else:
                    username_field = None
            except NoSuchElementException:
                continue
        
        # パスワードフィールドを検索
        for selector in password_selectors:
            try:
                password_field = self.driver.find_element(*selector)
                if password_field.is_displayed():
                    print(f"Found password field using: {selector}")
                    break
                else:
                    password_field = None
            except NoSuchElementException:
                continue
        
        # ログインボタンを検索
        for selector in button_selectors:
            try:
                login_button = self.driver.find_element(*selector)
                if login_button.is_displayed():
                    print(f"Found login button using: {selector}")
                    break
                else:
                    login_button = None
            except NoSuchElementException:
                continue
        
        return username_field, password_field, login_button

    def try_login_in_frame(self, frame_name, username, password):
        """
        指定されたフレーム内でログインを試行する
        """
        try:
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(frame_name)
            print(f"Switched to '{frame_name}' frame.")
            
            # ログイン要素を検索
            username_field, password_field, login_button = self.find_login_elements()
            
            if username_field and password_field and login_button:
                # オーバーレイを削除する汎用処理
                self.remove_overlays()
                
                # 認証情報を入力
                print(f"Entering username: {username}")
                username_field.clear()
                username_field.send_keys(username)
                
                print("Entering password: ********")
                password_field.clear()
                password_field.send_keys(password)
                
                # ログインボタンをクリック
                print("Clicking login button.")
                login_button.click()
                
                # アラート処理
                self.handle_alerts()
                
                time.sleep(self.wait_time)
                return True
            else:
                print(f"Could not find all login elements in '{frame_name}' frame.")
                return False
                
        except NoSuchFrameException:
            print(f"Could not switch to '{frame_name}' frame.")
            return False
        except Exception as e:
            print(f"Error in frame '{frame_name}': {e}")
            return False

    def handle_alerts(self):
        """
        アラートダイアログを処理する
        """
        try:
            # アラートが存在するか確認
            WebDriverWait(self.driver, 3).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            print(f"Alert detected: {alert_text}")
            
            # セッション重複の場合は承諾
            if "session" in alert_text.lower() or "active" in alert_text.lower():
                print("Accepting session termination alert.")
                alert.accept()
            else:
                print("Dismissing alert.")
                alert.dismiss()
                
        except TimeoutException:
            # アラートが存在しない場合は何もしない
            pass
        except Exception as e:
            print(f"Error handling alert: {e}")

    def remove_overlays(self):
        """
        一般的なモーダルオーバーレイを削除する
        """
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
                        overlay.parentNode.removeChild(overlay);
                        console.log('{overlay_id} overlay removed.');
                    }}
                """)
            except Exception:
                continue
        
        # クラス名ベースでも削除を試行
        try:
            self.driver.execute_script("""
                var overlays = document.querySelectorAll('.modal, .overlay, .popup, .backdrop');
                for (var i = 0; i < overlays.length; i++) {
                    overlays[i].style.display = 'none';
                }
            """)
        except Exception:
            pass

    def authenticate(self, login_url: str, username: str, password: str):
        """
        汎用的な認証処理
        """
        if not self.driver:
            print("WebDriver is not initialized. Cannot authenticate.")
            return False

        print(f"Attempting authentication for {login_url} with username '{username}' and password '********'")
        try:
            self.driver.get(login_url)
            time.sleep(self.wait_time)
            
            # 1. メインページでログイン要素を検索
            self.driver.switch_to.default_content()
            username_field, password_field, login_button = self.find_login_elements()
            
            if username_field and password_field and login_button:
                print("Found login elements on main page.")
                self.remove_overlays()
                
                # 認証情報を入力
                print(f"Entering username: {username}")
                username_field.clear()
                username_field.send_keys(username)
                
                print("Entering password: ********")
                password_field.clear()
                password_field.send_keys(password)
                
                # ボタンをクリック
                print("Clicking login button.")
                login_button.click()
                
                # アラート処理
                self.handle_alerts()
                
                time.sleep(self.wait_time * 2)
                return self.verify_login_success()
            
            # 2. フレーム内でログイン要素を検索
            frames = self.driver.find_elements(By.TAG_NAME, 'frame') + self.driver.find_elements(By.TAG_NAME, 'iframe')
            
            # よくあるフレーム名を優先的に試行
            priority_frames = ['master', 'main', 'content', 'login', 'auth']
            
            for frame_name in priority_frames:
                if self.try_login_in_frame(frame_name, username, password):
                    return self.verify_login_success()
            
            # 全フレームを順次試行
            for i, frame in enumerate(frames):
                frame_name = frame.get_attribute('name') or f'frame_{i}'
                if frame_name not in priority_frames:
                    if self.try_login_in_frame(frame_name, username, password):
                        return self.verify_login_success()
            
            print("Could not find login elements in any frame.")
            return False

        except Exception as e:
            print(f"An error occurred during authentication: {e}")
            return False
    
    def verify_login_success(self):
        """
        ログイン成功を汎用的に確認する
        """
        success_indicators = [
            # ログアウト関連
            (By.LINK_TEXT, "Logout"), (By.LINK_TEXT, "ログアウト"), (By.ID, "logout"),
            (By.XPATH, "//a[contains(text(), 'Logout')]"), (By.XPATH, "//a[contains(text(), 'ログアウト')]"),
            # ダッシュボード関連
            (By.ID, "dashboard"), (By.CLASS_NAME, "dashboard"),
            (By.XPATH, "//h1[contains(text(), 'Dashboard')]"), (By.XPATH, "//h1[contains(text(), 'ダッシュボード')]"),
            # 管理画面関連
            (By.XPATH, "//span[contains(text(), 'Admin')]"), (By.XPATH, "//span[contains(text(), '管理')]"),
            # ユーザー情報関連
            (By.ID, "user-info"), (By.CLASS_NAME, "user-info"), (By.ID, "username-display")
        ]
        
        failure_indicators = [
            # エラーメッセージ
            (By.XPATH, "//div[contains(text(), 'Invalid')]"), (By.XPATH, "//div[contains(text(), 'Error')]"),
            (By.XPATH, "//div[contains(text(), '無効')]"), (By.XPATH, "//div[contains(text(), 'エラー')]"),
            (By.CLASS_NAME, "error"), (By.ID, "error"), (By.CLASS_NAME, "alert-danger")
        ]
        
        # 失敗の兆候をチェック
        for selector in failure_indicators:
            try:
                if self.driver.find_element(*selector).is_displayed():
                    print(f"Login failed: Found failure indicator {selector}")
                    return False
            except NoSuchElementException:
                continue
        
        # メインページで成功の兆候をチェック
        self.driver.switch_to.default_content()
        for selector in success_indicators:
            try:
                element = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located(selector)
                )
                if element.is_displayed():
                    print(f"Login successful: Found success indicator {selector}")
                    return True
            except TimeoutException:
                continue
        
        # フレーム内で成功の兆候をチェック
        frames = self.driver.find_elements(By.TAG_NAME, 'frame') + self.driver.find_elements(By.TAG_NAME, 'iframe')
        for i, frame in enumerate(frames):
            try:
                frame_name = frame.get_attribute('name') or f'frame_{i}'
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(frame_name)
                
                for selector in success_indicators:
                    try:
                        element = WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located(selector)
                        )
                        if element.is_displayed():
                            print(f"Login successful: Found success indicator {selector} in frame {frame_name}")
                            self.driver.switch_to.default_content()
                            return True
                    except TimeoutException:
                        continue
                        
            except Exception:
                continue
        
        self.driver.switch_to.default_content()
        
        # URL変化をチェック
        current_url = self.driver.current_url
        if any(keyword in current_url.lower() for keyword in ['dashboard', 'admin', 'home', 'main']):
            print(f"Login successful: URL changed to {current_url}")
            return True
        
        # ページタイトル変化をチェック
        title = self.driver.title.lower()
        if any(keyword in title for keyword in ['dashboard', 'admin', 'home', 'main', 'ダッシュボード', '管理']):
            print(f"Login successful: Page title changed to {self.driver.title}")
            return True
        
        # Netgear固有の成功確認（従来ロジック）
        try:
            # 条件1: masterフレーム内のユーザー名フィールドが非表示になるか削除される
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame("master")
            WebDriverWait(self.driver, 3).until(
                EC.invisibility_of_element_located((By.ID, "username"))
            )
            print("Login successful: Username field disappeared in master frame.")
            self.driver.switch_to.default_content()
            return True
        except (TimeoutException, NoSuchFrameException):
            pass
            
        try:
            # 条件2: headerフレーム内のログアウト要素が表示される
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame("header")
            WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.ID, "logout"))
            )
            print("Login successful: Logout element found in header frame.")
            self.driver.switch_to.default_content()
            return True
        except (TimeoutException, NoSuchFrameException):
            pass
        
        self.driver.switch_to.default_content()
        print("Could not confirm login success.")
        return False

    def run(self, url: str, username: str = "admin", password: str = "password"):
        """
        認証クローラーの実行フロー
        """
        print(f"Starting authentication crawl for {url}")
        self.fetch_and_save_frames(url)
        # 認証が必要な場合は authenticate メソッドを呼び出す
        # self.authenticate(url, username, password)
        print("Authentication crawl completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="認証ページおよびフレームセット内のフレームを取得するクローラー"
    )
    parser.add_argument('--url', help='対象の認証ページのURL', default="http://127.0.0.1:8888")
    parser.add_argument('-o', '--output', default='crawl_output',
                        help='結果保存ディレクトリ (デフォルト: crawl_output)')
    parser.add_argument('-w', '--wait', type=int, default=5,help='JavaScript実行待機秒数 (デフォルト: 5秒)')
    # 認証情報に関する引数を追加
    parser.add_argument('--login', action='store_true', help='認証処理を実行する', default=True)
    parser.add_argument('--username', default='admin', help='ログインユーザー名 (デフォルト: admin)')
    parser.add_argument('--password', default='password', help='ログインパスワード (デフォルト: password)')


    args = parser.parse_args()

    auth_crawler = AuthenticationCrawler(args.url, args.output, args.wait)

    if args.login:
        # 認証処理を実行
        auth_crawler.authenticate(args.url, args.username, args.password)
    else:
        # フレーム取得処理を実行
        auth_crawler.fetch_and_save_frames(args.url)

    print("Authentication crawl completed.")