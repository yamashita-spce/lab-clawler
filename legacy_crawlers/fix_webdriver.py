#!/usr/bin/env python3
"""
WebDriver問題の修正版テスト
レガシークローラーと同じシンプルな設定を使用
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

def test_simple_webdriver():
    """シンプルなWebDriver設定でテスト"""
    print("🧪 Testing Simple WebDriver Configuration")
    
    try:
        # レガシーと同じシンプル設定
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        
        # ChromeDriverの自動管理を使用
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        
        print("✅ WebDriver initialized successfully")
        
        # 基本的なページアクセステスト
        driver.get("http://127.0.0.1:8888")
        print("✅ Page loaded successfully")
        
        # タイトル確認
        title = driver.title
        print(f"📄 Page title: {title}")
        
        # フレーム検出
        frames = driver.find_elements(By.TAG_NAME, 'frame')
        print(f"🖼️ Found {len(frames)} frames")
        
        driver.quit()
        print("✅ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_webdriver_manager():
    """WebDriverManagerを使用したテスト"""
    print("\n🧪 Testing with WebDriver Manager")
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60)
        
        print("✅ WebDriver with Manager initialized")
        
        driver.get("http://127.0.0.1:8888")
        print("✅ Page loaded with Manager")
        
        driver.quit()
        return True
        
    except ImportError:
        print("⚠️ webdriver-manager not installed")
        return False
    except Exception as e:
        print(f"❌ Manager test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 WebDriver Problem Diagnosis\n")
    
    # テスト1: シンプル設定
    simple_success = test_simple_webdriver()
    
    # テスト2: WebDriver Manager
    manager_success = test_webdriver_manager()
    
    print(f"\n📊 Test Results:")
    print(f"Simple Config: {'✅ PASS' if simple_success else '❌ FAIL'}")
    print(f"Manager Config: {'✅ PASS' if manager_success else '❌ FAIL'}")
    
    if simple_success:
        print("\n💡 Solution: Use simple Chrome configuration like legacy crawler")
    elif manager_success:
        print("\n💡 Solution: Use WebDriver Manager for automatic driver management")
    else:
        print("\n⚠️ Chrome/ChromeDriver installation issue detected")