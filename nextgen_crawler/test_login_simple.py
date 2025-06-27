#!/usr/bin/env python3
"""
Simple Login Test for IoT Device
単純なログインテスト
"""

import sys
import time
sys.path.append('./iot_crawler')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_simple_login():
    """シンプルなログインテスト"""
    print("🔧 Initializing WebDriver...")
    
    # Chrome設定（安定性重視）
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = None
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        print("🌐 Accessing target URL...")
        driver.get("http://127.0.0.1:8888")
        
        print("🔍 Looking for login elements...")
        
        # フレームを確認
        frames = driver.find_elements(By.TAG_NAME, "frame")
        frames.extend(driver.find_elements(By.TAG_NAME, "iframe"))
        
        print(f"📊 Found {len(frames)} frames")
        
        login_successful = False
        
        # メインページでログイン試行
        try:
            username_field = driver.find_element(By.NAME, "username")
            password_field = driver.find_element(By.NAME, "password")
            print("✅ Found login elements on main page")
        except:
            print("⚠️ No login elements on main page, trying frames...")
            
            # フレーム内でログイン試行
            for i, frame in enumerate(frames):
                try:
                    print(f"🔄 Trying frame {i}...")
                    driver.switch_to.frame(frame)
                    
                    username_field = driver.find_element(By.NAME, "username")
                    password_field = driver.find_element(By.NAME, "password")
                    submit_button = driver.find_element(By.XPATH, "//input[@type='submit'] | //input[@type='image'] | //button[@type='submit']")
                    
                    print(f"✅ Found login elements in frame {i}")
                    
                    # ログイン実行
                    username_field.clear()
                    username_field.send_keys("admin")
                    
                    password_field.clear()
                    password_field.send_keys("password")
                    
                    print("🔑 Submitting login...")
                    
                    # モーダルオーバーレイを削除
                    try:
                        driver.execute_script("""
                            var overlay = document.getElementById('modal_overlay');
                            if (overlay) overlay.remove();
                        """)
                        time.sleep(0.5)
                    except:
                        pass
                    
                    submit_button.click()
                    
                    # 短時間待機
                    time.sleep(3)
                    
                    # ログイン成功の確認（ユーザー名フィールドが消失するか確認）
                    try:
                        driver.find_element(By.NAME, "username")
                        print("⚠️ Username field still present")
                    except:
                        print("✅ Username field disappeared - login likely successful")
                        login_successful = True
                    
                    # アラートがあれば処理
                    try:
                        alert = driver.switch_to.alert
                        print(f"📢 Alert detected: {alert.text}")
                        alert.accept()
                        time.sleep(1)
                    except:
                        pass
                    
                    driver.switch_to.default_content()
                    break
                    
                except Exception as e:
                    print(f"❌ Frame {i} failed: {str(e)}")
                    try:
                        driver.switch_to.default_content()
                    except:
                        pass
                    continue
        
        if login_successful:
            print("🎉 Login successful!")
            
            # ログイン後の基本的なページ状態を確認
            print("📊 Post-login analysis...")
            
            current_url = driver.current_url
            page_title = driver.title
            
            print(f"📍 Current URL: {current_url}")
            print(f"📄 Page Title: {page_title}")
            
            # フレーム構造の分析
            post_login_frames = driver.find_elements(By.TAG_NAME, "frame")
            post_login_frames.extend(driver.find_elements(By.TAG_NAME, "iframe"))
            
            print(f"🖼️ Post-login frames: {len(post_login_frames)}")
            
            for i, frame in enumerate(post_login_frames):
                frame_name = frame.get_attribute("name") or f"frame_{i}"
                frame_src = frame.get_attribute("src") or "No src"
                print(f"  Frame {i}: {frame_name} -> {frame_src}")
            
            # リンクの抽出
            links = driver.find_elements(By.TAG_NAME, "a")
            print(f"🔗 Links found: {len(links)}")
            
            for i, link in enumerate(links[:10]):  # 最初の10個のみ
                href = link.get_attribute("href")
                text = link.text.strip()
                if href:
                    print(f"  Link {i}: {text} -> {href}")
            
            # フォームの抽出
            forms = driver.find_elements(By.TAG_NAME, "form")
            print(f"📝 Forms found: {len(forms)}")
            
            for i, form in enumerate(forms):
                action = form.get_attribute("action") or "No action"
                method = form.get_attribute("method") or "GET"
                print(f"  Form {i}: {method} -> {action}")
            
            return True
        else:
            print("❌ Login failed")
            return False
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return False
        
    finally:
        if driver:
            driver.quit()
            print("🧹 WebDriver closed")

if __name__ == "__main__":
    success = test_simple_login()
    exit(0 if success else 1)