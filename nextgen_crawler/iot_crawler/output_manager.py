"""
IoT Device Output Manager Module
クロール結果の保存・出力管理とFuzzing用データ準備
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from pathlib import Path

from .config import CrawlerConfig, CrawlerLogger
from .page_crawler import PageData, FrameData
from .structure_analyzer import URLStructure, SecurityContext

class IoTOutputManager:
    """IoTデバイス出力管理クラス"""
    
    def __init__(self, config: CrawlerConfig, logger: CrawlerLogger):
        self.config = config
        self.logger = logger
        self.session_id = None
        
        # タイムスタンプ付き固有ディレクトリの作成
        timestamp = int(time.time())
        unique_dir_name = f"crawl_session_{timestamp}"
        self.output_dir = Path(config.output_dir) / unique_dir_name
        
        # 出力ディレクトリの作成
        self._create_output_directories()
        
        self.logger.info(f"Created unique output directory: {self.output_dir}")
    
    def _create_output_directories(self):
        """出力ディレクトリ構造の作成"""
        directories = [
            self.output_dir,
            self.output_dir / "html",
            self.output_dir / "frames", 
            self.output_dir / "json",
            self.output_dir / "analysis",
            self.output_dir / "fuzzing",
            self.output_dir / "sessions",
            self.output_dir / "screenshots",
            self.output_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Output directories created at: {self.output_dir}")
    
    def set_session_id(self, session_id: str):
        """セッションIDの設定"""
        self.session_id = session_id
        
        # セッション固有のディレクトリ作成
        if session_id:
            session_dir = self.output_dir / "sessions" / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
    
    def save_page_data(self, pages_data: List[PageData]) -> Dict[str, str]:
        """ページデータの保存"""
        self.logger.info(f"Saving {len(pages_data)} pages")
        
        saved_files = {}
        
        for page in pages_data:
            try:
                # HTMLファイルの保存
                if self.config.save_html:
                    html_filename = self._generate_html_filename(page.url)
                    html_path = self.output_dir / "html" / html_filename
                    
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(page.html_content)
                    
                    saved_files[page.url] = str(html_path)
                    self.logger.debug(f"Saved HTML: {html_path}")
                
            except Exception as e:
                self.logger.error(f"Error saving page {page.url}: {str(e)}")
                continue
        
        return saved_files
    
    def save_frame_data(self, frames_data: List[FrameData]) -> Dict[str, str]:
        """フレームデータの保存"""
        self.logger.info(f"Saving {len(frames_data)} frames")
        
        saved_files = {}
        
        for frame in frames_data:
            try:
                # フレームHTMLファイルの保存
                frame_filename = self._generate_frame_filename(frame.name, frame.parent_url, frame.index)
                frame_path = self.output_dir / "frames" / frame_filename
                
                with open(frame_path, 'w', encoding='utf-8') as f:
                    f.write(frame.content)
                
                saved_files[f"{frame.parent_url}#{frame.name}"] = str(frame_path)
                self.logger.debug(f"Saved frame: {frame_path}")
                
            except Exception as e:
                self.logger.error(f"Error saving frame {frame.name}: {str(e)}")
                continue
        
        return saved_files
    
    def save_crawl_results(self, crawl_results: Dict[str, Any]) -> str:
        """クロール結果の総合保存"""
        self.logger.info("Saving comprehensive crawl results")
        
        try:
            # タイムスタンプ付きファイル名
            timestamp = int(time.time())
            results_filename = f"crawl_results_{timestamp}.json"
            results_path = self.output_dir / "json" / results_filename
            
            # 結果データの準備
            output_data = {
                'metadata': {
                    'session_id': self.session_id,
                    'timestamp': timestamp,
                    'crawler_version': '1.0',
                    'target_url': self.config.target_url,
                    'crawl_config': self._get_crawl_config_summary()
                },
                'results': crawl_results
            }
            
            # JSON保存
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Crawl results saved: {results_path}")
            return str(results_path)
            
        except Exception as e:
            self.logger.error(f"Error saving crawl results: {str(e)}")
            return ""
    
    def save_structure_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """構造分析結果の保存"""
        self.logger.info("Saving structure analysis")
        
        try:
            timestamp = int(time.time())
            analysis_filename = f"structure_analysis_{timestamp}.json"
            analysis_path = self.output_dir / "analysis" / analysis_filename
            
            # 分析データの準備
            output_data = {
                'metadata': {
                    'session_id': self.session_id,
                    'timestamp': timestamp,
                    'analysis_type': 'structure_analysis',
                    'target_url': self.config.target_url
                },
                'analysis': analysis_data
            }
            
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Structure analysis saved: {analysis_path}")
            return str(analysis_path)
            
        except Exception as e:
            self.logger.error(f"Error saving structure analysis: {str(e)}")
            return ""
    
    def save_fuzzing_data(self, fuzzing_data: Dict[str, Any]) -> str:
        """Fuzzing用データの保存"""
        self.logger.info("Saving fuzzing preparation data")
        
        try:
            timestamp = int(time.time())
            fuzzing_filename = f"fuzzing_data_{timestamp}.json"
            fuzzing_path = self.output_dir / "fuzzing" / fuzzing_filename
            
            # Fuzzing用データの準備
            output_data = {
                'metadata': {
                    'session_id': self.session_id,
                    'timestamp': timestamp,
                    'data_type': 'fuzzing_preparation',
                    'target_url': self.config.target_url,
                    'generation_config': {
                        'max_depth': self.config.max_depth,
                        'extract_forms': self.config.extract_forms,
                        'extract_links': self.config.extract_links
                    }
                },
                'fuzzing_data': fuzzing_data
            }
            
            with open(fuzzing_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Fuzzing data saved: {fuzzing_path}")
            return str(fuzzing_path)
            
        except Exception as e:
            self.logger.error(f"Error saving fuzzing data: {str(e)}")
            return ""
    
    def save_session_data(self, session_data: Dict[str, Any]) -> str:
        """セッションデータの保存"""
        if not self.session_id:
            self.logger.warning("No session ID set for session data saving")
            return ""
        
        try:
            session_filename = f"session_{self.session_id}.json"
            session_path = self.output_dir / "sessions" / self.session_id / session_filename
            
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Session data saved: {session_path}")
            return str(session_path)
            
        except Exception as e:
            self.logger.error(f"Error saving session data: {str(e)}")
            return ""
    
    def save_logs(self, logs: List[str]) -> str:
        """ログの保存"""
        try:
            timestamp = int(time.time())
            log_filename = f"crawler_log_{timestamp}.txt"
            log_path = self.output_dir / "logs" / log_filename
            
            with open(log_path, 'w', encoding='utf-8') as f:
                for log_entry in logs:
                    f.write(log_entry + '\n')
            
            self.logger.info(f"Logs saved: {log_path}")
            return str(log_path)
            
        except Exception as e:
            self.logger.error(f"Error saving logs: {str(e)}")
            return ""
    
    def create_fuzzing_report(self, crawl_results: Dict[str, Any], 
                             analysis_data: Dict[str, Any]) -> str:
        """Fuzzing用レポートの作成"""
        self.logger.info("Creating fuzzing report")
        
        try:
            timestamp = int(time.time())
            report_filename = f"fuzzing_report_{timestamp}.json"
            report_path = self.output_dir / "fuzzing" / report_filename
            
            # Fuzzing準備レポートの作成
            report_data = {
                'metadata': {
                    'session_id': self.session_id,
                    'timestamp': timestamp,
                    'target_url': self.config.target_url,
                    'report_type': 'fuzzing_preparation'
                },
                'executive_summary': self._create_executive_summary(crawl_results, analysis_data),
                'target_analysis': self._create_target_analysis(crawl_results, analysis_data),
                'attack_surface': self._create_attack_surface_analysis(analysis_data),
                'fuzzing_recommendations': self._create_fuzzing_recommendations(analysis_data),
                'reproduction_data': self._create_reproduction_data(crawl_results)
            }
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Fuzzing report created: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Error creating fuzzing report: {str(e)}")
            return ""
    
    def _create_executive_summary(self, crawl_results: Dict[str, Any], 
                                 analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """実行要約の作成"""
        summary = crawl_results.get('summary', {})
        analysis_summary = analysis_data.get('summary', {})
        
        return {
            'total_pages_crawled': summary.get('total_pages', 0),
            'total_frames_analyzed': summary.get('total_frames', 0),
            'total_forms_found': summary.get('total_forms', 0),
            'total_links_discovered': summary.get('total_links', 0),
            'crawl_depth_achieved': summary.get('crawl_depth', 0),
            'endpoint_distribution': analysis_summary.get('endpoint_types', {}),
            'security_issues_identified': len(analysis_summary.get('security_issues', {})),
            'fuzzing_readiness_score': self._calculate_fuzzing_readiness_score(analysis_data)
        }
    
    def _create_target_analysis(self, crawl_results: Dict[str, Any], 
                               analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """ターゲット分析の作成"""
        return {
            'device_type': 'IoT Router',
            'web_interface_type': 'Frameset-based',
            'authentication_method': 'Form-based',
            'session_management': 'Cookie-based',
            'identified_technologies': self._identify_technologies(crawl_results),
            'api_endpoints': [
                struct for struct in analysis_data.get('url_structures', [])
                if struct.get('is_api_endpoint', False)
            ],
            'configuration_endpoints': [
                struct for struct in analysis_data.get('url_structures', [])
                if struct.get('endpoint_type') == 'config'
            ]
        }
    
    def _create_attack_surface_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """攻撃面分析の作成"""
        security_contexts = analysis_data.get('security_contexts', [])
        
        input_points = []
        csrf_protection = []
        potential_vulnerabilities = []
        
        for ctx in security_contexts:
            # 入力ポイントの集約
            input_points.extend(ctx.get('sensitive_parameters', []))
            
            # CSRF保護の状況
            csrf_protection.append({
                'url': ctx.get('url'),
                'protected': ctx.get('csrf_tokens_count', 0) > 0,
                'token_count': ctx.get('csrf_tokens_count', 0)
            })
            
            # 脆弱性の集約
            potential_vulnerabilities.extend(ctx.get('potential_vulnerabilities', []))
        
        return {
            'total_input_points': len(input_points),
            'input_points_by_type': self._categorize_input_points(input_points),
            'csrf_protection_status': csrf_protection,
            'potential_vulnerabilities': list(set(potential_vulnerabilities)),
            'vulnerability_distribution': self._count_vulnerabilities(potential_vulnerabilities),
            'high_risk_endpoints': self._identify_high_risk_endpoints(security_contexts)
        }
    
    def _create_fuzzing_recommendations(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fuzzing推奨事項の作成"""
        fuzzing_prep = analysis_data.get('fuzzing_preparation', {})
        
        return {
            'primary_targets': {
                'config_endpoints': fuzzing_prep.get('config_endpoints', 0),
                'action_endpoints': fuzzing_prep.get('action_endpoints', 0),
                'api_endpoints': fuzzing_prep.get('api_endpoints', 0)
            },
            'fuzzing_strategies': self._recommend_fuzzing_strategies(analysis_data),
            'parameter_fuzzing': {
                'total_parameters': fuzzing_prep.get('total_parameters', 0),
                'input_points': fuzzing_prep.get('total_input_points', 0),
                'csrf_tokens': fuzzing_prep.get('total_csrf_tokens', 0)
            },
            'session_handling': {
                'authentication_required': True,
                'session_management': 'cookie_based',
                'csrf_protection': fuzzing_prep.get('total_csrf_tokens', 0) > 0
            }
        }
    
    def _create_reproduction_data(self, crawl_results: Dict[str, Any]) -> Dict[str, Any]:
        """再現データの作成"""
        return {
            'crawl_sequence': crawl_results.get('pages', []),
            'frame_structure': crawl_results.get('frames', []),
            'form_data': crawl_results.get('forms', []),
            'url_structure': crawl_results.get('url_structure', {}),
            'link_relationships': crawl_results.get('link_map', {})
        }
    
    def _generate_html_filename(self, url: str) -> str:
        """HTMLファイル名の生成"""
        # URLを安全なファイル名に変換
        safe_url = url.replace('://', '_').replace('/', '_').replace('?', '_').replace('&', '_')
        safe_url = safe_url.replace('=', '_').replace('#', '_').replace(':', '_')
        
        # 長すぎる場合はハッシュを使用
        if len(safe_url) > 100:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            safe_url = safe_url[:50] + '_' + url_hash
        
        return f"{safe_url}.html"
    
    def _generate_frame_filename(self, frame_name: str, parent_url: str, index: int) -> str:
        """フレームファイル名の生成"""
        parent_safe = parent_url.replace('://', '_').replace('/', '_').replace('?', '_')
        if len(parent_safe) > 50:
            parent_safe = parent_safe[:50]
        
        frame_safe = frame_name.replace('/', '_').replace('?', '_')
        return f"{parent_safe}_{frame_safe}_{index}.html"
    
    def _get_crawl_config_summary(self) -> Dict[str, Any]:
        """クロール設定の要約"""
        return {
            'max_depth': self.config.max_depth,
            'page_load_timeout': self.config.page_load_timeout,
            'element_wait_timeout': self.config.element_wait_timeout,
            'crawl_frames': self.config.crawl_frames,
            'extract_forms': self.config.extract_forms,
            'extract_links': self.config.extract_links,
            'follow_external_links': self.config.follow_external_links
        }
    
    def _calculate_fuzzing_readiness_score(self, analysis_data: Dict[str, Any]) -> float:
        """Fuzzing準備スコアの計算"""
        score = 0.0
        max_score = 100.0
        
        fuzzing_prep = analysis_data.get('fuzzing_preparation', {})
        
        # 入力ポイントの数
        input_points = fuzzing_prep.get('total_input_points', 0)
        score += min(input_points * 10, 30)  # 最大30点
        
        # パラメータの数
        parameters = fuzzing_prep.get('total_parameters', 0)
        score += min(parameters * 5, 20)  # 最大20点
        
        # APIエンドポイントの数
        api_endpoints = fuzzing_prep.get('api_endpoints', 0)
        score += min(api_endpoints * 15, 30)  # 最大30点
        
        # 設定エンドポイントの数
        config_endpoints = fuzzing_prep.get('config_endpoints', 0)
        score += min(config_endpoints * 20, 20)  # 最大20点
        
        return min(score, max_score)
    
    def _identify_technologies(self, crawl_results: Dict[str, Any]) -> List[str]:
        """技術スタックの識別"""
        technologies = []
        
        # フレーム構造から推測
        frames = crawl_results.get('frames', [])
        if frames:
            technologies.append('Frameset-based UI')
        
        # フォームから推測
        forms = crawl_results.get('forms', [])
        for form in forms:
            action = form.get('action', '').lower()
            if '.php' in action:
                technologies.append('PHP')
            elif '.cgi' in action:
                technologies.append('CGI')
            elif '.asp' in action:
                technologies.append('ASP')
        
        return list(set(technologies))
    
    def _categorize_input_points(self, input_points: List[Dict[str, Any]]) -> Dict[str, int]:
        """入力ポイントのカテゴリ分け"""
        categories = {}
        
        for point in input_points:
            point_type = point.get('type', 'unknown')
            categories[point_type] = categories.get(point_type, 0) + 1
        
        return categories
    
    def _count_vulnerabilities(self, vulnerabilities: List[str]) -> Dict[str, int]:
        """脆弱性の集計"""
        counts = {}
        for vuln in vulnerabilities:
            counts[vuln] = counts.get(vuln, 0) + 1
        return counts
    
    def _identify_high_risk_endpoints(self, security_contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """高リスクエンドポイントの識別"""
        high_risk = []
        
        for ctx in security_contexts:
            risk_score = 0
            
            # 脆弱性の数でスコア計算
            vulns = ctx.get('potential_vulnerabilities', [])
            risk_score += len(vulns) * 10
            
            # 機密パラメータの数
            sensitive_params = ctx.get('sensitive_parameters_count', 0)
            risk_score += sensitive_params * 5
            
            # CSRF保護の欠如
            if ctx.get('csrf_tokens_count', 0) == 0:
                risk_score += 20
            
            if risk_score >= 30:  # 閾値
                high_risk.append({
                    'url': ctx.get('url'),
                    'risk_score': risk_score,
                    'vulnerabilities': vulns,
                    'reasons': self._get_risk_reasons(ctx)
                })
        
        return sorted(high_risk, key=lambda x: x['risk_score'], reverse=True)
    
    def _get_risk_reasons(self, ctx: Dict[str, Any]) -> List[str]:
        """リスク理由の取得"""
        reasons = []
        
        if ctx.get('potential_vulnerabilities'):
            reasons.append('Potential vulnerabilities detected')
        
        if ctx.get('sensitive_parameters_count', 0) > 0:
            reasons.append('Sensitive parameters present')
        
        if ctx.get('csrf_tokens_count', 0) == 0:
            reasons.append('Missing CSRF protection')
        
        return reasons
    
    def _recommend_fuzzing_strategies(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Fuzzing戦略の推奨"""
        strategies = []
        
        fuzzing_prep = analysis_data.get('fuzzing_preparation', {})
        
        if fuzzing_prep.get('config_endpoints', 0) > 0:
            strategies.append('Configuration parameter fuzzing')
        
        if fuzzing_prep.get('action_endpoints', 0) > 0:
            strategies.append('Action endpoint fuzzing')
        
        if fuzzing_prep.get('api_endpoints', 0) > 0:
            strategies.append('API endpoint fuzzing')
        
        if fuzzing_prep.get('total_input_points', 0) > 0:
            strategies.append('Input validation fuzzing')
        
        security_issues = analysis_data.get('summary', {}).get('security_issues', {})
        if 'potential_sqli_get_params' in security_issues:
            strategies.append('SQL injection fuzzing')
        
        if 'potential_xss_innerhtml' in security_issues:
            strategies.append('XSS fuzzing')
        
        return strategies
    
    def get_output_summary(self) -> Dict[str, Any]:
        """出力結果の要約"""
        return {
            'output_directory': str(self.output_dir),
            'session_id': self.session_id,
            'directories_created': [
                'html', 'frames', 'json', 'analysis', 
                'fuzzing', 'sessions', 'screenshots', 'logs'
            ],
            'file_counts': self._count_output_files()
        }
    
    def _count_output_files(self) -> Dict[str, int]:
        """出力ファイル数の集計"""
        counts = {}
        
        for subdir in ['html', 'frames', 'json', 'analysis', 'fuzzing', 'sessions', 'logs']:
            dir_path = self.output_dir / subdir
            if dir_path.exists():
                counts[subdir] = len(list(dir_path.glob('*')))
            else:
                counts[subdir] = 0
        
        return counts