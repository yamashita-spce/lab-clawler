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
    # ファイル名に使えない文字をアンダースコアに置換
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

    def authenticate(self, login_url: str, username: str, password: str):
        """
        認証処理のスケルトン
        """
        if not self.driver:
            print("WebDriver is not initialized. Cannot authenticate.")
            return False

        print(f"Attempting authentication for {login_url} with username '{username}' and password '********'")
        try:
            self.driver.get(login_url)
            time.sleep(self.wait_time) # ページロード待機

            # フレームセット内のmasterフレームに切り替え
            self.driver.switch_to.default_content() # デフォルトコンテンツに戻る
            try:
                self.driver.switch_to.frame("master")
                print("Switched to 'master' frame.")
            except NoSuchFrameException:
                print("Could not switch to 'master' frame. Authentication failed.")
                return False

            # フレーム内の要素がロードされるまで待機
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.ID, "username")) # ユーザー名フィールドが出現するまで待機
            )
            print("Waited for login form elements to load.")

            # ユーザー名とパスワードのフィールド、ログインボタンを特定
            username_field = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")
            # onclick属性を持つinput[type="image"]要素を特定
            login_button = self.driver.find_element(By.XPATH, '//input[@type="image" and @onclick="doLogin(event);"]')

            print("Waited for login form elements to load.")

            print("Waited for login form elements to load.")

            # JavaScriptを使用してオーバーレイ要素をDOMから削除する
            try:
                self.driver.execute_script("""
                    var overlay = document.getElementById('modal_overlay');
                    if (overlay) {
                        overlay.parentNode.removeChild(overlay);
                        console.log('Modal overlay removed from DOM.');
                    }
                """)
                print("Attempted to remove modal overlay from DOM using JavaScript.")
                # 要素が削除されるまで少し待機
                time.sleep(1)
            except Exception as e:
                print(f"An error occurred while trying to remove modal overlay with JavaScript: {e}")
                # エラーが発生しても処理を続行
                pass


            # ユーザー名入力
            print(f"Entering username: {username}")
            username_field.send_keys(username)

            # パスワード入力
            print(f"Entering password: ********")
            password_field.send_keys(password)

            print("Waited for login form elements to load.")

            # ログインボタンがクリック可能になるまで待機 (JavaScriptで非表示にした後でも念のため待機)
            try:
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.element_to_be_clickable((By.XPATH, '//input[@type="image" and @onclick="doLogin(event);"]'))
                )
                print("Waited for login button to be clickable.")
            except TimeoutException:
                print("Login button was not clickable within the waiting time after attempting to hide overlay.")
                # クリック可能にならない場合は認証失敗と判断
                return False


            # ログインボタンクリック
            print("Clicking login button.")
            login_button.click()

            time.sleep(self.wait_time * 2) # ログイン後の遷移を待機

            # ログイン成功の確認ロジック
            # TODO: ログイン成功を示す要素のセレクタを指定してください
            # 例: ログアウトボタンの存在を確認する場合
            # try:
            #     WebDriverWait(self.driver, self.wait_time).until(
            #         EC.presence_of_element_located((By.LINK_TEXT, "Logout"))
            #     )
            #     print("Login successful: Logout link found.")
            #     return True
            # except TimeoutException:
            #     print("Login failed: Logout link not found after login attempt.")
            #     return False

            print("Login attempt complete. (Login success confirmation not yet implemented)")
            # ログイン成功確認ロジックが未実装のため、ここでは常にTrueを返します
            # 実際の使用時には、上記のTODO部分を適切に実装してください
            # return True # ログイン成功確認ロジックが未実装のため、ここでは常にTrueを返します

            # ログイン成功の確認ロジック
            print("Checking for login success...")
            try:
                # 条件1: masterフレーム内のユーザー名フィールドが非表示になるか削除される
                self.driver.switch_to.default_content() # デフォルトコンテンツに戻る
                self.driver.switch_to.frame("master")
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.invisibility_of_element_located((By.ID, "username"))
                )
                print("Login successful: Username field disappeared.")
                self.driver.switch_to.default_content() # デフォルトコンテンツに戻る
                return True
            except TimeoutException:
                print("Username field did not disappear. Checking for alternative success indicator.")
                self.driver.switch_to.default_content() # デフォルトコンテンツに戻る
                pass # タイムアウトした場合は次の条件を試す
            except NoSuchFrameException:
                 print("Could not switch back to master frame to check username field.")
                 self.driver.switch_to.default_content() # デフォルトコンテンツに戻る
                 pass # フレーム切り替えに失敗した場合も次の条件を試す


            try:
                # 条件2: headerフレーム内のログアウト要素が表示される
                self.driver.switch_to.default_content() # デフォルトコンテンツに戻る
                self.driver.switch_to.frame("header")
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.visibility_of_element_located((By.ID, "logout")) # logout要素が表示されるまで待機
                )
                print("Login successful: Logout element found in header frame.")
                self.driver.switch_to.default_content() # デフォルトコンテンツに戻る
                return True
            except TimeoutException:
                print("Login failed: Logout element not found in header frame after login attempt.")
                self.driver.switch_to.default_content() # デフォルトコンテンツに戻る
                return False
            except NoSuchFrameException:
                 print("Could not switch to header frame to check logout element. Login status unknown.")
                 self.driver.switch_to.default_content() # デフォルトコンテンツに戻る
                 return False # フレーム切り替えに失敗した場合はログイン状態不明とする


        except Exception as e:
            print(f"An error occurred during authentication: {e}")
            return False # 認証失敗

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
    parser.add_argument('url', help='対象の認証ページのURL')
    parser.add_argument('-o', '--output', default='crawl_output',
                        help='結果保存ディレクトリ (デフォルト: crawl_output)')
    parser.add_argument('-w', '--wait', type=int, default=5,
                        help='JavaScript実行待機秒数 (デフォルト: 5秒)')
    # 認証情報に関する引数を追加
    parser.add_argument('--login', action='store_true', help='認証処理を実行する')
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
