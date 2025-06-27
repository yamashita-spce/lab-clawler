#!/usr/bin/env python3
"""
IoT Device Crawler Command Line Interface
IoTデバイス自動クローラーのコマンドライン実行インターフェース
"""

import argparse
import sys
import json
import os
from typing import Dict, Any

from iot_crawler.main_crawler import create_iot_crawler
from iot_crawler.config import CrawlerConfig, load_config_from_env

def main():
    """メイン実行関数"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 設定の準備
    config = prepare_config(args)
    
    # クローラーの作成と初期化
    crawler = create_iot_crawler(
        target_url=config.target_url,
        username=config.username, 
        password=config.password,
        verbose=args.verbose
    )
    
    if not crawler.initialize():
        print("Failed to initialize crawler", file=sys.stderr)
        return 1
    
    try:
        if args.command == 'crawl':
            return run_crawl_command(crawler, args)
        elif args.command == 'restore':
            return run_restore_command(crawler, args)
        elif args.command == 'status':
            return run_status_command(crawler, args)
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user")
        return 130
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

def create_argument_parser() -> argparse.ArgumentParser:
    """引数パーサーの作成"""
    parser = argparse.ArgumentParser(
        description="IoT Device Web Interface Crawler for Security Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic crawl
  python iot_crawler_cli.py crawl --url http://192.168.1.1 --user admin --pass password
  
  # Verbose crawl with custom output
  python iot_crawler_cli.py crawl -v --url http://localhost:8888 -o /tmp/crawl_results
  
  # Restore previous session
  python iot_crawler_cli.py restore --session-file /path/to/session.json
  
  # Check crawler status
  python iot_crawler_cli.py status
  
Environment Variables:
  IOT_CRAWLER_TARGET_URL     Target IoT device URL
  IOT_CRAWLER_USERNAME       Login username (default: admin)
  IOT_CRAWLER_PASSWORD       Login password (default: password)
  IOT_CRAWLER_PAGE_TIMEOUT   Page load timeout in seconds (default: 3)
  IOT_CRAWLER_OUTPUT_DIR     Output directory (default: iot_crawler_output)
        """
    )
    
    # サブコマンド
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Crawl コマンド
    crawl_parser = subparsers.add_parser('crawl', help='Start crawling IoT device')
    crawl_parser.add_argument('--url', '-u', 
                             help='Target IoT device URL (e.g., http://192.168.1.1)')
    crawl_parser.add_argument('--username', '--user', 
                             help='Login username (default: admin)')
    crawl_parser.add_argument('--password', '--pass', 
                             help='Login password (default: password)')
    crawl_parser.add_argument('--output', '-o', 
                             help='Output directory (default: iot_crawler_output)')
    crawl_parser.add_argument('--max-depth', type=int, default=10,
                             help='Maximum crawl depth (default: 10)')
    crawl_parser.add_argument('--timeout', type=int, default=3,
                             help='Page load timeout in seconds (default: 3)')
    crawl_parser.add_argument('--no-frames', action='store_true',
                             help='Disable frame crawling')
    crawl_parser.add_argument('--no-forms', action='store_true', 
                             help='Disable form extraction')
    crawl_parser.add_argument('--screenshots', action='store_true',
                             help='Enable screenshot capture')
    crawl_parser.add_argument('--headful', action='store_true',
                             help='Run browser in non-headless mode')
    
    # Restore コマンド
    restore_parser = subparsers.add_parser('restore', help='Restore previous session')
    restore_parser.add_argument('--session-file', '-s', required=True,
                               help='Session file to restore')
    
    # Status コマンド
    status_parser = subparsers.add_parser('status', help='Show crawler status')
    
    # 共通オプション
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--config', '-c',
                       help='Configuration file path')
    
    return parser

def prepare_config(args) -> CrawlerConfig:
    """設定の準備"""
    # 環境変数から基本設定を読み込み
    config = load_config_from_env()
    
    # コマンドライン引数で上書き
    if hasattr(args, 'url') and args.url:
        config.target_url = args.url
    if hasattr(args, 'username') and args.username:
        config.username = args.username
    if hasattr(args, 'password') and args.password:
        config.password = args.password
    if hasattr(args, 'output') and args.output:
        config.output_dir = args.output
    if hasattr(args, 'max_depth') and args.max_depth:
        config.max_depth = args.max_depth
    if hasattr(args, 'timeout') and args.timeout:
        config.page_load_timeout = args.timeout
        config.element_wait_timeout = args.timeout
        config.frame_wait_timeout = args.timeout
    if hasattr(args, 'no_frames') and args.no_frames:
        config.crawl_frames = False
    if hasattr(args, 'no_forms') and args.no_forms:
        config.extract_forms = False
    if hasattr(args, 'screenshots') and args.screenshots:
        config.save_screenshots = True
    if hasattr(args, 'headful') and args.headful:
        config.headless = False
    
    return config

