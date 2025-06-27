"""
IoT Device Structure Analyzer Module
DOM構造とURL構造の詳細分析とFuzzing用データ準備
"""

import re
import json
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from urllib.parse import urlparse, parse_qs, urljoin
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

from .config import CrawlerConfig, CrawlerLogger

@dataclass
class DOMElement:
    """DOM要素データクラス"""
    tag: str
    attributes: Dict[str, str]
    text_content: str
    xpath: str
    css_selector: str
    parent_xpath: str
    children_count: int
    depth: int
    is_interactive: bool
    security_relevant: bool

@dataclass
class URLStructure:
    """URL構造データクラス"""
    url: str
    scheme: str
    netloc: str
    path: str
    params: str
    query: str
    fragment: str
    path_segments: List[str]
    query_params: Dict[str, List[str]]
    file_extension: Optional[str]
    is_api_endpoint: bool
    endpoint_type: str  # 'config', 'status', 'action', 'data', 'unknown'

@dataclass
class SecurityContext:
    """セキュリティコンテキストデータクラス"""
    url: str
    authentication_required: bool
    csrf_tokens: List[str]
    session_identifiers: List[str]
    sensitive_parameters: List[str]
    input_validation_points: List[Dict[str, Any]]
    potential_vulnerabilities: List[str]

