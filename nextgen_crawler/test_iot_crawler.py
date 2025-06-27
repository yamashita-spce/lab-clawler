#!/usr/bin/env python3
"""
IoT Crawler Test Script
簡単な動作確認用スクリプト
"""

from iot_crawler import create_iot_crawler

def test_basic_crawl():
    """基本的なクロールテスト"""
    print("🧪 Starting IoT Crawler Test")
    
    try:
        # クローラー作成
        crawler = create_iot_crawler(
            target_url="http://127.0.0.1:8888",
            username="admin",
            password="password",
            verbose=True
        )
        
        print("✅ Crawler created successfully")
        
        # 初期化テスト
        if crawler.initialize():
            print("✅ Crawler initialized successfully")
            
            # ステータス確認
            status = crawler.get_status()
            print(f"📊 Status: {status}")
            
            # 認証のみテスト
            print("🔐 Testing authentication only...")
            success = crawler._perform_authentication(
                "http://127.0.0.1:8888", "admin", "password"
            )
            
            if success:
                print("✅ Authentication successful!")
                return True
            else:
                print("❌ Authentication failed")
                return False
        else:
            print("❌ Crawler initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False
    finally:
        # クリーンアップ
        if 'crawler' in locals():
            crawler._cleanup()

if __name__ == "__main__":
    success = test_basic_crawl()
    print(f"\n🎯 Test Result: {'PASSED' if success else 'FAILED'}")