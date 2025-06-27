"""
IoT Device Main Crawler Module
全モジュールを統合したメインクローラー
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

from .config import CrawlerConfig, CrawlerLogger, load_config_from_env
from .authentication import IoTAuthenticator
from .page_crawler import IoTPageCrawler
from .session_manager import IoTSessionManager
from .structure_analyzer import IoTStructureAnalyzer
from .output_manager import IoTOutputManager

class IoTMainCrawler:
    """IoTデバイス統合クローラー"""
    
    def __init__(self, config: CrawlerConfig = None, verbose: bool = False):
        # 設定の初期化
        self.config = config or load_config_from_env()
        self.logger = CrawlerLogger(verbose=verbose)
        
        # コンポーネントの初期化
        self.driver: Optional[webdriver.Chrome] = None
        self.authenticator: Optional[IoTAuthenticator] = None
        self.page_crawler: Optional[IoTPageCrawler] = None
        self.session_manager: Optional[IoTSessionManager] = None
        self.structure_analyzer: Optional[IoTStructureAnalyzer] = None
        self.output_manager: Optional[IoTOutputManager] = None
        
        # セッション管理
        self.session_id = str(uuid.uuid4())
        self.crawl_results: Dict[str, Any] = {}
        self.analysis_results: Dict[str, Any] = {}
        
    def initialize(self) -> bool:
        """クローラーの初期化"""
        self.logger.info("Initializing IoT Crawler")
        
        try:
            # WebDriverの初期化
            if not self._init_webdriver():
                return False
            
            # コンポーネントの初期化
            self.authenticator = IoTAuthenticator(self.driver, self.config, self.logger)
            self.page_crawler = IoTPageCrawler(self.driver, self.config, self.logger)
            self.session_manager = IoTSessionManager(self.driver, self.config, self.logger)
            self.structure_analyzer = IoTStructureAnalyzer(self.driver, self.config, self.logger)
            self.output_manager = IoTOutputManager(self.config, self.logger)
            
            # セッション開始
            self.session_manager.create_session(self.session_id)
            self.output_manager.set_session_id(self.session_id)
            
            self.logger.info(f"Crawler initialized with session ID: {self.session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize crawler: {str(e)}")
            return False
    
    def _init_webdriver(self) -> bool:
        """WebDriverの初期化"""
        try:
            # レガシークローラーと同じシンプル設定
            chrome_options = Options()
            
            if self.config.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--disable-gpu')
            # 過剰な設定を削除してシンプル化
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(60)  # レガシーと同じ60秒
            
            self.logger.info("WebDriver initialized successfully")
            return True
            
        except WebDriverException as e:
            self.logger.error(f"Failed to initialize WebDriver: {str(e)}")
            return False
    
    def run_full_crawl(self, target_url: str = None, username: str = None, 
                       password: str = None) -> Dict[str, Any]:
        """完全クロールの実行"""
        target_url = target_url or self.config.target_url
        username = username or self.config.username
        password = password or self.config.password
        
        self.logger.info(f"Starting full crawl for: {target_url}")
        
        try:
            # 1. 認証処理
            if not self._perform_authentication(target_url, username, password):
                self.logger.error("Authentication failed")
                return self._create_error_result("Authentication failed")
            
            # 2. 認証状態の保存
            auth_state = self.session_manager.capture_auth_state(
                target_url, username, True, 
                getattr(self.authenticator, 'auth_data', {}).get('frame')
            )
            
            # 3. 全ページクロール
            self.crawl_results = self.page_crawler.crawl_all_pages(target_url)
            
            # 4. 構造分析
            self._perform_structure_analysis()
            
            # 5. 結果保存
            return self._save_and_finalize_results()
            
        except Exception as e:
            self.logger.error(f"Error during full crawl: {str(e)}")
            return self._create_error_result(str(e))
        
        finally:
            self._cleanup()
    
    def _perform_authentication(self, target_url: str, username: str, password: str) -> bool:
        """認証処理の実行"""
        self.logger.info("Performing authentication")
        
        try:
            success = self.authenticator.authenticate(target_url, username, password)
            
            if success:
                self.logger.info("Authentication successful")
                # 認証アクションの記録
                self.session_manager.record_crawl_action(
                    'authenticate', target_url, 
                    {'username': username, 'success': True}
                )
            else:
                self.logger.error("Authentication failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return False
    
    def _perform_structure_analysis(self):
        """構造分析の実行"""
        self.logger.info("Performing structure analysis")
        
        try:
            analysis_results = {}
            
            # 各ページの構造分析
            for page in self.page_crawler.get_pages_data():
                page_analysis = self.structure_analyzer.analyze_page_structure(
                    page.url, page.html_content
                )
                analysis_results[page.url] = page_analysis
            
            # 包括的な分析結果
            self.analysis_results = self.structure_analyzer.get_comprehensive_analysis()
            self.analysis_results['detailed_analysis'] = analysis_results
            
            self.logger.info("Structure analysis completed")
            
        except Exception as e:
            self.logger.error(f"Structure analysis error: {str(e)}")
    
    def _save_and_finalize_results(self) -> Dict[str, Any]:
        """結果保存と最終化"""
        self.logger.info("Saving and finalizing results")
        
        try:
            # HTMLファイルの保存
            html_files = self.output_manager.save_page_data(
                self.page_crawler.get_pages_data()
            )
            
            # フレームファイルの保存
            frame_files = self.output_manager.save_frame_data(
                self.page_crawler.get_frames_data()
            )
            
            # JSON結果の保存
            crawl_results_file = self.output_manager.save_crawl_results(self.crawl_results)
            
            # 構造分析結果の保存
            analysis_file = self.output_manager.save_structure_analysis(self.analysis_results)
            
            # Fuzzing用データの準備と保存
            fuzzing_data = self._prepare_fuzzing_data()
            fuzzing_file = self.output_manager.save_fuzzing_data(fuzzing_data)
            
            # Fuzzingレポートの作成
            report_file = self.output_manager.create_fuzzing_report(
                self.crawl_results, self.analysis_results
            )
            
            # セッションデータの保存
            session_snapshot = self.session_manager.create_reproducible_snapshot()
            session_file = self.output_manager.save_session_data(session_snapshot)
            
            # ログの保存
            log_file = self.output_manager.save_logs(self.logger.get_logs())
            
            # 最終結果の構築
            final_results = {
                'session_id': self.session_id,
                'status': 'completed',
                'timestamp': time.time(),
                'target_url': self.config.target_url,
                'crawl_summary': self.crawl_results.get('summary', {}),
                'analysis_summary': self.analysis_results.get('summary', {}),
                'output_files': {
                    'html_files': html_files,
                    'frame_files': frame_files,
                    'crawl_results': crawl_results_file,
                    'analysis_results': analysis_file,
                    'fuzzing_data': fuzzing_file,
                    'fuzzing_report': report_file,
                    'session_data': session_file,
                    'logs': log_file
                },
                'fuzzing_readiness': self._assess_fuzzing_readiness(),
                'recommendations': self._generate_recommendations()
            }
            
            self.logger.info("Results saved and finalized successfully")
            return final_results
            
        except Exception as e:
            self.logger.error(f"Error saving results: {str(e)}")
            return self._create_error_result(f"Error saving results: {str(e)}")
    
    def _prepare_fuzzing_data(self) -> Dict[str, Any]:
        """Fuzzing用データの準備"""
        fuzzing_data = {
            'session_id': self.session_id,
            'target_info': {
                'url': self.config.target_url,
                'authentication': {
                    'required': True,
                    'method': 'form_based',
                    'username': self.config.username,
                    'password': self.config.password
                }
            },
            'endpoints': [],
            'parameters': [],
            'forms': [],
            'session_data': self.session_manager.create_reproducible_snapshot(),
            'attack_surface': self.analysis_results.get('fuzzing_preparation', {})
        }
        
        # エンドポイント情報の抽出
        for url_struct in self.analysis_results.get('url_structures', []):
            endpoint_info = {
                'url': url_struct.get('url'),
                'type': url_struct.get('endpoint_type'),
                'is_api': url_struct.get('is_api_endpoint'),
                'path_segments': url_struct.get('path_segments'),
                'query_params': url_struct.get('query_params'),
                'file_extension': url_struct.get('file_extension')
            }
            fuzzing_data['endpoints'].append(endpoint_info)
        
        # フォーム情報の抽出
        fuzzing_data['forms'] = self.page_crawler.get_form_data()
        
        # パラメータ情報の抽出
        for ctx in self.analysis_results.get('security_contexts', []):
            for param in ctx.get('sensitive_parameters', []):
                param_info = {
                    'url': ctx.get('url'),
                    'name': param.get('name'),
                    'type': param.get('type'),
                    'element': param.get('element'),
                    'xpath': param.get('xpath'),
                    'security_relevant': True
                }
                fuzzing_data['parameters'].append(param_info)
        
        return fuzzing_data
    
    def _assess_fuzzing_readiness(self) -> Dict[str, Any]:
        """Fuzzing準備状況の評価"""
        summary = self.crawl_results.get('summary', {})
        analysis_summary = self.analysis_results.get('summary', {})
        
        readiness_score = 0
        max_score = 100
        
        # ページ数による評価
        page_count = summary.get('total_pages', 0)
        readiness_score += min(page_count * 5, 25)
        
        # フォーム数による評価
        form_count = summary.get('total_forms', 0)
        readiness_score += min(form_count * 10, 20)
        
        # エンドポイントタイプによる評価
        endpoint_types = analysis_summary.get('endpoint_types', {})
        if endpoint_types.get('config', 0) > 0:
            readiness_score += 20
        if endpoint_types.get('action', 0) > 0:
            readiness_score += 15
        if endpoint_types.get('api', 0) > 0:
            readiness_score += 10
        
        # セキュリティコンテキストによる評価
        security_issues = len(analysis_summary.get('security_issues', {}))
        readiness_score += min(security_issues * 2, 10)
        
        readiness_level = "Low"
        if readiness_score >= 70:
            readiness_level = "High"
        elif readiness_score >= 40:
            readiness_level = "Medium"
        
        return {
            'score': min(readiness_score, max_score),
            'level': readiness_level,
            'factors': {
                'page_coverage': page_count,
                'form_coverage': form_count,
                'endpoint_diversity': len(endpoint_types),
                'security_context': security_issues
            }
        }
    
    def _generate_recommendations(self) -> List[str]:
        """推奨事項の生成"""
        recommendations = []
        
        summary = self.crawl_results.get('summary', {})
        analysis_summary = self.analysis_results.get('summary', {})
        
        # ページカバレッジに基づく推奨
        if summary.get('total_pages', 0) < 5:
            recommendations.append("Consider increasing crawl depth to discover more pages")
        
        # フォームに基づく推奨
        if summary.get('total_forms', 0) == 0:
            recommendations.append("No forms discovered - verify authentication and page access")
        
        # セキュリティに基づく推奨
        security_issues = analysis_summary.get('security_issues', {})
        if 'potential_csrf_missing_token' in security_issues:
            recommendations.append("CSRF vulnerabilities detected - prioritize CSRF testing")
        
        if 'potential_sqli_get_params' in security_issues:
            recommendations.append("SQL injection vectors found - focus on parameter fuzzing")
        
        # エンドポイントに基づく推奨
        endpoint_types = analysis_summary.get('endpoint_types', {})
        if endpoint_types.get('config', 0) > 0:
            recommendations.append("Configuration endpoints found - test for unauthorized access")
        
        if endpoint_types.get('action', 0) > 0:
            recommendations.append("Action endpoints detected - verify authentication requirements")
        
        return recommendations
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """エラー結果の作成"""
        return {
            'session_id': self.session_id,
            'status': 'error',
            'error': error_message,
            'timestamp': time.time(),
            'target_url': self.config.target_url,
            'logs': self.logger.get_logs()
        }
    
    def _cleanup(self):
        """リソースのクリーンアップ"""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("WebDriver closed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    def restore_session(self, session_file: str) -> bool:
        """セッションの復元"""
        self.logger.info(f"Restoring session from: {session_file}")
        
        try:
            session = self.session_manager.load_session(session_file)
            if not session:
                return False
            
            # セッションの再現
            success = self.session_manager.replay_session(session)
            
            if success:
                self.logger.info("Session restored successfully")
            else:
                self.logger.error("Session restoration failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error restoring session: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """現在の状態取得"""
        return {
            'session_id': self.session_id,
            'initialized': self.driver is not None,
            'authenticated': getattr(self.authenticator, 'authenticated', False) if self.authenticator else False,
            'pages_crawled': len(self.page_crawler.get_pages_data()) if self.page_crawler else 0,
            'frames_crawled': len(self.page_crawler.get_frames_data()) if self.page_crawler else 0,
            'target_url': self.config.target_url
        }

def create_iot_crawler(target_url: str = None, username: str = None, 
                      password: str = None, verbose: bool = False) -> IoTMainCrawler:
    """IoTクローラーのファクトリー関数"""
    config = load_config_from_env()
    
    if target_url:
        config.target_url = target_url
    if username:
        config.username = username
    if password:
        config.password = password
    
    return IoTMainCrawler(config, verbose)