"""
IoT Device Crawler Package
IoTデバイスの自動クロール・分析・Fuzzing準備用パッケージ
"""

from .config import CrawlerConfig, CrawlerLogger, load_config_from_env
from .main_crawler import IoTMainCrawler, create_iot_crawler
from .authentication import IoTAuthenticator
from .page_crawler import IoTPageCrawler, PageData, FrameData
from .session_manager import IoTSessionManager, SessionState, CrawlSession
from .structure_analyzer import IoTStructureAnalyzer, DOMElement, URLStructure, SecurityContext
from .output_manager import IoTOutputManager

__version__ = "1.0.0"
__author__ = "IoT Security Research Team"
__description__ = "IoT Device Web Interface Crawler for Security Analysis and Fuzzing Preparation"

__all__ = [
    # Main components
    'IoTMainCrawler',
    'create_iot_crawler',
    
    # Configuration
    'CrawlerConfig',
    'CrawlerLogger', 
    'load_config_from_env',
    
    # Core modules
    'IoTAuthenticator',
    'IoTPageCrawler',
    'IoTSessionManager',
    'IoTStructureAnalyzer',
    'IoTOutputManager',
    
    # Data classes
    'PageData',
    'FrameData',
    'SessionState',
    'CrawlSession',
    'DOMElement',
    'URLStructure',
    'SecurityContext'
]