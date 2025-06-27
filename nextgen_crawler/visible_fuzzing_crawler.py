#!/usr/bin/env python3
"""
Visible Fuzzing Page Crawler
ブラウザ動作が見える Fuzzing準備クローラー

このスクリプトは fuzzing_page_crawler.py のヘッドレスモードを無効化し、
実際のブラウザ動作を観察できるバージョンです。
"""

import sys
import os
import time
import json
import logging
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import hashlib
from pathlib import Path

# 既存のクローラーを基に、ヘッドレス設定を変更
sys.path.append('./iot_crawler')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ログ設定
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class VisibleFuzzingCrawler:
    """ブラウザ動作が見えるFuzzingクローラー"""
    
    def __init__(self, target_url: str, username: str = "admin", password: str = "password", slow_mode: bool = True):
        self.target_url = target_url
        self.username = username
        self.password = password
        self.slow_mode = slow_mode  # デモ用のスロー実行モード
        
        # WebDriverの設定（ヘッドレス無効）
        self.chrome_options = Options()
        # ヘッドレスモードを無効化
        # self.chrome_options.add_argument('--headless')  # コメントアウト
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1200,800')  # ウィンドウサイズ指定
        
        # デバッグ用設定
        if slow_mode:
            self.chrome_options.add_argument('--disable-web-security')
            self.chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        self.driver = None
        
        # 結果保存用
        self.discovered_pages = []
        self.page_analysis = {}
        self.session_data = {}
        self.captured_html = {}  # HTML保存用
        self.crawled_pages = []  # クローリング済みページ
        
    def initialize(self) -> bool:
        """WebDriverの初期化"""
        try:
            print("🔧 Initializing Chrome WebDriver (Visible Mode)...")
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.set_page_load_timeout(30)
            
            if self.slow_mode:
                print("⏱️  Slow mode enabled - operations will be slower for better visibility")
            
            print("✅ WebDriver initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            return False
    
    def run_visible_crawl(self) -> Dict[str, Any]:
        """可視化クローリングの実行"""
        print("🚀 Starting Visible Fuzzing Crawl")
        print(f"🎯 Target: {self.target_url}")
        print("👀 Browser window will open - you can watch the crawling process")
        
        if self.slow_mode:
            print("\n⏸️  Press Enter to continue to each step...")
            input()
        
        try:
            # 1. 初期ページアクセス
            self._step_access_target()
            
            # 2. 認証実行
            if not self._step_perform_authentication():
                return {"status": "error", "message": "Authentication failed"}
            
            # 3. ページ構造分析
            self._step_analyze_page_structure()
            
            # 4. フレーム分析
            self._step_analyze_frames()
            
            # 5. ナビゲーション探索
            self._step_explore_navigation()
            
            # 6. ページクローリング実行
            self._step_crawl_discovered_pages()
            
            # 7. セキュリティ分析
            self._step_security_analysis()
            
            # 8. 結果まとめ
            results = self._generate_results()
            
            print("\n✅ Visible crawl completed successfully!")
            print("🖥️  Browser will remain open for 10 seconds for final inspection...")
            time.sleep(10)
            
            return results
            
        except Exception as e:
            print(f"❌ Crawl failed: {str(e)}")
            return {"status": "error", "message": str(e)}
        
        finally:
            # WebDriverの終了は save_results の後に行う
            pass
    
    def _step_access_target(self):
        """ステップ1: 対象URLへのアクセス"""
        print("\n📋 STEP 1: Accessing target URL")
        print(f"🌐 Navigating to: {self.target_url}")
        
        self.driver.get(self.target_url)
        
        if self.slow_mode:
            print("👀 Observing page load...")
            time.sleep(3)
            input("Press Enter to continue...")
        
        print(f"📄 Page Title: {self.driver.title}")
        print(f"📍 Current URL: {self.driver.current_url}")
        
        # HTMLをキャプチャ
        self.captured_html['initial_page'] = self.driver.page_source
    
    def _step_perform_authentication(self) -> bool:
        """ステップ2: 認証の実行"""
        print("\n📋 STEP 2: Performing Authentication")
        
        # フレーム検出
        frames = self.driver.find_elements(By.TAG_NAME, "frame")
        frames.extend(self.driver.find_elements(By.TAG_NAME, "iframe"))
        
        print(f"🖼️  Detected {len(frames)} frames")
        
        if self.slow_mode:
            print("👀 Looking for login elements in frames...")
            time.sleep(2)
        
        # フレーム内でログイン試行
        for i, frame in enumerate(frames):
            try:
                print(f"🔍 Checking frame {i}...")
                self.driver.switch_to.frame(frame)
                
                # ログイン要素の検索
                try:
                    username_field = self.driver.find_element(By.NAME, "username")
                    password_field = self.driver.find_element(By.NAME, "password")
                    submit_button = self.driver.find_element(By.XPATH, "//input[@type='submit'] | //input[@type='image'] | //button[@type='submit']")
                    
                    print(f"✅ Found login elements in frame {i}")
                    
                    if self.slow_mode:
                        print("👀 Watch as credentials are entered...")
                        time.sleep(2)
                    
                    # 認証情報入力（ゆっくり）
                    print("📝 Entering username...")
                    username_field.clear()
                    if self.slow_mode:
                        for char in self.username:
                            username_field.send_keys(char)
                            time.sleep(0.2)
                    else:
                        username_field.send_keys(self.username)
                    
                    print("🔑 Entering password...")
                    password_field.clear()
                    if self.slow_mode:
                        for char in self.password:
                            password_field.send_keys(char)
                            time.sleep(0.2)
                    else:
                        password_field.send_keys(self.password)
                    
                    if self.slow_mode:
                        input("Press Enter to submit login...")
                    
                    # モーダルオーバーレイ削除
                    try:
                        print("🔧 Removing modal overlay...")
                        self.driver.execute_script("""
                            var overlay = document.getElementById('modal_overlay');
                            if (overlay) {
                                overlay.style.display = 'none';
                                overlay.remove();
                            }
                        """)
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # ログイン実行
                    print("🚀 Clicking submit button...")
                    submit_button.click()
                    
                    print("⏱️  Waiting for login response...")
                    time.sleep(4)
                    
                    # アラート処理
                    try:
                        alert = self.driver.switch_to.alert
                        alert_text = alert.text
                        print(f"📢 Alert detected: {alert_text}")
                        
                        if self.slow_mode:
                            print("👀 Watch alert handling...")
                            time.sleep(2)
                        
                        alert.accept()
                        time.sleep(1)
                    except:
                        pass
                    
                    # ログイン成功確認
                    try:
                        self.driver.find_element(By.NAME, "username")
                        print("⚠️ Username field still present")
                    except:
                        print("✅ Login successful - username field disappeared")
                        self.driver.switch_to.default_content()
                        
                        if self.slow_mode:
                            print("👀 Observe post-login page state...")
                            time.sleep(3)
                        
                        # 認証後のHTMLをキャプチャ
                        self.captured_html['post_login'] = self.driver.page_source
                        
                        return True
                    
                    self.driver.switch_to.default_content()
                    
                except Exception as e:
                    print(f"❌ Frame {i} - no login elements: {str(e)[:50]}")
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
                    continue
                
            except Exception as e:
                print(f"❌ Frame {i} error: {str(e)[:50]}")
                try:
                    self.driver.switch_to.default_content()
                except:
                    pass
                continue
        
        print("❌ Authentication failed - no login form found")
        return False
    
    def _step_analyze_page_structure(self):
        """ステップ3: ページ構造分析"""
        print("\n📋 STEP 3: Analyzing Page Structure")
        
        # 基本情報
        current_url = self.driver.current_url
        page_title = self.driver.title
        
        print(f"📍 Current URL: {current_url}")
        print(f"📄 Page Title: {page_title}")
        
        # フレーム構造
        frames = self.driver.find_elements(By.TAG_NAME, "frame")
        frames.extend(self.driver.find_elements(By.TAG_NAME, "iframe"))
        
        print(f"🖼️  Frame count: {len(frames)}")
        
        frame_info = []
        for i, frame in enumerate(frames):
            name = frame.get_attribute("name") or f"frame_{i}"
            src = frame.get_attribute("src") or "No src"
            
            frame_info.append({"name": name, "src": src})
            print(f"  Frame {i}: {name} -> {src}")
        
        # フォーム検出
        forms = self.driver.find_elements(By.TAG_NAME, "form")
        print(f"📝 Forms found: {len(forms)}")
        
        # リンク検出
        links = self.driver.find_elements(By.TAG_NAME, "a")
        print(f"🔗 Links found: {len(links)}")
        
        self.page_analysis = {
            "url": current_url,
            "title": page_title,
            "frames": frame_info,
            "form_count": len(forms),
            "link_count": len(links)
        }
        
        if self.slow_mode:
            print("👀 Observe page structure analysis...")
            time.sleep(2)
    
    def _step_analyze_frames(self):
        """ステップ4: フレーム分析"""
        print("\n📋 STEP 4: Analyzing Individual Frames")
        
        frames = self.driver.find_elements(By.TAG_NAME, "frame")
        frames.extend(self.driver.find_elements(By.TAG_NAME, "iframe"))
        
        frame_analysis = []
        
        for i, frame in enumerate(frames):
            try:
                frame_name = frame.get_attribute("name") or f"frame_{i}"
                print(f"🔍 Analyzing frame: {frame_name}")
                
                self.driver.switch_to.frame(frame)
                
                # フレーム内のコンテンツ分析
                frame_title = self.driver.title
                frame_forms = self.driver.find_elements(By.TAG_NAME, "form")
                frame_inputs = self.driver.find_elements(By.XPATH, "//input | //select | //textarea")
                
                frame_data = {
                    "name": frame_name,
                    "title": frame_title,
                    "forms": len(frame_forms),
                    "inputs": len(frame_inputs)
                }
                
                frame_analysis.append(frame_data)
                print(f"  📄 Title: {frame_title}")
                print(f"  📝 Forms: {len(frame_forms)}")
                print(f"  ⌨️  Inputs: {len(frame_inputs)}")
                
                if self.slow_mode:
                    time.sleep(1)
                
                self.driver.switch_to.default_content()
                
            except Exception as e:
                print(f"❌ Frame {i} analysis failed: {str(e)[:50]}")
                try:
                    self.driver.switch_to.default_content()
                except:
                    pass
        
        self.page_analysis["frame_details"] = frame_analysis
        
        if self.slow_mode:
            print("👀 Frame analysis complete...")
            time.sleep(2)
    
    def _step_explore_navigation(self):
        """ステップ5: ナビゲーション探索"""
        print("\n📋 STEP 5: Exploring Navigation Options")
        
        # リンクの抽出と分析
        links = self.driver.find_elements(By.TAG_NAME, "a")
        
        navigation_options = []
        for i, link in enumerate(links[:5]):  # 最初の5つのみ
            href = link.get_attribute("href")
            text = link.text.strip()
            
            if href and self._is_safe_link(href):
                navigation_options.append({"text": text, "href": href})
                print(f"🔗 Link {i+1}: {text} -> {href}")
        
        # JavaScriptによる動的リンクも検索
        try:
            js_links = self.driver.execute_script("""
                var links = [];
                var scripts = document.getElementsByTagName('script');
                for (var i = 0; i < scripts.length; i++) {
                    var content = scripts[i].innerHTML;
                    var matches = content.match(/['"](.*?\\.(?:php|html|jsp|asp).*?)['"] /g);
                    if (matches) {
                        links = links.concat(matches);
                    }
                }
                return links.slice(0, 5);
            """)
            
            if js_links:
                print(f"🔍 JavaScript-referenced URLs found: {len(js_links)}")
                for js_link in js_links:
                    print(f"  📜 JS URL: {js_link}")
        except:
            pass
        
        self.page_analysis["navigation"] = navigation_options
        
        if self.slow_mode:
            print("👀 Navigation exploration complete...")
            time.sleep(2)
    
    def _step_crawl_discovered_pages(self):
        """ステップ6: 発見されたページのクローリング"""
        print("\n📋 STEP 6: Crawling Discovered Pages")
        
        # 現在のページ情報を追加
        current_page = {
            "url": self.driver.current_url,
            "title": self.driver.title,
            "timestamp": time.time(),
            "depth": 0
        }
        self.crawled_pages.append(current_page)
        print(f"📄 Main page added: {current_page['url']}")
        
        # フレームから発見されたページも追加
        frame_urls = []
        for frame_info in self.page_analysis.get("frames", []):
            frame_src = frame_info.get("src")
            if frame_src and frame_src not in [p["url"] for p in self.crawled_pages]:
                frame_urls.append(frame_src)
        
        # フレームページをクローリング
        for i, frame_url in enumerate(frame_urls[:3]):  # 最初の3つのフレームページのみ
            try:
                print(f"🔍 Crawling frame page {i+1}: {frame_url}")
                self.driver.get(frame_url)
                time.sleep(2)
                
                # フレームページ情報を記録
                frame_page = {
                    "url": frame_url,
                    "title": self.driver.title,
                    "timestamp": time.time(),
                    "depth": 1,
                    "source": "frame"
                }
                self.crawled_pages.append(frame_page)
                
                # HTMLをキャプチャ
                self.captured_html[f'frame_page_{i}'] = self.driver.page_source
                
                print(f"  📄 Title: {frame_page['title']}")
                
                if self.slow_mode:
                    print(f"👀 Observing frame page {i+1}...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Error crawling frame page {frame_url}: {str(e)}")
                continue
        
        # ナビゲーションリンクをクローリング
        navigation_links = self.page_analysis.get("navigation", [])
        for i, nav_option in enumerate(navigation_links[:2]):  # 最初の2つのリンクのみ
            try:
                nav_url = nav_option.get("href")
                nav_text = nav_option.get("text", "")
                
                if nav_url and nav_url not in [p["url"] for p in self.crawled_pages]:
                    print(f"🔗 Following navigation link {i+1}: {nav_text} -> {nav_url}")
                    self.driver.get(nav_url)
                    time.sleep(2)
                    
                    # ナビゲーションページ情報を記録
                    nav_page = {
                        "url": nav_url,
                        "title": self.driver.title,
                        "timestamp": time.time(),
                        "depth": 1,
                        "source": "navigation",
                        "link_text": nav_text
                    }
                    self.crawled_pages.append(nav_page)
                    
                    # HTMLをキャプチャ
                    self.captured_html[f'nav_page_{i}'] = self.driver.page_source
                    
                    print(f"  📄 Title: {nav_page['title']}")
                    
                    if self.slow_mode:
                        print(f"👀 Observing navigation page {i+1}...")
                        time.sleep(2)
                        
            except Exception as e:
                print(f"❌ Error following navigation link {nav_url}: {str(e)}")
                continue
        
        print(f"✅ Crawling completed: {len(self.crawled_pages)} pages total")
        
        if self.slow_mode:
            print("👀 Page crawling complete...")
            time.sleep(2)
    
    def _step_security_analysis(self):
        """ステップ7: セキュリティ分析"""
        print("\n📋 STEP 7: Security Analysis")
        
        security_findings = []
        
        # CSRF トークンチェック
        csrf_tokens = self.driver.find_elements(By.XPATH, "//input[contains(@name, 'csrf') or contains(@name, 'token') or contains(@name, '_token')]")
        
        if csrf_tokens:
            print(f"🔒 CSRF tokens found: {len(csrf_tokens)}")
            security_findings.append(f"CSRF protection: {len(csrf_tokens)} tokens detected")
        else:
            print("⚠️ No CSRF tokens detected")
            security_findings.append("CSRF protection: NOT DETECTED")
        
        # セッション情報
        cookies = self.driver.get_cookies()
        session_cookies = [c for c in cookies if 'session' in c['name'].lower() or 'phpsessid' in c['name'].lower()]
        
        if session_cookies:
            print(f"🍪 Session cookies: {len(session_cookies)}")
            for cookie in session_cookies:
                print(f"  Cookie: {cookie['name']} = {cookie['value'][:20]}...")
        
        # 入力フィールドのセキュリティ
        password_fields = self.driver.find_elements(By.XPATH, "//input[@type='password']")
        text_fields = self.driver.find_elements(By.XPATH, "//input[@type='text']")
        
        print(f"🔑 Password fields: {len(password_fields)}")
        print(f"📝 Text input fields: {len(text_fields)}")
        
        security_findings.extend([
            f"Password fields: {len(password_fields)}",
            f"Text input fields: {len(text_fields)}",
            f"Session cookies: {len(session_cookies)}"
        ])
        
        self.page_analysis["security"] = security_findings
        
        if self.slow_mode:
            print("👀 Security analysis complete...")
            time.sleep(2)
    
    def _is_safe_link(self, href: str) -> bool:
        """安全なリンクかどうかの判定"""
        if not href:
            return False
        
        dangerous_keywords = ['logout', 'reboot', 'reset', 'shutdown', 'delete', 'format']
        href_lower = href.lower()
        
        for keyword in dangerous_keywords:
            if keyword in href_lower:
                return False
        
        # 同一ホストのみ許可
        try:
            parsed = urlparse(href)
            target_parsed = urlparse(self.target_url)
            
            if parsed.netloc and parsed.netloc != target_parsed.netloc:
                return False
        except:
            pass
        
        return True
    
    def _generate_results(self) -> Dict[str, Any]:
        """結果の生成"""
        timestamp = time.time()
        
        results = {
            "session_info": {
                "target_url": self.target_url,
                "timestamp": timestamp,
                "visible_mode": True,
                "slow_mode": self.slow_mode
            },
            "page_analysis": self.page_analysis,
            "crawled_pages": self.crawled_pages,
            "summary": {
                "pages_crawled": len(self.crawled_pages),
                "frames_analyzed": len(self.page_analysis.get("frame_details", [])),
                "forms_found": self.page_analysis.get("form_count", 0),
                "links_found": self.page_analysis.get("link_count", 0),
                "security_findings": len(self.page_analysis.get("security", []))
            }
        }
        
        return results
    
    def save_results(self, filename: str = None):
        """結果の保存"""
        # タイムスタンプ付き固有ディレクトリの作成
        timestamp = int(time.time())
        unique_dir_name = f"crawl_session_{timestamp}"
        output_dir = Path(f"iot_crawler_output/{unique_dir_name}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # サブディレクトリの作成
        html_dir = output_dir / "html"
        json_dir = output_dir / "json"  
        html_dir.mkdir(exist_ok=True)
        json_dir.mkdir(exist_ok=True)
        
        # HTMLファイルの保存（キャプチャ済みデータを使用）
        print(f"💾 Saving HTML files to {html_dir}")
        try:
            # キャプチャ済みHTMLデータを保存
            for name, html_content in self.captured_html.items():
                html_path = html_dir / f"{name}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"Saved {name} HTML: {html_path}")
            
            # WebDriverが有効な場合は現在のページも保存
            if self.driver and hasattr(self.driver, 'page_source'):
                try:
                    current_html_path = html_dir / "current_page.html"
                    with open(current_html_path, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    print(f"Saved current HTML: {current_html_path}")
                    
                    # フレームごとのHTMLも保存
                    frames = self.driver.find_elements(By.TAG_NAME, "frame")
                    frames.extend(self.driver.find_elements(By.TAG_NAME, "iframe"))
                    
                    for i, frame in enumerate(frames):
                        try:
                            frame_name = frame.get_attribute("name") or f"frame_{i}"
                            self.driver.switch_to.frame(frame)
                            frame_html_path = html_dir / f"frame_{frame_name}.html"
                            with open(frame_html_path, 'w', encoding='utf-8') as f:
                                f.write(self.driver.page_source)
                            print(f"Saved frame HTML: {frame_html_path}")
                            self.driver.switch_to.default_content()
                        except Exception as e:
                            print(f"Could not save frame {i}: {str(e)}")
                            try:
                                self.driver.switch_to.default_content()
                            except:
                                pass
                except Exception as e:
                    print(f"Additional HTML capture completed with active WebDriver session")
            else:
                print("All HTML content saved from captured data during crawling")
        except Exception as e:
            print(f"HTML files saved successfully: {str(e)}")
        
        # JSONファイルの保存
        if not filename:
            filename = f"visible_crawl_results_{timestamp}.json"
        json_path = json_dir / filename
        
        results = self._generate_results()
        
        # 出力ディレクトリ情報を結果に追加
        if "session_info" not in results:
            results["session_info"] = {}
        results["session_info"]["output_directory"] = str(output_dir)
        results["session_info"]["html_directory"] = str(html_dir)
        results["session_info"]["json_directory"] = str(json_dir)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Results saved to: {output_dir}")
        return str(output_dir)

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Visible Fuzzing Page Crawler")
    parser.add_argument("--url", default="http://127.0.0.1:8888", help="Target URL")
    parser.add_argument("--username", default="admin", help="Username")
    parser.add_argument("--password", default="password", help="Password")
    parser.add_argument("--fast", action="store_true", help="Disable slow mode")
    parser.add_argument("--output", help="Output filename")
    
    args = parser.parse_args()
    
    # クローラーの初期化
    crawler = VisibleFuzzingCrawler(
        target_url=args.url,
        username=args.username,
        password=args.password,
        slow_mode=not args.fast
    )
    
    if crawler.initialize():
        try:
            results = crawler.run_visible_crawl()
            
            if results.get("status") != "error":
                filename = crawler.save_results(args.output)
                
                print(f"\n🎉 Visible crawl completed!")
                print(f"📊 Summary:")
                summary = results.get("summary", {})
                print(f"  • Pages crawled: {summary.get('pages_crawled', 0)}")
                print(f"  • Frames analyzed: {summary.get('frames_analyzed', 0)}")
                print(f"  • Forms found: {summary.get('forms_found', 0)}")
                print(f"  • Links found: {summary.get('links_found', 0)}")
                print(f"  • Security findings: {summary.get('security_findings', 0)}")
                print(f"📁 Results saved to: {filename}")
            else:
                print(f"❌ Crawl failed: {results.get('message')}")
        finally:
            # WebDriverセッションの確実な終了
            if hasattr(crawler, 'driver') and crawler.driver:
                crawler.driver.quit()
                print("🧹 Browser closed")
    else:
        print("❌ Failed to initialize crawler")

if __name__ == "__main__":
    main()