"""
IoT Device Page Crawler Module
IoTデバイスのページ構造を再帰的にクロールするモジュール
"""

import time
import hashlib
from urllib.parse import urljoin, urlparse
from typing import Set, Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    NoSuchFrameException, StaleElementReferenceException
)

from .config import CrawlerConfig, CrawlerLogger

@dataclass
class PageData:
    """ページデータクラス"""
    url: str
    title: str
    html_content: str
    frame_name: Optional[str] = None
    parent_url: Optional[str] = None
    depth: int = 0
    timestamp: float = field(default_factory=time.time)
    content_hash: str = field(init=False)
    
    def __post_init__(self):
        self.content_hash = hashlib.md5(self.html_content.encode()).hexdigest()

@dataclass
class FrameData:
    """フレームデータクラス"""
    name: str
    src: str
    content: str
    parent_url: str
    index: int
    timestamp: float = field(default_factory=time.time)

class IoTPageCrawler:
    """IoTデバイスページクローラー"""
    
    def __init__(self, driver: webdriver.Chrome, config: CrawlerConfig, logger: CrawlerLogger):
        self.driver = driver
        self.config = config
        self.logger = logger
        
        # クロール状態管理
        self.visited_urls: Set[str] = set()
        self.visited_hashes: Set[str] = set()
        self.pages_data: List[PageData] = []
        self.frames_data: List[FrameData] = []
        self.crawl_queue: List[Tuple[str, int]] = []  # (url, depth)
        
        # 構造分析データ
        self.url_structure: Dict[str, Any] = {}
        self.link_map: Dict[str, List[str]] = {}
        self.form_data: List[Dict[str, Any]] = []
        
    def crawl_all_pages(self, start_url: str) -> Dict[str, Any]:
        """全ページクロールの開始"""
        self.logger.info(f"Starting comprehensive crawl from: {start_url}")
        
        # 初期ページの追加
        self.crawl_queue.append((start_url, 0))
        
        while self.crawl_queue:
            current_url, depth = self.crawl_queue.pop(0)
            
            if depth > self.config.max_depth:
                self.logger.debug(f"Max depth reached for: {current_url}")
                continue
                
            if current_url in self.visited_urls:
                self.logger.debug(f"Already visited: {current_url}")
                continue
            
            self.logger.info(f"Crawling page (depth {depth}): {current_url}")
            
            try:
                # ページクロール実行
                page_data = self._crawl_single_page(current_url, depth)
                if page_data:
                    self.pages_data.append(page_data)
                    self.visited_urls.add(current_url)
                    
                    # リンク抽出と次のページへの追加
                    self._extract_and_queue_links(current_url, depth)
                    
                    # フレームクロール
                    if self.config.crawl_frames:
                        self._crawl_frames(current_url)
                
            except Exception as e:
                self.logger.error(f"Error crawling {current_url}: {str(e)}")
                continue
        
        # 結果の構築
        return self._build_crawl_results()
    
    def _crawl_single_page(self, url: str, depth: int) -> Optional[PageData]:
        """単一ページのクロール"""
        try:
            # ページロード
            self.driver.get(url)
            time.sleep(self.config.element_wait_timeout)
            
            # ページデータ取得
            title = self.driver.title
            html_content = self.driver.page_source
            
            # 重複チェック
            content_hash = hashlib.md5(html_content.encode()).hexdigest()
            if content_hash in self.visited_hashes:
                self.logger.debug(f"Duplicate content detected for: {url}")
                return None
            
            self.visited_hashes.add(content_hash)
            
            # フォーム抽出
            if self.config.extract_forms:
                self._extract_forms(url)
            
            # HTMLファイルを即座に保存
            if self.config.save_html:
                self._save_html_immediately(url, html_content, depth)
            
            return PageData(
                url=url,
                title=title,
                html_content=html_content,
                depth=depth
            )
            
        except Exception as e:
            self.logger.error(f"Error loading page {url}: {str(e)}")
            return None
    
    def _crawl_frames(self, parent_url: str):
        """フレームのクロール"""
        self.logger.debug(f"Crawling frames for: {parent_url}")
        
        try:
            self.driver.switch_to.default_content()
            
            # フレーム要素の取得
            frames = self.driver.find_elements(By.TAG_NAME, 'frame')
            frames.extend(self.driver.find_elements(By.TAG_NAME, 'iframe'))
            
            for index, frame_element in enumerate(frames):
                try:
                    frame_name = frame_element.get_attribute('name') or f'frame_{index}'
                    frame_src = frame_element.get_attribute('src')
                    
                    if not frame_src:
                        # srcが動的に設定される場合の待機
                        frame_src = self._wait_for_frame_src(frame_element)
                    
                    if frame_src:
                        frame_url = urljoin(parent_url, frame_src)
                        self.logger.debug(f"Processing frame: {frame_name} -> {frame_url}")
                        
                        # フレームに切り替え
                        self.driver.switch_to.default_content()
                        self.driver.switch_to.frame(frame_name)
                        
                        # フレーム内容取得
                        WebDriverWait(self.driver, self.config.frame_wait_timeout).until(
                            EC.presence_of_element_located((By.TAG_NAME, "html"))
                        )
                        
                        frame_content = self.driver.page_source
                        
                        # フレームデータ保存
                        frame_data = FrameData(
                            name=frame_name,
                            src=frame_url,
                            content=frame_content,
                            parent_url=parent_url,
                            index=index
                        )
                        self.frames_data.append(frame_data)
                        
                        # フレーム内のリンク抽出
                        self._extract_frame_links(frame_url, parent_url)
                        
                        # フレーム内のフォーム抽出
                        if self.config.extract_forms:
                            self._extract_forms(frame_url, frame_name)
                
                except Exception as e:
                    self.logger.debug(f"Error processing frame {index}: {str(e)}")
                    continue
                
                finally:
                    self.driver.switch_to.default_content()
        
        except Exception as e:
            self.logger.error(f"Error crawling frames for {parent_url}: {str(e)}")
        
        finally:
            self.driver.switch_to.default_content()
    
    def _wait_for_frame_src(self, frame_element, max_wait: int = None) -> Optional[str]:
        """フレームsrc属性の待機"""
        if max_wait is None:
            max_wait = self.config.frame_wait_timeout
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                src = frame_element.get_attribute("src")
                if src and src.strip():
                    return src
                
                time.sleep(0.5)
                
                # 要素の再取得（DOM更新対応）
                frame_name = frame_element.get_attribute("name")
                if frame_name:
                    self.driver.switch_to.default_content()
                    frame_element = self.driver.find_element(By.NAME, frame_name)
                    
            except StaleElementReferenceException:
                break
            except Exception:
                break
        
        return None
    
    def _extract_and_queue_links(self, current_url: str, current_depth: int):
        """リンク抽出と次のページキューへの追加"""
        if not self.config.extract_links:
            return
        
        try:
            self.driver.switch_to.default_content()
            
            # リンク要素の取得
            link_elements = self.driver.find_elements(By.TAG_NAME, 'a')
            
            current_links = []
            
            for link_element in link_elements:
                try:
                    href = link_element.get_attribute('href')
                    if not href:
                        continue
                    
                    # 絶対URLに変換
                    absolute_url = urljoin(current_url, href)
                    
                    # フィルタリング
                    if self._should_follow_link(absolute_url, current_url):
                        current_links.append(absolute_url)
                        
                        # クロールキューに追加
                        if absolute_url not in self.visited_urls:
                            self.crawl_queue.append((absolute_url, current_depth + 1))
                            self.logger.debug(f"Queued link: {absolute_url}")
                
                except Exception as e:
                    self.logger.debug(f"Error processing link: {str(e)}")
                    continue
            
            # リンクマップ更新
            self.link_map[current_url] = current_links
            
        except Exception as e:
            self.logger.error(f"Error extracting links from {current_url}: {str(e)}")
    
    def _extract_frame_links(self, frame_url: str, parent_url: str):
        """フレーム内のリンク抽出"""
        try:
            link_elements = self.driver.find_elements(By.TAG_NAME, 'a')
            frame_links = []
            
            for link_element in link_elements:
                try:
                    href = link_element.get_attribute('href')
                    if href:
                        absolute_url = urljoin(frame_url, href)
                        if self._should_follow_link(absolute_url, parent_url):
                            frame_links.append(absolute_url)
                            
                            # メインクロールキューに追加
                            if absolute_url not in self.visited_urls:
                                self.crawl_queue.append((absolute_url, 1))
                
                except Exception:
                    continue
            
            self.link_map[frame_url] = frame_links
            
        except Exception as e:
            self.logger.debug(f"Error extracting frame links: {str(e)}")
    
    def _should_follow_link(self, url: str, current_url: str) -> bool:
        """リンクフォローの判断"""
        try:
            parsed_url = urlparse(url)
            parsed_current = urlparse(current_url)
            
            # 外部リンクの除外
            if not self.config.follow_external_links:
                if parsed_url.netloc != parsed_current.netloc:
                    return False
            
            # スキームフィルタ
            if parsed_url.scheme not in ['http', 'https']:
                return False
            
            # 除外パターン
            exclude_patterns = [
                'javascript:', 'mailto:', '#', 'tel:',
                '.pdf', '.zip', '.tar', '.gz',
                'logout', 'reboot', 'reset'
            ]
            
            url_lower = url.lower()
            for pattern in exclude_patterns:
                if pattern in url_lower:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _extract_forms(self, url: str, frame_name: Optional[str] = None):
        """フォーム情報の抽出"""
        try:
            form_elements = self.driver.find_elements(By.TAG_NAME, 'form')
            
            for i, form in enumerate(form_elements):
                try:
                    form_data = {
                        'url': url,
                        'frame': frame_name,
                        'index': i,
                        'action': form.get_attribute('action') or url,
                        'method': form.get_attribute('method') or 'GET',
                        'fields': [],
                        'timestamp': time.time()
                    }
                    
                    # 入力フィールドの抽出
                    input_elements = form.find_elements(By.TAG_NAME, 'input')
                    select_elements = form.find_elements(By.TAG_NAME, 'select')
                    textarea_elements = form.find_elements(By.TAG_NAME, 'textarea')
                    
                    for input_elem in input_elements:
                        field_data = {
                            'type': 'input',
                            'input_type': input_elem.get_attribute('type') or 'text',
                            'name': input_elem.get_attribute('name'),
                            'id': input_elem.get_attribute('id'),
                            'value': input_elem.get_attribute('value'),
                            'placeholder': input_elem.get_attribute('placeholder'),
                            'required': input_elem.get_attribute('required') is not None
                        }
                        form_data['fields'].append(field_data)
                    
                    for select_elem in select_elements:
                        options = []
                        option_elements = select_elem.find_elements(By.TAG_NAME, 'option')
                        for option in option_elements:
                            options.append({
                                'value': option.get_attribute('value'),
                                'text': option.text
                            })
                        
                        field_data = {
                            'type': 'select',
                            'name': select_elem.get_attribute('name'),
                            'id': select_elem.get_attribute('id'),
                            'options': options
                        }
                        form_data['fields'].append(field_data)
                    
                    for textarea_elem in textarea_elements:
                        field_data = {
                            'type': 'textarea',
                            'name': textarea_elem.get_attribute('name'),
                            'id': textarea_elem.get_attribute('id'),
                            'placeholder': textarea_elem.get_attribute('placeholder')
                        }
                        form_data['fields'].append(field_data)
                    
                    self.form_data.append(form_data)
                    
                except Exception as e:
                    self.logger.debug(f"Error extracting form {i}: {str(e)}")
                    continue
        
        except Exception as e:
            self.logger.debug(f"Error extracting forms from {url}: {str(e)}")
    
    def _build_crawl_results(self) -> Dict[str, Any]:
        """クロール結果の構築"""
        # URL構造の分析
        self._analyze_url_structure()
        
        return {
            'summary': {
                'total_pages': len(self.pages_data),
                'total_frames': len(self.frames_data),
                'total_forms': len(self.form_data),
                'total_links': sum(len(links) for links in self.link_map.values()),
                'crawl_depth': max((page.depth for page in self.pages_data), default=0),
                'timestamp': time.time()
            },
            'pages': [
                {
                    'url': page.url,
                    'title': page.title,
                    'frame_name': page.frame_name,
                    'parent_url': page.parent_url,
                    'depth': page.depth,
                    'content_hash': page.content_hash,
                    'timestamp': page.timestamp
                }
                for page in self.pages_data
            ],
            'frames': [
                {
                    'name': frame.name,
                    'src': frame.src,
                    'parent_url': frame.parent_url,
                    'index': frame.index,
                    'timestamp': frame.timestamp
                }
                for frame in self.frames_data
            ],
            'url_structure': self.url_structure,
            'link_map': self.link_map,
            'forms': self.form_data
        }
    
    def _analyze_url_structure(self):
        """URL構造の分析"""
        structure = {}
        
        for page in self.pages_data:
            parsed = urlparse(page.url)
            path_parts = [part for part in parsed.path.split('/') if part]
            
            current_level = structure
            for part in path_parts:
                if part not in current_level:
                    current_level[part] = {
                        'pages': [],
                        'children': {}
                    }
                current_level[part]['pages'].append({
                    'url': page.url,
                    'title': page.title,
                    'depth': page.depth
                })
                current_level = current_level[part]['children']
        
        self.url_structure = structure
    
    def get_pages_data(self) -> List[PageData]:
        """ページデータの取得"""
        return self.pages_data.copy()
    
    def get_frames_data(self) -> List[FrameData]:
        """フレームデータの取得"""
        return self.frames_data.copy()
    
    def get_form_data(self) -> List[Dict[str, Any]]:
        """フォームデータの取得"""
        return self.form_data.copy()
    
    def _save_html_immediately(self, url: str, html_content: str, depth: int):
        """HTMLファイルの即座保存"""
        try:
            # 出力ディレクトリの確認/作成
            from pathlib import Path
            import re
            
            # 基本出力ディレクトリ
            base_output_dir = Path(self.config.output_dir)
            
            # タイムスタンプ付き固有ディレクトリの検索
            crawl_session_dirs = list(base_output_dir.glob("crawl_session_*"))
            if crawl_session_dirs:
                # 最新のセッションディレクトリを使用
                latest_dir = max(crawl_session_dirs, key=lambda x: x.stat().st_mtime)
                html_dir = latest_dir / "html"
            else:
                # 新しいセッションディレクトリを作成
                import time
                timestamp = int(time.time())
                unique_dir_name = f"crawl_session_{timestamp}"
                session_dir = base_output_dir / unique_dir_name
                session_dir.mkdir(parents=True, exist_ok=True)
                html_dir = session_dir / "html"
            
            html_dir.mkdir(parents=True, exist_ok=True)
            
            # URLからファイル名を生成
            from urllib.parse import urlparse
            parsed = urlparse(url)
            filename = f"{parsed.netloc}{parsed.path}{parsed.query}"
            # 不正な文字を置換
            filename = re.sub(r'[^\w\-_\.]', '_', filename)
            # 長すぎる場合は切り詰め
            if len(filename) > 100:
                filename = filename[:100]
            if not filename:
                filename = "index"
            
            # 深度情報を含むファイル名
            safe_filename = f"{depth:03d}_{filename}.html"
            html_path = html_dir / safe_filename
            
            # HTMLファイルの保存
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.debug(f"Saved HTML immediately: {html_path}")
            
        except Exception as e:
            self.logger.warning(f"Could not save HTML immediately for {url}: {str(e)}")