def run_crawl_command(crawler, args) -> int:
    """クロールコマンドの実行"""
    print("🚀 Starting IoT Device Crawl")
    print(f"Target: {crawler.config.target_url}")
    print(f"Session ID: {crawler.session_id}")
    print(f"Output Directory: {crawler.config.output_dir}")
    print("-" * 50)
    
    # クロール実行
    results = crawler.run_full_crawl()
    
    if results.get('status') == 'error':
        print(f"❌ Crawl failed: {results.get('error')}")
        return 1
    
    # 結果表示
    print_crawl_results(results)
    
    return 0

def run_restore_command(crawler, args) -> int:
    """復元コマンドの実行"""
    print(f"🔄 Restoring session from: {args.session_file}")
    
    if not os.path.exists(args.session_file):
        print(f"❌ Session file not found: {args.session_file}")
        return 1
    
    success = crawler.restore_session(args.session_file)
    
    if success:
        print("✅ Session restored successfully")
        return 0
    else:
        print("❌ Session restoration failed")
        return 1

def run_status_command(crawler, args) -> int:
    """ステータスコマンドの実行"""
    status = crawler.get_status()
    
    print("📊 Crawler Status")
    print(f"Session ID: {status['session_id']}")
    print(f"Initialized: {'✅' if status['initialized'] else '❌'}")
    print(f"Authenticated: {'✅' if status['authenticated'] else '❌'}")
    print(f"Pages Crawled: {status['pages_crawled']}")
    print(f"Frames Crawled: {status['frames_crawled']}")
    print(f"Target URL: {status['target_url']}")
    
    return 0

def print_crawl_results(results: Dict[str, Any]):
    """クロール結果の表示"""
    print("✅ Crawl completed successfully!")
    print()
    
    # サマリー情報
    crawl_summary = results.get('crawl_summary', {})
    analysis_summary = results.get('analysis_summary', {})
    
    print("📈 Crawl Summary:")
    print(f"  • Pages discovered: {crawl_summary.get('total_pages', 0)}")
    print(f"  • Frames analyzed: {crawl_summary.get('total_frames', 0)}")
    print(f"  • Forms found: {crawl_summary.get('total_forms', 0)}")
    print(f"  • Links discovered: {crawl_summary.get('total_links', 0)}")
    print(f"  • Maximum depth: {crawl_summary.get('crawl_depth', 0)}")
    print()
    
    # セキュリティ分析
    print("🔒 Security Analysis:")
    endpoint_types = analysis_summary.get('endpoint_types', {})
    for endpoint_type, count in endpoint_types.items():
        print(f"  • {endpoint_type.capitalize()} endpoints: {count}")
    
    security_issues = analysis_summary.get('security_issues', {})
    if security_issues:
        print(f"  • Security issues detected: {len(security_issues)}")
        for issue, count in security_issues.items():
            print(f"    - {issue}: {count}")
    else:
        print("  • No security issues detected")
    print()
    
    # Fuzzing準備状況
    fuzzing_readiness = results.get('fuzzing_readiness', {})
    print("🎯 Fuzzing Readiness:")
    print(f"  • Readiness Score: {fuzzing_readiness.get('score', 0)}/100")
    print(f"  • Readiness Level: {fuzzing_readiness.get('level', 'Unknown')}")
    
    factors = fuzzing_readiness.get('factors', {})
    for factor, value in factors.items():
        print(f"  • {factor.replace('_', ' ').title()}: {value}")
    print()
    
    # 推奨事項
    recommendations = results.get('recommendations', [])
    if recommendations:
        print("💡 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        print()
    
    # 出力ファイル
    output_files = results.get('output_files', {})
    print("📁 Output Files:")
    for file_type, file_path in output_files.items():
        if file_path:
            print(f"  • {file_type.replace('_', ' ').title()}: {file_path}")
    print()
    
    print(f"🎉 Session ID: {results['session_id']}")
    print("Use the session ID to restore this crawl state for fuzzing")

if __name__ == '__main__':
    sys.exit(main())