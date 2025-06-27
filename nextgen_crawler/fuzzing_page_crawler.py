#!/usr/bin/env python3
"""
Fuzzing-Oriented Post-Login Page Crawler
ログイン後のFuzzing準備に特化したページクローラー

このモジュールは、IoTデバイスへのログイン後に以下を実行します：
1. 全ページ・エンドポイントの網羅的発見
2. 各ページの状態変化の記録
3. Fuzzing対象となる入力ポイントの詳細分析
4. セッション状態の完全キャプチャ
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

sys.path.append('./iot_crawler')
from iot_crawler.main_crawler import create_iot_crawler
from iot_crawler.config import CrawlerConfig

# ログ設定
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PageState:
    """ページ状態の詳細記録"""
    url: str
    title: str
    timestamp: float
    page_hash: str
    forms: List[Dict]
    links: List[str]
    inputs: List[Dict]
    frames: List[Dict]
    cookies: List[Dict]
    local_storage: Dict
    session_storage: Dict
    javascript_vars: Dict
    dom_structure_hash: str
    security_tokens: List[str]

@dataclass
class FuzzingTarget:
    """Fuzzing対象の詳細情報"""
    endpoint: str
    method: str
    parameters: List[Dict]
    csrf_tokens: List[str]
    authentication_required: bool
    session_dependent: bool
    priority_score: int
    vulnerability_indicators: List[str]

class FuzzingPageCrawler:
    """Fuzzing準備に特化したページクローラー"""
    
    def __init__(self, target_url: str, username: str = "admin", password: str = "password"):
        self.target_url = target_url
        self.username = username
        self.password = password
        
        # 基本クローラーの初期化
        self.crawler = create_iot_crawler(
            target_url=target_url,
            username=username,
            password=password,
            verbose=True
        )
        
        # 状態管理
        self.visited_pages: Set[str] = set()
        self.page_states: List[PageState] = []
        self.fuzzing_targets: List[FuzzingTarget] = []
        self.navigation_paths: List[List[str]] = []
        self.session_changes: List[Dict] = []
        
        # 設定
        self.max_depth = 15  # より深いクローリング
        self.max_pages = 100  # 最大ページ数
        self.wait_time = 2    # ページ間待機時間
        
    def initialize(self) -> bool:
        """クローラーの初期化"""
        logger.info("🔧 Initializing Fuzzing Page Crawler")
        return self.crawler.initialize()
    
    def run_comprehensive_crawl(self) -> Dict[str, Any]:
        """包括的なログイン後クローリングの実行"""
        logger.info("🚀 Starting Comprehensive Post-Login Crawl")
        
        try:
            # 1. 認証実行
            if not self._perform_authentication():
                return {"status": "error", "message": "Authentication failed"}
            
            # 2. 初期状態の記録
            initial_state = self._capture_page_state(self.target_url, "Initial authenticated state")
            self.page_states.append(initial_state)
            
            # 3. 包括的ページ発見
            discovered_pages = self._discover_all_pages()
            logger.info(f"📊 Discovered {len(discovered_pages)} unique pages")
            
            # 4. 各ページの詳細分析
            for page_url in discovered_pages:
                self._analyze_page_for_fuzzing(page_url)
                time.sleep(self.wait_time)
            
            # 5. ナビゲーションパスの分析
            self._analyze_navigation_paths()
            
            # 6. Fuzzing対象の優先度付け
            self._prioritize_fuzzing_targets()
            
            # 7. 結果の生成
            results = self._generate_fuzzing_results()
            
            logger.info("✅ Comprehensive crawl completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"❌ Crawl failed: {str(e)}")
            return {"status": "error", "message": str(e)}
        
        finally:
            self.cleanup()
    
    def _perform_authentication(self) -> bool:
        """認証の実行（改良版）"""
        logger.info("🔐 Performing authentication")
        
        try:
            # ページにアクセス
            self.crawler.driver.get(self.target_url)
            time.sleep(2)
            
            # フレーム内でログイン要素を探す
            frames = self.crawler.driver.find_elements("tag name", "frame")
            frames.extend(self.crawler.driver.find_elements("tag name", "iframe"))
            
            for i, frame in enumerate(frames):
                try:
                    self.crawler.driver.switch_to.frame(frame)
                    
                    # ログイン要素の検索
                    username_field = self.crawler.driver.find_element("name", "username")
                    password_field = self.crawler.driver.find_element("name", "password")
                    submit_button = self.crawler.driver.find_element("xpath", "//input[@type='submit'] | //input[@type='image'] | //button[@type='submit']")
                    
                    logger.info(f"✅ Found login elements in frame {i}")
                    
                    # 認証情報入力
                    username_field.clear()
                    username_field.send_keys(self.username)
                    
                    password_field.clear()
                    password_field.send_keys(self.password)
                    
                    # モーダルオーバーレイを削除
                    try:
                        self.crawler.driver.execute_script("""
                            var overlay = document.getElementById('modal_overlay');
                            if (overlay) overlay.remove();
                        """)
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # ログイン実行
                    submit_button.click()
                    time.sleep(3)
                    
                    # アラート処理
                    try:
                        alert = self.crawler.driver.switch_to.alert
                        logger.info(f"📢 Alert detected: {alert.text}")
                        alert.accept()
                        time.sleep(1)
                    except:
                        pass
                    
                    # ログイン成功確認
                    try:
                        self.crawler.driver.find_element("name", "username")
                        logger.warning("⚠️ Username field still present")
                    except:
                        logger.info("✅ Username field disappeared - login successful")
                        self.crawler.driver.switch_to.default_content()
                        return True
                    
                    self.crawler.driver.switch_to.default_content()
                    
                except Exception as e:
                    logger.debug(f"Frame {i} failed: {str(e)}")
                    try:
                        self.crawler.driver.switch_to.default_content()
                    except:
                        pass
                    continue
            
            logger.error("❌ Authentication failed - no login form found")
            return False
            
        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            return False
    
    def _discover_all_pages(self) -> List[str]:
        """全ページの発見（深度優先探索）"""
        logger.info("🔍 Discovering all accessible pages")
        
        discovered = set()
        to_visit = [self.target_url]
        visited = set()
        
        while to_visit and len(discovered) < self.max_pages:
            current_url = to_visit.pop(0)
            
            if current_url in visited:
                continue
                
            visited.add(current_url)
            
            try:
                # ページにアクセス
                self.crawler.driver.get(current_url)
                time.sleep(1)
                
                discovered.add(current_url)
                logger.debug(f"📄 Analyzing page: {current_url}")
                
                # リンクの抽出
                new_links = self._extract_all_links()
                
                # フレーム内のリンクも抽出
                frame_links = self._extract_frame_links()
                new_links.extend(frame_links)
                
                # 新しいリンクを追加
                for link in new_links:
                    full_url = urljoin(current_url, link)
                    if self._should_visit_url(full_url) and full_url not in visited:
                        to_visit.append(full_url)
                
                # フォームアクションURLも追加
                form_actions = self._extract_form_actions()
                for action in form_actions:
                    full_url = urljoin(current_url, action)
                    if self._should_visit_url(full_url) and full_url not in visited:
                        to_visit.append(full_url)
                        
            except Exception as e:
                logger.warning(f"⚠️ Error accessing {current_url}: {str(e)}")
                continue
        
        return list(discovered)
    
    def _extract_all_links(self) -> List[str]:
        """現在のページから全リンクを抽出"""
        links = []
        
        try:
            # <a> タグのリンク
            a_elements = self.crawler.driver.find_elements("tag name", "a")
            for element in a_elements:
                href = element.get_attribute("href")
                if href:
                    links.append(href)
            
            # <form> のaction属性
            forms = self.crawler.driver.find_elements("tag name", "form")
            for form in forms:
                action = form.get_attribute("action")
                if action:
                    links.append(action)
            
            # JavaScriptから動的に生成されるURL（基本的なパターン）
            script_elements = self.crawler.driver.find_elements("tag name", "script")
            for script in script_elements:
                content = script.get_attribute("innerHTML")
                if content:
                    # 簡単なURL抽出パターン
                    import re
                    urls = re.findall(r'["\']([^"\']*\.(?:php|html|jsp|asp)[^"\']*)["\']', content)
                    links.extend(urls)
                    
        except Exception as e:
            logger.warning(f"⚠️ Error extracting links: {str(e)}")
        
        return links
    
    def _extract_frame_links(self) -> List[str]:
        """フレーム内のリンクを抽出"""
        links = []
        
        try:
            # フレームの検出
            frames = self.crawler.driver.find_elements("tag name", "frame")
            frames.extend(self.crawler.driver.find_elements("tag name", "iframe"))
            
            original_context = None
            
            for i, frame in enumerate(frames):
                try:
                    # フレームに切り替え
                    self.crawler.driver.switch_to.frame(frame)
                    
                    # フレーム内のリンクを抽出
                    frame_links = self._extract_all_links()
                    links.extend(frame_links)
                    
                    # 元のコンテキストに戻る
                    self.crawler.driver.switch_to.default_content()
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error processing frame {i}: {str(e)}")
                    # エラー時も元のコンテキストに戻る
                    try:
                        self.crawler.driver.switch_to.default_content()
                    except:
                        pass
                        
        except Exception as e:
            logger.warning(f"⚠️ Error extracting frame links: {str(e)}")
        
        return links
    
    def _extract_form_actions(self) -> List[str]:
        """フォームのアクションURLを抽出"""
        actions = []
        
        try:
            forms = self.crawler.driver.find_elements("tag name", "form")
            for form in forms:
                action = form.get_attribute("action")
                if action:
                    actions.append(action)
                elif not action:  # actionが空の場合は現在のページ
                    actions.append(self.crawler.driver.current_url)
                    
        except Exception as e:
            logger.warning(f"⚠️ Error extracting form actions: {str(e)}")
        
        return actions
    
    def _should_visit_url(self, url: str) -> bool:
        """URLを訪問すべきかの判定"""
        parsed = urlparse(url)
        target_parsed = urlparse(self.target_url)
        
        # 同一ホストのみ
        if parsed.netloc != target_parsed.netloc:
            return False
        
        # 危険なエンドポイントを避ける
        dangerous_paths = [
            'logout', 'reboot', 'reset', 'shutdown', 'restart',
            'factory_default', 'format', 'delete_all'
        ]
        
        for dangerous in dangerous_paths:
            if dangerous.lower() in url.lower():
                return False
        
        # ファイル拡張子フィルター
        allowed_extensions = ['.php', '.html', '.htm', '.jsp', '.asp', '.aspx', '']
        if any(url.lower().endswith(ext) for ext in allowed_extensions) or '.' not in parsed.path.split('/')[-1]:
            return True
        
        return False
    
    def _capture_page_state(self, url: str, description: str = "") -> PageState:
        """ページ状態の詳細キャプチャ"""
        try:
            # ページのHTMLハッシュ
            page_source = self.crawler.driver.page_source
            page_hash = hashlib.md5(page_source.encode()).hexdigest()
            
            # DOM構造のハッシュ（より軽量）
            dom_elements = self.crawler.driver.find_elements("xpath", "//*")
            dom_structure = [elem.tag_name for elem in dom_elements[:100]]  # 最初の100要素
            dom_hash = hashlib.md5(str(dom_structure).encode()).hexdigest()
            
            # フォーム情報の抽出
            forms = self._extract_detailed_forms()
            
            # リンク情報
            links = self._extract_all_links()
            
            # 入力要素の詳細
            inputs = self._extract_input_details()
            
            # フレーム情報
            frames = self._extract_frame_info()
            
            # ブラウザ状態
            cookies = self.crawler.driver.get_cookies()
            
            # ストレージ情報（エラーを無視）
            local_storage = {}
            session_storage = {}
            try:
                local_storage = self.crawler.driver.execute_script("return window.localStorage;") or {}
                session_storage = self.crawler.driver.execute_script("return window.sessionStorage;") or {}
            except:
                pass
            
            # JavaScript変数（基本的なもの）
            js_vars = {}
            try:
                js_vars = self.crawler.driver.execute_script("""
                    var vars = {};
                    if (typeof window !== 'undefined') {
                        vars.userAgent = navigator.userAgent;
                        vars.location = window.location.href;
                        vars.title = document.title;
                    }
                    return vars;
                """) or {}
            except:
                pass
            
            # セキュリティトークンの検出
            tokens = self._extract_security_tokens()
            
            return PageState(
                url=url,
                title=self.crawler.driver.title,
                timestamp=time.time(),
                page_hash=page_hash,
                forms=forms,
                links=links,
                inputs=inputs,
                frames=frames,
                cookies=cookies,
                local_storage=local_storage,
                session_storage=session_storage,
                javascript_vars=js_vars,
                dom_structure_hash=dom_hash,
                security_tokens=tokens
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Error capturing page state for {url}: {str(e)}")
            return PageState(
                url=url,
                title="",
                timestamp=time.time(),
                page_hash="",
                forms=[],
                links=[],
                inputs=[],
                frames=[],
                cookies=[],
                local_storage={},
                session_storage={},
                javascript_vars={},
                dom_structure_hash="",
                security_tokens=[]
            )
    
    def _extract_detailed_forms(self) -> List[Dict]:
        """フォームの詳細情報を抽出"""
        forms = []
        
        try:
            form_elements = self.crawler.driver.find_elements("tag name", "form")
            
            for i, form in enumerate(form_elements):
                form_data = {
                    "index": i,
                    "action": form.get_attribute("action") or self.crawler.driver.current_url,
                    "method": form.get_attribute("method") or "GET",
                    "fields": [],
                    "csrf_tokens": []
                }
                
                # フォーム内の入力要素
                inputs = form.find_elements("xpath", ".//input | .//select | .//textarea")
                
                for input_elem in inputs:
                    field = {
                        "type": input_elem.get_attribute("type") or "text",
                        "name": input_elem.get_attribute("name") or "",
                        "id": input_elem.get_attribute("id") or "",
                        "value": input_elem.get_attribute("value") or "",
                        "required": input_elem.get_attribute("required") is not None,
                        "readonly": input_elem.get_attribute("readonly") is not None,
                        "disabled": input_elem.get_attribute("disabled") is not None,
                        "maxlength": input_elem.get_attribute("maxlength") or "",
                        "pattern": input_elem.get_attribute("pattern") or "",
                        "placeholder": input_elem.get_attribute("placeholder") or ""
                    }
                    
                    form_data["fields"].append(field)
                    
                    # CSRFトークンの検出
                    if any(token_name in field["name"].lower() for token_name in ["csrf", "token", "_token", "authenticity"]):
                        form_data["csrf_tokens"].append({
                            "name": field["name"],
                            "value": field["value"]
                        })
                
                forms.append(form_data)
                
        except Exception as e:
            logger.warning(f"⚠️ Error extracting forms: {str(e)}")
        
        return forms
    
    def _extract_input_details(self) -> List[Dict]:
        """入力要素の詳細情報"""
        inputs = []
        
        try:
            input_elements = self.crawler.driver.find_elements("xpath", "//input | //select | //textarea")
            
            for i, elem in enumerate(input_elements):
                input_data = {
                    "index": i,
                    "tag": elem.tag_name,
                    "type": elem.get_attribute("type") or "",
                    "name": elem.get_attribute("name") or "",
                    "id": elem.get_attribute("id") or "",
                    "value": elem.get_attribute("value") or "",
                    "xpath": self._get_element_xpath(elem),
                    "css_selector": self._get_element_css_selector(elem),
                    "fuzzing_priority": self._calculate_fuzzing_priority(elem)
                }
                
                inputs.append(input_data)
                
        except Exception as e:
            logger.warning(f"⚠️ Error extracting inputs: {str(e)}")
        
        return inputs
    
    def _extract_frame_info(self) -> List[Dict]:
        """フレーム情報の抽出"""
        frames = []
        
        try:
            frame_elements = self.crawler.driver.find_elements("tag name", "frame")
            frame_elements.extend(self.crawler.driver.find_elements("tag name", "iframe"))
            
            for i, frame in enumerate(frame_elements):
                frame_data = {
                    "index": i,
                    "name": frame.get_attribute("name") or "",
                    "src": frame.get_attribute("src") or "",
                    "id": frame.get_attribute("id") or ""
                }
                
                frames.append(frame_data)
                
        except Exception as e:
            logger.warning(f"⚠️ Error extracting frames: {str(e)}")
        
        return frames
    
    def _extract_security_tokens(self) -> List[str]:
        """セキュリティトークンの抽出"""
        tokens = []
        
        try:
            # hidden inputからのトークン
            hidden_inputs = self.crawler.driver.find_elements("xpath", "//input[@type='hidden']")
            for input_elem in hidden_inputs:
                name = input_elem.get_attribute("name") or ""
                value = input_elem.get_attribute("value") or ""
                
                if any(token_name in name.lower() for token_name in ["csrf", "token", "_token", "authenticity"]):
                    tokens.append(value)
            
            # metaタグからのトークン
            meta_elements = self.crawler.driver.find_elements("xpath", "//meta[@name]")
            for meta in meta_elements:
                name = meta.get_attribute("name") or ""
                content = meta.get_attribute("content") or ""
                
                if any(token_name in name.lower() for token_name in ["csrf", "token"]):
                    tokens.append(content)
                    
        except Exception as e:
            logger.warning(f"⚠️ Error extracting security tokens: {str(e)}")
        
        return list(set(tokens))  # 重複除去
    
    def _get_element_xpath(self, element) -> str:
        """要素のXPathを取得"""
        try:
            return self.crawler.driver.execute_script("""
                function getXPath(element) {
                    if (element.id !== '') {
                        return '//*[@id="' + element.id + '"]';
                    }
                    if (element === document.body) {
                        return '/html/body';
                    }
                    
                    var ix = 0;
                    var siblings = element.parentNode.childNodes;
                    for (var i = 0; i < siblings.length; i++) {
                        var sibling = siblings[i];
                        if (sibling === element) {
                            return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            ix++;
                        }
                    }
                }
                return getXPath(arguments[0]);
            """, element)
        except:
            return ""
    
    def _get_element_css_selector(self, element) -> str:
        """要素のCSSセレクターを取得"""
        try:
            return self.crawler.driver.execute_script("""
                function getCSSSelector(element) {
                    if (element.id) {
                        return '#' + element.id;
                    }
                    
                    var path = [];
                    while (element.nodeType === Node.ELEMENT_NODE) {
                        var selector = element.nodeName.toLowerCase();
                        if (element.id) {
                            selector += '#' + element.id;
                            path.unshift(selector);
                            break;
                        } else {
                            var sibling = element;
                            var nth = 1;
                            while (sibling = sibling.previousElementSibling) {
                                if (sibling.nodeName.toLowerCase() == selector)
                                    nth++;
                            }
                            if (nth != 1)
                                selector += ':nth-of-type(' + nth + ')';
                        }
                        path.unshift(selector);
                        element = element.parentNode;
                    }
                    return path.join(' > ');
                }
                return getCSSSelector(arguments[0]);
            """, element)
        except:
            return ""
    
    def _calculate_fuzzing_priority(self, element) -> int:
        """Fuzzing優先度の計算"""
        priority = 0
        
        try:
            elem_type = element.get_attribute("type") or ""
            elem_name = element.get_attribute("name") or ""
            
            # 入力タイプによる優先度
            if elem_type in ["text", "password", "email", "url"]:
                priority += 10
            elif elem_type in ["hidden"]:
                priority += 5
            elif elem_type in ["submit", "button"]:
                priority += 3
            
            # 名前による優先度
            high_priority_names = ["username", "password", "admin", "config", "command"]
            for name in high_priority_names:
                if name in elem_name.lower():
                    priority += 15
                    break
            
            # セキュリティ関連
            security_names = ["csrf", "token", "auth"]
            for name in security_names:
                if name in elem_name.lower():
                    priority += 8
                    break
                    
        except Exception as e:
            logger.warning(f"⚠️ Error calculating fuzzing priority: {str(e)}")
        
        return priority
    
    def _analyze_page_for_fuzzing(self, url: str):
        """ページのFuzzing分析"""
        try:
            logger.debug(f"🔬 Analyzing page for fuzzing: {url}")
            
            # ページにアクセス
            self.crawler.driver.get(url)
            time.sleep(1)
            
            # ページ状態をキャプチャ
            page_state = self._capture_page_state(url, f"Fuzzing analysis of {url}")
            self.page_states.append(page_state)
            
            # Fuzzing対象を特定
            for form in page_state.forms:
                fuzzing_target = FuzzingTarget(
                    endpoint=form["action"],
                    method=form["method"],
                    parameters=form["fields"],
                    csrf_tokens=[t["value"] for t in form["csrf_tokens"]],
                    authentication_required=True,  # ログイン後なので基本的にTrue
                    session_dependent=len(form["csrf_tokens"]) > 0,
                    priority_score=self._calculate_endpoint_priority(form),
                    vulnerability_indicators=self._detect_vulnerability_indicators(form)
                )
                
                self.fuzzing_targets.append(fuzzing_target)
                
        except Exception as e:
            logger.warning(f"⚠️ Error analyzing page {url} for fuzzing: {str(e)}")
    
    def _calculate_endpoint_priority(self, form: Dict) -> int:
        """エンドポイントの優先度計算"""
        priority = 0
        
        # フィールド数による優先度
        priority += len(form["fields"]) * 2
        
        # CSRFトークンの有無
        if form["csrf_tokens"]:
            priority += 10
        else:
            priority += 15  # CSRFトークンがないのは脆弱性の可能性
        
        # フォームのアクションによる優先度
        action = form["action"].lower()
        high_priority_actions = ["config", "admin", "settings", "update", "save"]
        for keyword in high_priority_actions:
            if keyword in action:
                priority += 20
                break
        
        return priority
    
    def _detect_vulnerability_indicators(self, form: Dict) -> List[str]:
        """脆弱性指標の検出"""
        indicators = []
        
        # CSRFトークンの欠如
        if not form["csrf_tokens"]:
            indicators.append("missing_csrf_token")
        
        # SQLインジェクションの可能性
        for field in form["fields"]:
            if field["type"] in ["text", "hidden"] and not field["pattern"]:
                indicators.append("potential_sql_injection")
                break
        
        # XSSの可能性
        text_fields = [f for f in form["fields"] if f["type"] in ["text", "textarea"]]
        if text_fields:
            indicators.append("potential_xss")
        
        # パストラバーサルの可能性
        file_fields = [f for f in form["fields"] if "file" in f["name"].lower() or "path" in f["name"].lower()]
        if file_fields:
            indicators.append("potential_path_traversal")
        
        return indicators
    
    def _analyze_navigation_paths(self):
        """ナビゲーションパスの分析"""
        logger.info("🗺️ Analyzing navigation paths")
        
        # 基本的なパス分析（現在のページ状態から）
        for i, state in enumerate(self.page_states):
            path = [state.url]
            
            # リンクを辿った仮想的なパス
            for link in state.links[:5]:  # 最初の5つのリンクのみ
                try:
                    full_link = urljoin(state.url, link)
                    if self._should_visit_url(full_link):
                        path.append(full_link)
                except:
                    continue
            
            if len(path) > 1:
                self.navigation_paths.append(path)
    
    def _prioritize_fuzzing_targets(self):
        """Fuzzing対象の優先度付け"""
        logger.info("📊 Prioritizing fuzzing targets")
        
        # 優先度でソート
        self.fuzzing_targets.sort(key=lambda x: x.priority_score, reverse=True)
        
        # 上位ターゲットにランキングを追加
        for i, target in enumerate(self.fuzzing_targets[:20]):  # 上位20個
            logger.info(f"🎯 Priority {i+1}: {target.endpoint} (Score: {target.priority_score})")
    
    def _generate_fuzzing_results(self) -> Dict[str, Any]:
        """Fuzzing結果の生成"""
        results = {
            "session_info": {
                "target_url": self.target_url,
                "timestamp": time.time(),
                "total_pages": len(self.page_states),
                "total_fuzzing_targets": len(self.fuzzing_targets),
                "total_navigation_paths": len(self.navigation_paths)
            },
            "page_states": [asdict(state) for state in self.page_states],
            "fuzzing_targets": [asdict(target) for target in self.fuzzing_targets],
            "navigation_paths": self.navigation_paths,
            "session_changes": self.session_changes,
            "statistics": self._generate_statistics(),
            "recommendations": self._generate_recommendations()
        }
        
        return results
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """統計情報の生成"""
        total_forms = sum(len(state.forms) for state in self.page_states)
        total_inputs = sum(len(state.inputs) for state in self.page_states)
        total_tokens = sum(len(state.security_tokens) for state in self.page_states)
        
        vulnerability_types = {}
        for target in self.fuzzing_targets:
            for indicator in target.vulnerability_indicators:
                vulnerability_types[indicator] = vulnerability_types.get(indicator, 0) + 1
        
        return {
            "pages_discovered": len(self.page_states),
            "unique_urls": len(set(state.url for state in self.page_states)),
            "total_forms": total_forms,
            "total_inputs": total_inputs,
            "total_security_tokens": total_tokens,
            "high_priority_targets": len([t for t in self.fuzzing_targets if t.priority_score >= 30]),
            "vulnerability_indicators": vulnerability_types,
            "pages_with_csrf": len([s for s in self.page_states if s.security_tokens]),
            "average_page_complexity": total_inputs / len(self.page_states) if self.page_states else 0
        }
    
    def _generate_recommendations(self) -> List[str]:
        """推奨事項の生成"""
        recommendations = []
        
        stats = self._generate_statistics()
        
        if stats["high_priority_targets"] > 5:
            recommendations.append(f"High-priority fuzzing targets identified: {stats['high_priority_targets']}. Focus on these first.")
        
        if "missing_csrf_token" in stats["vulnerability_indicators"]:
            recommendations.append(f"CSRF protection missing in {stats['vulnerability_indicators']['missing_csrf_token']} forms. Prioritize CSRF testing.")
        
        if "potential_sql_injection" in stats["vulnerability_indicators"]:
            recommendations.append("SQL injection vectors detected. Include SQL injection payloads in fuzzing.")
        
        if stats["pages_with_csrf"] < len(self.page_states) * 0.5:
            recommendations.append("Less than 50% of pages have CSRF protection. Consider comprehensive CSRF testing.")
        
        if stats["average_page_complexity"] > 10:
            recommendations.append("High page complexity detected. Consider automated input generation for comprehensive testing.")
        
        return recommendations
    
    def _url_to_filename(self, url: str) -> str:
        """URLからファイル名を生成"""
        import re
        # URLから不正な文字を除去してファイル名を生成
        parsed = urlparse(url)
        filename = f"{parsed.netloc}{parsed.path}{parsed.query}"
        # 不正な文字を置換
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        # 長すぎる場合は切り詰め
        if len(filename) > 100:
            filename = filename[:100]
        return filename if filename else "index"
    
    def save_results(self, output_file: str = "fuzzing_crawl_results.json"):
        """結果の保存"""
        try:
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
            
            # HTMLファイルの保存（保存済みのHTMLファイルをコピー）
            logger.info(f"💾 Organizing HTML files to {html_dir}")
            
            # 既存のHTMLファイルを検索してコピー
            base_output_dir = Path("iot_crawler_output")
            existing_html_files = list(base_output_dir.glob("*/html/*.html"))
            
            if existing_html_files:
                import shutil
                for html_file in existing_html_files:
                    target_path = html_dir / html_file.name
                    try:
                        shutil.copy2(html_file, target_path)
                        logger.debug(f"Copied HTML: {target_path}")
                    except Exception as e:
                        logger.warning(f"Could not copy {html_file}: {str(e)}")
            else:
                logger.info("No existing HTML files found - HTML was saved during crawling")
            
            # JSONファイルの保存
            json_path = json_dir / output_file
            logger.info(f"💾 Saving JSON results to {json_path}")
            
            results = self._generate_fuzzing_results()
            
            # 出力ディレクトリ情報を結果に追加
            results["output_info"] = {
                "output_directory": str(output_dir),
                "html_directory": str(html_dir),
                "json_directory": str(json_dir),
                "timestamp": timestamp,
                "html_files_copied": len(list(html_dir.glob("*.html")))
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"✅ Results saved successfully to {output_dir}")
            return str(output_dir)
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")
            return None
    
    def cleanup(self):
        """クリーンアップ"""
        if hasattr(self.crawler, 'driver') and self.crawler.driver:
            self.crawler.driver.quit()
        logger.info("🧹 Cleanup completed")

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fuzzing-Oriented Post-Login Page Crawler")
    parser.add_argument("--url", default="http://127.0.0.1:8888", help="Target URL")
    parser.add_argument("--username", default="admin", help="Username")
    parser.add_argument("--password", default="password", help="Password") 
    parser.add_argument("--output", default="fuzzing_crawl_results.json", help="Output file")
    
    args = parser.parse_args()
    
    # クローラーの実行
    crawler = FuzzingPageCrawler(args.url, args.username, args.password)
    
    if crawler.initialize():
        results = crawler.run_comprehensive_crawl()
        
        if results.get("status") != "error":
            output_file = crawler.save_results(args.output)
            print(f"\n🎉 Fuzzing crawl completed successfully!")
            print(f"📊 Results saved to: {output_file}")
            print(f"📈 Statistics:")
            print(f"  • Pages discovered: {results['statistics']['pages_discovered']}")
            print(f"  • Fuzzing targets: {results['session_info']['total_fuzzing_targets']}")
            print(f"  • High-priority targets: {results['statistics']['high_priority_targets']}")
            print(f"  • Vulnerability indicators: {len(results['statistics']['vulnerability_indicators'])}")
        else:
            print(f"❌ Crawl failed: {results.get('message')}")
    else:
        print("❌ Failed to initialize crawler")

if __name__ == "__main__":
    main()