class IoTStructureAnalyzer:
    """IoTデバイス構造分析クラス"""
    
    def __init__(self, driver: webdriver.Chrome, config: CrawlerConfig, logger: CrawlerLogger):
        self.driver = driver
        self.config = config
        self.logger = logger
        
        # 分析結果データ
        self.dom_elements: Dict[str, List[DOMElement]] = {}  # URL -> elements
        self.url_structures: List[URLStructure] = []
        self.security_contexts: List[SecurityContext] = []
        
        # IoTデバイス固有のパターン
        self.iot_patterns = {
            'config_endpoints': [
                r'config', r'setup', r'settings', r'admin', r'management',
                r'network', r'wireless', r'security', r'firewall'
            ],
            'status_endpoints': [
                r'status', r'info', r'stats', r'monitor', r'health',
                r'system', r'device', r'hardware'
            ],
            'action_endpoints': [
                r'reboot', r'reset', r'restart', r'update', r'upgrade',
                r'backup', r'restore', r'apply', r'save'
            ],
            'data_endpoints': [
                r'log', r'event', r'history', r'report', r'data',
                r'export', r'download'
            ],
            'sensitive_params': [
                'password', 'passwd', 'pass', 'secret', 'key', 'token',
                'session', 'auth', 'credential', 'login', 'username'
            ],
            'csrf_indicators': [
                'csrf', 'token', 'nonce', '_token', 'authenticity_token',
                'security_token', 'form_token'
            ]
        }
    
    def analyze_page_structure(self, url: str, html_content: str) -> Dict[str, Any]:
        """ページ構造の包括的分析"""
        self.logger.debug(f"Analyzing structure for: {url}")
        
        try:
            # URL構造分析
            url_structure = self._analyze_url_structure(url)
            self.url_structures.append(url_structure)
            
            # DOM構造分析
            dom_elements = self._analyze_dom_structure(url, html_content)
            self.dom_elements[url] = dom_elements
            
            # セキュリティコンテキスト分析
            security_context = self._analyze_security_context(url, html_content, dom_elements)
            self.security_contexts.append(security_context)
            
            # Fuzzing用データ準備
            fuzzing_data = self._prepare_fuzzing_data(url, url_structure, dom_elements, security_context)
            
            return {
                'url_structure': url_structure,
                'dom_elements': dom_elements,
                'security_context': security_context,
                'fuzzing_data': fuzzing_data,
                'analysis_timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing structure for {url}: {str(e)}")
            return {}
    
    def _analyze_url_structure(self, url: str) -> URLStructure:
        """URL構造の詳細分析"""
        parsed = urlparse(url)
        
        # パス分析
        path_segments = [seg for seg in parsed.path.split('/') if seg]
        file_extension = None
        if path_segments:
            last_segment = path_segments[-1]
            if '.' in last_segment:
                file_extension = last_segment.split('.')[-1]
        
        # クエリパラメータ分析
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        
        # エンドポイントタイプの判定
        endpoint_type = self._classify_endpoint_type(url, path_segments)
        
        # API エンドポイントの判定
        is_api_endpoint = self._is_api_endpoint(url, path_segments, file_extension)
        
        return URLStructure(
            url=url,
            scheme=parsed.scheme,
            netloc=parsed.netloc,
            path=parsed.path,
            params=parsed.params,
            query=parsed.query,
            fragment=parsed.fragment,
            path_segments=path_segments,
            query_params=query_params,
            file_extension=file_extension,
            is_api_endpoint=is_api_endpoint,
            endpoint_type=endpoint_type
        )
    
    def _classify_endpoint_type(self, url: str, path_segments: List[str]) -> str:
        """エンドポイントタイプの分類"""
        url_lower = url.lower()
        path_lower = ' '.join(path_segments).lower()
        
        # 設定系
        if any(re.search(pattern, url_lower) for pattern in self.iot_patterns['config_endpoints']):
            return 'config'
        
        # ステータス系
        if any(re.search(pattern, url_lower) for pattern in self.iot_patterns['status_endpoints']):
            return 'status'
        
        # アクション系
        if any(re.search(pattern, url_lower) for pattern in self.iot_patterns['action_endpoints']):
            return 'action'
        
        # データ系
        if any(re.search(pattern, url_lower) for pattern in self.iot_patterns['data_endpoints']):
            return 'data'
        
        return 'unknown'
    
    def _is_api_endpoint(self, url: str, path_segments: List[str], file_extension: Optional[str]) -> bool:
        """APIエンドポイントの判定"""
        # 拡張子による判定
        api_extensions = ['json', 'xml', 'api', 'cgi', 'php', 'asp', 'jsp']
        if file_extension and file_extension.lower() in api_extensions:
            return True
        
        # パスパターンによる判定
        api_patterns = [r'api', r'ajax', r'rest', r'service', r'rpc', r'graphql']
        url_lower = url.lower()
        if any(re.search(pattern, url_lower) for pattern in api_patterns):
            return True
        
        # クエリパラメータによる判定
        api_params = ['action', 'method', 'function', 'cmd', 'command']
        parsed = urlparse(url)
        if parsed.query:
            query_params = parse_qs(parsed.query)
            if any(param in query_params for param in api_params):
                return True
        
        return False
    
    def _analyze_dom_structure(self, url: str, html_content: str) -> List[DOMElement]:
        """DOM構造の詳細分析"""
        elements = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 全要素の分析
            for element in soup.find_all():
                try:
                    dom_element = self._create_dom_element(element, url)
                    if dom_element:
                        elements.append(dom_element)
                except Exception as e:
                    self.logger.debug(f"Error analyzing element: {str(e)}")
                    continue
            
            return elements
            
        except Exception as e:
            self.logger.error(f"Error analyzing DOM for {url}: {str(e)}")
            return []
    
    def _create_dom_element(self, element, url: str) -> Optional[DOMElement]:
        """DOM要素データの作成"""
        try:
            # 基本属性
            tag = element.name
            attributes = dict(element.attrs) if element.attrs else {}
            text_content = element.get_text(strip=True)
            
            # XPath生成（簡略化）
            xpath = self._generate_xpath(element)
            css_selector = self._generate_css_selector(element)
            
            # 親要素のXPath
            parent_xpath = self._generate_xpath(element.parent) if element.parent else ""
            
            # 子要素数
            children_count = len(list(element.children))
            
            # 深度計算
            depth = len(list(element.parents))
            
            # インタラクティブ要素の判定
            is_interactive = self._is_interactive_element(element)
            
            # セキュリティ関連要素の判定
            security_relevant = self._is_security_relevant_element(element)
            
            return DOMElement(
                tag=tag,
                attributes=attributes,
                text_content=text_content,
                xpath=xpath,
                css_selector=css_selector,
                parent_xpath=parent_xpath,
                children_count=children_count,
                depth=depth,
                is_interactive=is_interactive,
                security_relevant=security_relevant
            )
            
        except Exception as e:
            self.logger.debug(f"Error creating DOM element: {str(e)}")
            return None
    
    def _generate_xpath(self, element) -> str:
        """要素のXPath生成"""
        if element is None or element.name is None:
            return ""
        
        path_parts = []
        current = element
        
        while current and current.name:
            siblings = [sibling for sibling in current.parent.children 
                       if sibling.name == current.name] if current.parent else [current]
            
            if len(siblings) == 1:
                path_parts.append(current.name)
            else:
                index = siblings.index(current) + 1
                path_parts.append(f"{current.name}[{index}]")
            
            current = current.parent
        
        path_parts.reverse()
        return "/" + "/".join(path_parts)
    
    def _generate_css_selector(self, element) -> str:
        """要素のCSSセレクター生成"""
        if element is None or element.name is None:
            return ""
        
        selector_parts = []
        current = element
        
        while current and current.name:
            part = current.name
            
            # ID属性があれば使用
            if current.get('id'):
                part = f"{part}#{current['id']}"
                selector_parts.append(part)
                break
            
            # クラス属性があれば使用
            if current.get('class'):
                classes = ' '.join(current['class'])
                part = f"{part}.{classes.replace(' ', '.')}"
            
            selector_parts.append(part)
            current = current.parent
        
        selector_parts.reverse()
        return " > ".join(selector_parts)
    
    def _is_interactive_element(self, element) -> bool:
        """インタラクティブ要素の判定"""
        interactive_tags = ['input', 'button', 'select', 'textarea', 'a', 'form']
        
        if element.name in interactive_tags:
            return True
        
        # クリック可能な要素の検出
        if element.get('onclick') or element.get('href'):
            return True
        
        # role属性による判定
        role = element.get('role')
        if role in ['button', 'link', 'tab', 'menuitem']:
            return True
        
        return False
    
    def _is_security_relevant_element(self, element) -> bool:
        """セキュリティ関連要素の判定"""
        # パスワードフィールド
        if element.name == 'input' and element.get('type') == 'password':
            return True
        
        # 隠しフィールド（CSRFトークンなど）
        if element.name == 'input' and element.get('type') == 'hidden':
            name = element.get('name', '').lower()
            if any(pattern in name for pattern in self.iot_patterns['csrf_indicators']):
                return True
        
        # セキュリティ関連のname/id属性
        name_id = (element.get('name', '') + element.get('id', '')).lower()
        if any(pattern in name_id for pattern in self.iot_patterns['sensitive_params']):
            return True
        
        return False
    
    def _analyze_security_context(self, url: str, html_content: str, 
                                 dom_elements: List[DOMElement]) -> SecurityContext:
        """セキュリティコンテキストの分析"""
        csrf_tokens = []
        session_identifiers = []
        sensitive_parameters = []
        input_validation_points = []
        potential_vulnerabilities = []
        
        # DOM要素からセキュリティ情報を抽出
        for element in dom_elements:
            if element.security_relevant:
                # CSRFトークンの検出
                if element.tag == 'input' and element.attributes.get('type') == 'hidden':
                    name = element.attributes.get('name', '').lower()
                    if any(pattern in name for pattern in self.iot_patterns['csrf_indicators']):
                        csrf_tokens.append({
                            'name': element.attributes.get('name'),
                            'value': element.attributes.get('value'),
                            'xpath': element.xpath
                        })
                
                # 機密パラメータの検出
                name_id = (element.attributes.get('name', '') + 
                          element.attributes.get('id', '')).lower()
                if any(pattern in name_id for pattern in self.iot_patterns['sensitive_params']):
                    sensitive_parameters.append({
                        'element': element.tag,
                        'name': element.attributes.get('name'),
                        'id': element.attributes.get('id'),
                        'type': element.attributes.get('type'),
                        'xpath': element.xpath
                    })
            
            # 入力検証ポイントの検出
            if element.tag == 'input' and element.is_interactive:
                validation_info = self._analyze_input_validation(element)
                if validation_info:
                    input_validation_points.append(validation_info)
        
        # HTMLソースからの追加分析
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # セッション識別子の検出
        session_identifiers = self._extract_session_identifiers(soup)
        
        # 潜在的な脆弱性の検出
        potential_vulnerabilities = self._detect_potential_vulnerabilities(soup, url)
        
        # 認証要求の判定
        authentication_required = self._requires_authentication(soup, url)
        
        return SecurityContext(
            url=url,
            authentication_required=authentication_required,
            csrf_tokens=csrf_tokens,
            session_identifiers=session_identifiers,
            sensitive_parameters=sensitive_parameters,
            input_validation_points=input_validation_points,
            potential_vulnerabilities=potential_vulnerabilities
        )
    
    def _analyze_input_validation(self, element: DOMElement) -> Optional[Dict[str, Any]]:
        """入力検証の分析"""
        validation_info = {
            'xpath': element.xpath,
            'name': element.attributes.get('name'),
            'type': element.attributes.get('type', 'text'),
            'validation_attributes': {},
            'constraints': []
        }
        
        # HTML5検証属性
        validation_attrs = ['required', 'pattern', 'min', 'max', 'minlength', 'maxlength', 'step']
        for attr in validation_attrs:
            if attr in element.attributes:
                validation_info['validation_attributes'][attr] = element.attributes[attr]
        
        # 制約の分析
        if 'pattern' in element.attributes:
            validation_info['constraints'].append({
                'type': 'regex',
                'value': element.attributes['pattern']
            })
        
        if 'maxlength' in element.attributes:
            validation_info['constraints'].append({
                'type': 'max_length',
                'value': element.attributes['maxlength']
            })
        
        return validation_info if validation_info['validation_attributes'] or validation_info['constraints'] else None
    
    def _extract_session_identifiers(self, soup: BeautifulSoup) -> List[str]:
        """セッション識別子の抽出"""
        session_identifiers = []
        
        # Cookie名から推測
        # 実際のCookieは別途Seleniumで取得する必要がある
        
        # JavaScript内のセッション情報
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # セッション関連の変数を検索
                session_patterns = [
                    r'sessionId["\']?\s*[=:]\s*["\']([^"\']+)["\']',
                    r'PHPSESSID["\']?\s*[=:]\s*["\']([^"\']+)["\']',
                    r'session["\']?\s*[=:]\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in session_patterns:
                    matches = re.findall(pattern, script.string, re.IGNORECASE)
                    session_identifiers.extend(matches)
        
        return list(set(session_identifiers))
    
    def _detect_potential_vulnerabilities(self, soup: BeautifulSoup, url: str) -> List[str]:
        """潜在的な脆弱性の検出"""
        vulnerabilities = []
        
        # XSS関連
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'eval(' in script.string:
                vulnerabilities.append('potential_xss_eval')
            if script.string and 'innerHTML' in script.string:
                vulnerabilities.append('potential_xss_innerhtml')
        
        # CSRF関連
        forms = soup.find_all('form')
        for form in forms:
            if form.get('method', '').upper() == 'POST':
                # CSRFトークンの有無を確認
                has_csrf = any(
                    inp.get('name', '').lower() in ['csrf', 'token', '_token']
                    for inp in form.find_all('input', type='hidden')
                )
                if not has_csrf:
                    vulnerabilities.append('potential_csrf_missing_token')
        
        # SQLインジェクション関連
        if any(param in url.lower() for param in ['id=', 'user=', 'page=', 'item=']):
            vulnerabilities.append('potential_sqli_get_params')
        
        # パストラバーサル関連
        if any(param in url.lower() for param in ['file=', 'path=', 'dir=', 'include=']):
            vulnerabilities.append('potential_path_traversal')
        
        # デフォルトクレデンシャル
        if 'admin' in url.lower() or 'login' in url.lower():
            vulnerabilities.append('potential_default_credentials')
        
        return list(set(vulnerabilities))
    
    def _requires_authentication(self, soup: BeautifulSoup, url: str) -> bool:
        """認証要求の判定"""
        # ログインフォームの存在
        login_indicators = soup.find_all(['input'], attrs={'type': 'password'})
        if login_indicators:
            return True
        
        # URLパターンによる判定
        auth_patterns = ['login', 'auth', 'signin', 'admin']
        if any(pattern in url.lower() for pattern in auth_patterns):
            return True
        
        return False
    
    def _prepare_fuzzing_data(self, url: str, url_structure: URLStructure, 
                             dom_elements: List[DOMElement], 
                             security_context: SecurityContext) -> Dict[str, Any]:
        """Fuzzing用データの準備"""
        fuzzing_data = {
            'target_url': url,
            'endpoint_type': url_structure.endpoint_type,
            'is_api_endpoint': url_structure.is_api_endpoint,
            'input_points': [],
            'parameters': {},
            'csrf_tokens': security_context.csrf_tokens,
            'session_requirements': security_context.session_identifiers,
            'validation_constraints': security_context.input_validation_points,
            'potential_attack_vectors': security_context.potential_vulnerabilities
        }
        
        # 入力ポイントの抽出
        for element in dom_elements:
            if element.is_interactive and element.tag in ['input', 'select', 'textarea']:
                input_point = {
                    'type': element.tag,
                    'name': element.attributes.get('name'),
                    'id': element.attributes.get('id'),
                    'input_type': element.attributes.get('type', 'text'),
                    'xpath': element.xpath,
                    'css_selector': element.css_selector,
                    'required': 'required' in element.attributes,
                    'security_relevant': element.security_relevant
                }
                fuzzing_data['input_points'].append(input_point)
        
        # URLパラメータの抽出
        for param, values in url_structure.query_params.items():
            fuzzing_data['parameters'][param] = {
                'values': values,
                'type': 'query_param',
                'sensitive': param.lower() in self.iot_patterns['sensitive_params']
            }
        
        return fuzzing_data
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """包括的な分析結果の取得"""
        return {
            'summary': {
                'total_urls': len(self.url_structures),
                'total_dom_elements': sum(len(elements) for elements in self.dom_elements.values()),
                'total_security_contexts': len(self.security_contexts),
                'endpoint_types': self._get_endpoint_type_distribution(),
                'security_issues': self._get_security_issue_summary()
            },
            'url_structures': [
                {
                    'url': struct.url,
                    'endpoint_type': struct.endpoint_type,
                    'is_api_endpoint': struct.is_api_endpoint,
                    'path_segments': struct.path_segments,
                    'query_params': struct.query_params,
                    'file_extension': struct.file_extension
                }
                for struct in self.url_structures
            ],
            'security_contexts': [
                {
                    'url': ctx.url,
                    'authentication_required': ctx.authentication_required,
                    'csrf_tokens_count': len(ctx.csrf_tokens),
                    'sensitive_parameters_count': len(ctx.sensitive_parameters),
                    'potential_vulnerabilities': ctx.potential_vulnerabilities
                }
                for ctx in self.security_contexts
            ],
            'fuzzing_preparation': self._get_fuzzing_preparation_summary()
        }
    
    def _get_endpoint_type_distribution(self) -> Dict[str, int]:
        """エンドポイントタイプの分布"""
        distribution = {}
        for struct in self.url_structures:
            endpoint_type = struct.endpoint_type
            distribution[endpoint_type] = distribution.get(endpoint_type, 0) + 1
        return distribution
    
    def _get_security_issue_summary(self) -> Dict[str, int]:
        """セキュリティ問題の要約"""
        all_vulnerabilities = []
        for ctx in self.security_contexts:
            all_vulnerabilities.extend(ctx.potential_vulnerabilities)
        
        summary = {}
        for vuln in all_vulnerabilities:
            summary[vuln] = summary.get(vuln, 0) + 1
        
        return summary
    
    def _get_fuzzing_preparation_summary(self) -> Dict[str, Any]:
        """Fuzzing準備の要約"""
        total_input_points = 0
        total_parameters = 0
        total_csrf_tokens = 0
        
        for ctx in self.security_contexts:
            total_input_points += len(ctx.input_validation_points)
            total_csrf_tokens += len(ctx.csrf_tokens)
        
        for struct in self.url_structures:
            total_parameters += len(struct.query_params)
        
        return {
            'total_input_points': total_input_points,
            'total_parameters': total_parameters,
            'total_csrf_tokens': total_csrf_tokens,
            'api_endpoints': sum(1 for struct in self.url_structures if struct.is_api_endpoint),
            'config_endpoints': sum(1 for struct in self.url_structures if struct.endpoint_type == 'config'),
            'action_endpoints': sum(1 for struct in self.url_structures if struct.endpoint_type == 'action')
        }