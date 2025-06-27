#!/usr/bin/env python3
"""
Fuzzing Crawl Results Visualization Generator
Fuzzingクロール結果の可視化生成ツール

このモジュールは、fuzzing_page_crawler.pyの結果を分析し、
以下の可視化を生成します：
1. ページ構造とフレーム関係図
2. Fuzzing対象の優先度分布
3. 脆弱性指標の分析
4. セキュリティ分析レポート
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
from matplotlib.patches import FancyBboxPatch
import numpy as np
from typing import Dict, List, Any, Tuple
import pandas as pd
from datetime import datetime
import seaborn as sns
from urllib.parse import urlparse
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['figure.dpi'] = 100

class FuzzingVisualizationGenerator:
    """Fuzzingクロール結果の可視化生成クラス"""
    
    def __init__(self, results_file: str):
        """
        初期化
        
        Args:
            results_file: fuzzing_page_crawler.pyの結果JSONファイル
        """
        self.results_file = results_file
        self.data = self._load_results()
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72', 
            'accent': '#F18F01',
            'warning': '#C73E1D',
            'success': '#6A994E',
            'info': '#577590',
            'light': '#F5F5F5',
            'dark': '#2D3436'
        }
        
    def _load_results(self) -> Dict[str, Any]:
        """結果ファイルの読み込み"""
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading results file: {e}")
            return {}
    
    def generate_all_visualizations(self, output_dir: str = "visualizations"):
        """全ての可視化を生成"""
        import os
        from datetime import datetime
        
        # タイムスタンプ付きディレクトリの自動生成
        if output_dir == "visualizations" or not output_dir.endswith(('_', '-')):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if output_dir == "visualizations":
                output_dir = f"visualizations_{timestamp}"
            elif not any(c in output_dir for c in ['_', '-']):
                output_dir = f"{output_dir}_{timestamp}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        print("📊 Generating comprehensive visualizations...")
        
        # 1. ページ構造図
        self.create_page_structure_diagram(f"{output_dir}/page_structure.png")
        
        # 2. Fuzzing対象分析
        self.create_fuzzing_targets_analysis(f"{output_dir}/fuzzing_targets.png")
        
        # 3. 脆弱性分布
        self.create_vulnerability_distribution(f"{output_dir}/vulnerability_distribution.png")
        
        # 4. セキュリティ分析ダッシュボード
        self.create_security_dashboard(f"{output_dir}/security_dashboard.png")
        
        # 5. フレーム関係図
        self.create_frame_relationship_graph(f"{output_dir}/frame_relationships.png")
        
        # 6. 総合レポート
        self.create_comprehensive_report(f"{output_dir}/comprehensive_report.png")
        
        print(f"✅ All visualizations saved to {output_dir}/")
        return output_dir
    
    def create_page_structure_diagram(self, output_path: str):
        """ページ構造図の作成"""
        fig, ax = plt.subplots(1, 1, figsize=(14, 10))
        
        # データ準備
        pages = self.data.get('page_states', [])
        target_url = self.data.get('session_info', {}).get('target_url', '')
        
        if not pages:
            ax.text(0.5, 0.5, 'No page data available', ha='center', va='center', fontsize=16)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            return
        
        # ページ階層の構築
        page_hierarchy = self._build_page_hierarchy(pages)
        
        # 描画
        y_positions = {}
        x_positions = {}
        
        # メインページ
        main_page = page_hierarchy.get('main', {})
        ax.add_patch(FancyBboxPatch((0.1, 0.8), 0.8, 0.15, 
                                   boxstyle="round,pad=0.02", 
                                   facecolor=self.colors['primary'], 
                                   edgecolor='black', linewidth=2))
        ax.text(0.5, 0.875, f"Main Page\n{main_page.get('title', 'Unknown')}", 
                ha='center', va='center', fontsize=12, color='white', weight='bold')
        
        # フレーム構造
        frames = main_page.get('frames', [])
        if frames:
            frame_width = 0.8 / len(frames)
            for i, frame in enumerate(frames):
                x = 0.1 + i * frame_width
                y = 0.5
                
                # フレームボックス
                ax.add_patch(FancyBboxPatch((x, y), frame_width-0.02, 0.2, 
                                           boxstyle="round,pad=0.01", 
                                           facecolor=self.colors['secondary'], 
                                           edgecolor='black', linewidth=1))
                
                # フレーム名とURL
                frame_name = frame.get('name', f'Frame {i}')
                frame_src = frame.get('src', '')
                frame_text = f"{frame_name}\n{urlparse(frame_src).path}"
                
                ax.text(x + frame_width/2, y + 0.1, frame_text, 
                        ha='center', va='center', fontsize=9, color='white')
                
                # 接続線
                ax.plot([0.5, x + frame_width/2], [0.8, y + 0.2], 
                       'k-', alpha=0.6, linewidth=1)
        
        # サブページ
        subpages = [p for p in pages if p['url'] != target_url]
        if subpages:
            subpage_width = 0.8 / max(len(subpages), 1)
            for i, page in enumerate(subpages):
                x = 0.1 + i * subpage_width
                y = 0.1
                
                # サブページボックス
                ax.add_patch(FancyBboxPatch((x, y), subpage_width-0.02, 0.15, 
                                           boxstyle="round,pad=0.01", 
                                           facecolor=self.colors['accent'], 
                                           edgecolor='black', linewidth=1))
                
                page_title = page.get('title', 'Unknown')
                page_path = urlparse(page['url']).path
                page_text = f"{page_title}\n{page_path}"
                
                ax.text(x + subpage_width/2, y + 0.075, page_text, 
                        ha='center', va='center', fontsize=8, color='black')
        
        # 統計情報
        stats = self.data.get('statistics', {})
        stats_text = f"""Pages: {stats.get('pages_discovered', 0)}
Forms: {stats.get('total_forms', 0)}
Inputs: {stats.get('total_inputs', 0)}
Security Tokens: {stats.get('total_security_tokens', 0)}"""
        
        ax.text(0.02, 0.02, stats_text, fontsize=10, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors['light']))
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('IoT Device Page Structure Analysis', fontsize=16, weight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Page structure diagram saved: {output_path}")
    
    def create_fuzzing_targets_analysis(self, output_path: str):
        """Fuzzing対象分析の作成"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        targets = self.data.get('fuzzing_targets', [])
        
        if not targets:
            fig.text(0.5, 0.5, 'No fuzzing targets data available', 
                    ha='center', va='center', fontsize=16)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            return
        
        # 1. 優先度分布
        priorities = [t.get('priority_score', 0) for t in targets]
        methods = [t.get('method', 'Unknown') for t in targets]
        
        ax1.hist(priorities, bins=10, color=self.colors['primary'], alpha=0.7, edgecolor='black')
        ax1.set_title('Fuzzing Target Priority Distribution', fontsize=14, weight='bold')
        ax1.set_xlabel('Priority Score')
        ax1.set_ylabel('Count')
        ax1.grid(True, alpha=0.3)
        
        # 2. HTTPメソッド分布
        method_counts = pd.Series(methods).value_counts()
        colors = [self.colors['secondary'], self.colors['accent'], self.colors['warning']][:len(method_counts)]
        
        wedges, texts, autotexts = ax2.pie(method_counts.values, labels=method_counts.index, 
                                          autopct='%1.1f%%', colors=colors, startangle=90)
        ax2.set_title('HTTP Methods Distribution', fontsize=14, weight='bold')
        
        # 3. 脆弱性指標
        vuln_indicators = {}
        for target in targets:
            for indicator in target.get('vulnerability_indicators', []):
                vuln_indicators[indicator] = vuln_indicators.get(indicator, 0) + 1
        
        if vuln_indicators:
            indicators = list(vuln_indicators.keys())
            counts = list(vuln_indicators.values())
            
            bars = ax3.bar(indicators, counts, color=self.colors['warning'], alpha=0.7)
            ax3.set_title('Vulnerability Indicators', fontsize=14, weight='bold')
            ax3.set_xlabel('Indicator Type')
            ax3.set_ylabel('Count')
            ax3.tick_params(axis='x', rotation=45)
            
            # 値をバーの上に表示
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
        else:
            ax3.text(0.5, 0.5, 'No vulnerability indicators', ha='center', va='center')
            ax3.set_title('Vulnerability Indicators', fontsize=14, weight='bold')
        
        # 4. エンドポイント分析
        endpoints = [urlparse(t.get('endpoint', '')).path for t in targets]
        endpoint_types = self._classify_endpoints(endpoints)
        
        if endpoint_types:
            type_counts = pd.Series(endpoint_types).value_counts()
            bars = ax4.bar(type_counts.index, type_counts.values, 
                          color=self.colors['success'], alpha=0.7)
            ax4.set_title('Endpoint Types', fontsize=14, weight='bold')
            ax4.set_xlabel('Endpoint Type')
            ax4.set_ylabel('Count')
            ax4.tick_params(axis='x', rotation=45)
            
            for bar in bars:
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
        else:
            ax4.text(0.5, 0.5, 'No endpoint data', ha='center', va='center')
            ax4.set_title('Endpoint Types', fontsize=14, weight='bold')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"🎯 Fuzzing targets analysis saved: {output_path}")
    
    def create_vulnerability_distribution(self, output_path: str):
        """脆弱性分布の作成"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # データ準備
        stats = self.data.get('statistics', {})
        vuln_indicators = stats.get('vulnerability_indicators', {})
        
        # 1. 脆弱性指標の分布
        if vuln_indicators:
            labels = list(vuln_indicators.keys())
            values = list(vuln_indicators.values())
            
            # 色の設定
            colors = []
            for label in labels:
                if 'csrf' in label.lower():
                    colors.append(self.colors['warning'])
                elif 'sql' in label.lower():
                    colors.append('#e74c3c')
                elif 'xss' in label.lower():
                    colors.append('#f39c12')
                else:
                    colors.append(self.colors['info'])
            
            wedges, texts, autotexts = ax1.pie(values, labels=labels, autopct='%1.1f%%', 
                                              colors=colors, startangle=90)
            ax1.set_title('Vulnerability Indicators Distribution', fontsize=14, weight='bold')
            
            # 凡例の追加
            ax1.legend(wedges, [f'{label}: {value}' for label, value in zip(labels, values)],
                      title="Vulnerabilities", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        else:
            ax1.text(0.5, 0.5, 'No vulnerability data available', 
                    ha='center', va='center', fontsize=12)
            ax1.set_title('Vulnerability Indicators Distribution', fontsize=14, weight='bold')
        
        # 2. セキュリティ指標の比較
        security_metrics = {
            'CSRF Protected Pages': stats.get('pages_with_csrf', 0),
            'Non-CSRF Pages': stats.get('pages_discovered', 0) - stats.get('pages_with_csrf', 0),
            'High Priority Targets': stats.get('high_priority_targets', 0),
            'Total Security Tokens': stats.get('total_security_tokens', 0)
        }
        
        metrics_names = list(security_metrics.keys())
        metrics_values = list(security_metrics.values())
        
        bars = ax2.bar(metrics_names, metrics_values, 
                      color=[self.colors['success'], self.colors['warning'], 
                            self.colors['primary'], self.colors['accent']])
        
        ax2.set_title('Security Metrics Overview', fontsize=14, weight='bold')
        ax2.set_ylabel('Count')
        ax2.tick_params(axis='x', rotation=45)
        
        # 値をバーの上に表示
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"🔒 Vulnerability distribution saved: {output_path}")
    
    def create_security_dashboard(self, output_path: str):
        """セキュリティ分析ダッシュボードの作成"""
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
        
        # タイトル
        fig.suptitle('IoT Device Security Analysis Dashboard', fontsize=20, weight='bold')
        
        # 基本統計
        stats = self.data.get('statistics', {})
        session_info = self.data.get('session_info', {})
        
        # 1. 概要情報 (左上)
        ax1 = fig.add_subplot(gs[0, :2])
        overview_text = f"""
Target URL: {session_info.get('target_url', 'Unknown')}
Scan Date: {datetime.fromtimestamp(session_info.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}
Total Pages: {stats.get('pages_discovered', 0)}
Total Forms: {stats.get('total_forms', 0)}
Total Inputs: {stats.get('total_inputs', 0)}
High Priority Targets: {stats.get('high_priority_targets', 0)}
Average Page Complexity: {stats.get('average_page_complexity', 0):.1f}
        """
        ax1.text(0.05, 0.95, overview_text, transform=ax1.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", 
                facecolor=self.colors['light']))
        ax1.set_title('Scan Overview', fontsize=14, weight='bold')
        ax1.axis('off')
        
        # 2. リスク評価 (右上)
        ax2 = fig.add_subplot(gs[0, 2:])
        risk_score = self._calculate_risk_score(stats)
        risk_color = self._get_risk_color(risk_score)
        
        # リスクメーター
        theta = np.linspace(0, np.pi, 100)
        r = np.ones_like(theta)
        ax2.plot(theta, r, 'k-', linewidth=3)
        
        # リスクレベル表示
        risk_angle = np.pi * (1 - risk_score / 100)
        ax2.arrow(0, 0, np.cos(risk_angle), np.sin(risk_angle), 
                 head_width=0.1, head_length=0.1, fc=risk_color, ec=risk_color)
        
        ax2.text(0, -0.3, f'Risk Score: {risk_score}/100', ha='center', fontsize=14, weight='bold')
        ax2.text(0, -0.5, self._get_risk_level(risk_score), ha='center', fontsize=12, color=risk_color)
        ax2.set_xlim(-1.5, 1.5)
        ax2.set_ylim(-0.7, 1.2)
        ax2.set_aspect('equal')
        ax2.axis('off')
        ax2.set_title('Risk Assessment', fontsize=14, weight='bold')
        
        # 3. 脆弱性分布 (左中)
        ax3 = fig.add_subplot(gs[1, :2])
        vuln_indicators = stats.get('vulnerability_indicators', {})
        if vuln_indicators:
            labels = list(vuln_indicators.keys())
            values = list(vuln_indicators.values())
            colors = [self.colors['warning'], self.colors['warning'], self.colors['info']][:len(labels)]
            
            bars = ax3.bar(labels, values, color=colors)
            ax3.set_title('Vulnerability Indicators', fontsize=14, weight='bold')
            ax3.tick_params(axis='x', rotation=45)
            
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
        else:
            ax3.text(0.5, 0.5, 'No vulnerabilities detected', ha='center', va='center', fontsize=12)
            ax3.set_title('Vulnerability Indicators', fontsize=14, weight='bold')
        
        # 4. Fuzzing準備状況 (右中)
        ax4 = fig.add_subplot(gs[1, 2:])
        targets = self.data.get('fuzzing_targets', [])
        if targets:
            priorities = [t.get('priority_score', 0) for t in targets]
            ax4.hist(priorities, bins=8, color=self.colors['primary'], alpha=0.7, edgecolor='black')
            ax4.set_title('Fuzzing Target Priorities', fontsize=14, weight='bold')
            ax4.set_xlabel('Priority Score')
            ax4.set_ylabel('Count')
        else:
            ax4.text(0.5, 0.5, 'No fuzzing targets', ha='center', va='center', fontsize=12)
            ax4.set_title('Fuzzing Target Priorities', fontsize=14, weight='bold')
        
        # 5. 推奨事項 (下部全体)
        ax5 = fig.add_subplot(gs[2, :])
        recommendations = self.data.get('recommendations', [])
        if recommendations:
            rec_text = "Security Recommendations:\n"
            for i, rec in enumerate(recommendations, 1):
                rec_text += f"{i}. {rec}\n"
        else:
            rec_text = "No specific recommendations generated."
        
        ax5.text(0.05, 0.95, rec_text, transform=ax5.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", 
                facecolor=self.colors['light']))
        ax5.set_title('Security Recommendations', fontsize=14, weight='bold')
        ax5.axis('off')
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Security dashboard saved: {output_path}")
    
    def create_frame_relationship_graph(self, output_path: str):
        """フレーム関係図の作成"""
        fig, ax = plt.subplots(1, 1, figsize=(14, 10))
        
        # NetworkXグラフの作成
        G = nx.DiGraph()
        
        # データ準備
        pages = self.data.get('page_states', [])
        target_url = self.data.get('session_info', {}).get('target_url', '')
        
        # メインページを追加
        main_page = next((p for p in pages if p['url'] == target_url), None)
        if main_page:
            G.add_node('Main Page', type='main', title=main_page.get('title', 'Unknown'))
            
            # フレームを追加
            for frame in main_page.get('frames', []):
                frame_name = frame.get('name', 'Unknown Frame')
                frame_url = frame.get('src', '')
                
                G.add_node(frame_name, type='frame', url=frame_url)
                G.add_edge('Main Page', frame_name)
        
        # サブページを追加
        for page in pages:
            if page['url'] != target_url:
                page_name = f"Page: {urlparse(page['url']).path}"
                G.add_node(page_name, type='page', url=page['url'])
                G.add_edge('Main Page', page_name)
        
        if G.number_of_nodes() == 0:
            ax.text(0.5, 0.5, 'No frame relationship data available', 
                   ha='center', va='center', fontsize=16)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            return
        
        # レイアウト計算
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # ノードの描画
        node_colors = []
        node_sizes = []
        
        for node in G.nodes():
            node_data = G.nodes[node]
            if node_data.get('type') == 'main':
                node_colors.append(self.colors['primary'])
                node_sizes.append(3000)
            elif node_data.get('type') == 'frame':
                node_colors.append(self.colors['secondary'])
                node_sizes.append(2000)
            else:
                node_colors.append(self.colors['accent'])
                node_sizes.append(1500)
        
        # グラフの描画
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                              alpha=0.8, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, 
                              arrowsize=20, arrowstyle='->', ax=ax)
        
        # ラベルの描画
        labels = {}
        for node in G.nodes():
            if len(node) > 15:
                labels[node] = node[:15] + '...'
            else:
                labels[node] = node
        
        nx.draw_networkx_labels(G, pos, labels, font_size=9, font_color='white', 
                               font_weight='bold', ax=ax)
        
        ax.set_title('Frame and Page Relationship Graph', fontsize=16, weight='bold')
        ax.axis('off')
        
        # 凡例
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors['primary'], 
                      markersize=15, label='Main Page'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors['secondary'], 
                      markersize=12, label='Frame'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors['accent'], 
                      markersize=10, label='Sub Page')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"🕸️ Frame relationship graph saved: {output_path}")
    
    def create_comprehensive_report(self, output_path: str):
        """総合レポートの作成"""
        fig = plt.figure(figsize=(20, 24))
        gs = fig.add_gridspec(6, 4, hspace=0.4, wspace=0.3)
        
        # メインタイトル
        fig.suptitle('IoT Device Security Analysis - Comprehensive Report', 
                    fontsize=24, weight='bold', y=0.98)
        
        # セッション情報
        session_info = self.data.get('session_info', {})
        stats = self.data.get('statistics', {})
        
        # 1. エグゼクティブサマリー
        ax1 = fig.add_subplot(gs[0, :])
        summary_text = f"""
EXECUTIVE SUMMARY
Target: {session_info.get('target_url', 'Unknown')}
Scan Date: {datetime.fromtimestamp(session_info.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}

FINDINGS OVERVIEW:
• {stats.get('pages_discovered', 0)} pages discovered with {stats.get('total_forms', 0)} forms and {stats.get('total_inputs', 0)} input fields
• {stats.get('high_priority_targets', 0)} high-priority fuzzing targets identified
• {len(stats.get('vulnerability_indicators', {}))} different vulnerability types detected
• {stats.get('pages_with_csrf', 0)} pages with CSRF protection out of {stats.get('pages_discovered', 0)} total pages

RISK ASSESSMENT: {self._get_risk_level(self._calculate_risk_score(stats))} ({self._calculate_risk_score(stats)}/100)
        """
        
        ax1.text(0.02, 0.98, summary_text, transform=ax1.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", 
                facecolor=self.colors['light'], alpha=0.8))
        ax1.axis('off')
        
        # 2-6. 他の可視化を小さなサブプロットとして配置
        # (既存の関数を再利用して小さなバージョンを作成)
        
        # 2. ページ構造 (簡易版)
        self._create_mini_page_structure(fig.add_subplot(gs[1, :2]))
        
        # 3. 脆弱性分布 (簡易版)
        self._create_mini_vulnerability_chart(fig.add_subplot(gs[1, 2:]))
        
        # 4. Fuzzing対象 (簡易版)
        self._create_mini_fuzzing_targets(fig.add_subplot(gs[2, :2]))
        
        # 5. セキュリティメトリクス (簡易版)
        self._create_mini_security_metrics(fig.add_subplot(gs[2, 2:]))
        
        # 6. 詳細な推奨事項
        ax6 = fig.add_subplot(gs[3:5, :])
        recommendations = self.data.get('recommendations', [])
        detailed_recommendations = self._generate_detailed_recommendations(stats)
        
        all_recommendations = recommendations + detailed_recommendations
        
        if all_recommendations:
            rec_text = "DETAILED SECURITY RECOMMENDATIONS:\n\n"
            for i, rec in enumerate(all_recommendations, 1):
                rec_text += f"{i}. {rec}\n\n"
        else:
            rec_text = "No specific security recommendations generated."
        
        ax6.text(0.02, 0.98, rec_text, transform=ax6.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", 
                facecolor=self.colors['light'], alpha=0.8))
        ax6.set_title('Security Recommendations', fontsize=14, weight='bold')
        ax6.axis('off')
        
        # 7. 技術的詳細
        ax7 = fig.add_subplot(gs[5, :])
        tech_details = self._generate_technical_details()
        ax7.text(0.02, 0.98, tech_details, transform=ax7.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.5", 
                facecolor=self.colors['light'], alpha=0.8))
        ax7.set_title('Technical Details', fontsize=14, weight='bold')
        ax7.axis('off')
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📋 Comprehensive report saved: {output_path}")
    
    # ヘルパーメソッド
    def _build_page_hierarchy(self, pages: List[Dict]) -> Dict:
        """ページ階層の構築"""
        target_url = self.data.get('session_info', {}).get('target_url', '')
        main_page = next((p for p in pages if p['url'] == target_url), {})
        
        return {
            'main': main_page,
            'subpages': [p for p in pages if p['url'] != target_url]
        }
    
    def _classify_endpoints(self, endpoints: List[str]) -> List[str]:
        """エンドポイントの分類"""
        classifications = []
        for endpoint in endpoints:
            if 'admin' in endpoint.lower() or 'config' in endpoint.lower():
                classifications.append('Admin/Config')
            elif 'api' in endpoint.lower():
                classifications.append('API')
            elif 'login' in endpoint.lower() or 'auth' in endpoint.lower():
                classifications.append('Authentication')
            elif endpoint.endswith('.php'):
                classifications.append('PHP Page')
            elif endpoint.endswith('.html'):
                classifications.append('HTML Page')
            else:
                classifications.append('Other')
        return classifications
    
    def _calculate_risk_score(self, stats: Dict) -> int:
        """リスクスコアの計算"""
        score = 0
        
        # 脆弱性指標による加算
        vuln_indicators = stats.get('vulnerability_indicators', {})
        for indicator, count in vuln_indicators.items():
            if 'csrf' in indicator.lower():
                score += count * 20
            elif 'sql' in indicator.lower():
                score += count * 25
            elif 'xss' in indicator.lower():
                score += count * 15
            else:
                score += count * 10
        
        # CSRF保護の欠如
        pages_total = stats.get('pages_discovered', 1)
        pages_with_csrf = stats.get('pages_with_csrf', 0)
        csrf_ratio = pages_with_csrf / pages_total
        if csrf_ratio < 0.5:
            score += 30
        
        # 高優先度ターゲットの存在
        high_priority = stats.get('high_priority_targets', 0)
        if high_priority > 0:
            score += min(high_priority * 5, 20)
        
        return min(score, 100)
    
    def _get_risk_color(self, score: int) -> str:
        """リスクスコアに基づく色の取得"""
        if score >= 70:
            return self.colors['warning']
        elif score >= 40:
            return self.colors['accent']
        else:
            return self.colors['success']
    
    def _get_risk_level(self, score: int) -> str:
        """リスクレベルの取得"""
        if score >= 70:
            return 'HIGH RISK'
        elif score >= 40:
            return 'MEDIUM RISK'
        else:
            return 'LOW RISK'
    
    def _create_mini_page_structure(self, ax):
        """ミニページ構造図"""
        pages = self.data.get('page_states', [])
        if not pages:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center')
            ax.set_title('Page Structure', fontsize=12, weight='bold')
            return
        
        # 簡単な棒グラフで表現
        main_page = pages[0] if pages else {}
        frame_count = len(main_page.get('frames', []))
        form_count = len(main_page.get('forms', []))
        
        categories = ['Frames', 'Forms', 'Pages']
        values = [frame_count, form_count, len(pages)]
        
        bars = ax.bar(categories, values, color=[self.colors['primary'], self.colors['secondary'], self.colors['accent']])
        ax.set_title('Page Structure Overview', fontsize=12, weight='bold')
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom')
    
    def _create_mini_vulnerability_chart(self, ax):
        """ミニ脆弱性チャート"""
        stats = self.data.get('statistics', {})
        vuln_indicators = stats.get('vulnerability_indicators', {})
        
        if vuln_indicators:
            labels = list(vuln_indicators.keys())
            values = list(vuln_indicators.values())
            
            wedges, texts = ax.pie(values, labels=labels, startangle=90)
            ax.set_title('Vulnerability Distribution', fontsize=12, weight='bold')
        else:
            ax.text(0.5, 0.5, 'No vulnerabilities\ndetected', ha='center', va='center')
            ax.set_title('Vulnerability Distribution', fontsize=12, weight='bold')
    
    def _create_mini_fuzzing_targets(self, ax):
        """ミニFuzzing対象チャート"""
        targets = self.data.get('fuzzing_targets', [])
        if targets:
            priorities = [t.get('priority_score', 0) for t in targets]
            ax.hist(priorities, bins=5, color=self.colors['primary'], alpha=0.7)
            ax.set_title('Fuzzing Target Priorities', fontsize=12, weight='bold')
            ax.set_xlabel('Priority Score')
        else:
            ax.text(0.5, 0.5, 'No fuzzing\ntargets', ha='center', va='center')
            ax.set_title('Fuzzing Target Priorities', fontsize=12, weight='bold')
    
    def _create_mini_security_metrics(self, ax):
        """ミニセキュリティメトリクス"""
        stats = self.data.get('statistics', {})
        
        metrics = {
            'CSRF Protected': stats.get('pages_with_csrf', 0),
            'High Priority': stats.get('high_priority_targets', 0),
            'Security Tokens': stats.get('total_security_tokens', 0)
        }
        
        ax.bar(metrics.keys(), metrics.values(), 
               color=[self.colors['success'], self.colors['warning'], self.colors['info']])
        ax.set_title('Security Metrics', fontsize=12, weight='bold')
        ax.tick_params(axis='x', rotation=45)
    
    def _generate_detailed_recommendations(self, stats: Dict) -> List[str]:
        """詳細な推奨事項の生成"""
        recommendations = []
        
        # CSRF保護の評価
        pages_total = stats.get('pages_discovered', 1)
        pages_with_csrf = stats.get('pages_with_csrf', 0)
        if pages_with_csrf < pages_total:
            recommendations.append(
                f"Implement CSRF protection for {pages_total - pages_with_csrf} unprotected pages. "
                "Consider using synchronizer tokens or double-submit cookies."
            )
        
        # 入力検証の推奨
        total_inputs = stats.get('total_inputs', 0)
        if total_inputs > 0:
            recommendations.append(
                f"Implement comprehensive input validation for {total_inputs} input fields. "
                "Use whitelist validation, parameterized queries, and output encoding."
            )
        
        # セキュリティヘッダーの推奨
        recommendations.append(
            "Implement security headers including Content-Security-Policy, "
            "X-Frame-Options, X-XSS-Protection, and Strict-Transport-Security."
        )
        
        # 認証の強化
        recommendations.append(
            "Consider implementing multi-factor authentication and session timeout mechanisms."
        )
        
        return recommendations
    
    def _generate_technical_details(self) -> str:
        """技術的詳細の生成"""
        session_info = self.data.get('session_info', {})
        stats = self.data.get('statistics', {})
        
        return f"""
TECHNICAL ANALYSIS DETAILS:

Crawl Statistics:
• Total pages analyzed: {stats.get('pages_discovered', 0)}
• Total forms discovered: {stats.get('total_forms', 0)}
• Total input fields: {stats.get('total_inputs', 0)}
• Average page complexity: {stats.get('average_page_complexity', 0):.2f}

Security Analysis:
• Pages with CSRF protection: {stats.get('pages_with_csrf', 0)}
• Security tokens detected: {stats.get('total_security_tokens', 0)}
• High-priority fuzzing targets: {stats.get('high_priority_targets', 0)}

Fuzzing Preparation:
• Total fuzzing targets identified: {session_info.get('total_fuzzing_targets', 0)}
• Navigation paths mapped: {session_info.get('total_navigation_paths', 0)}
• Session reproducibility: Enabled

Methodology:
• Authentication: Automated frame-based login
• Coverage: Comprehensive page and frame analysis
• Analysis: DOM structure, form extraction, security token detection
• Prioritization: Risk-based fuzzing target scoring
        """

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fuzzing Crawl Results Visualization Generator")
    parser.add_argument("--input", default="fuzzing_test_results.json", 
                       help="Input JSON file from fuzzing_page_crawler.py")
    parser.add_argument("--output", default="visualizations", 
                       help="Output directory for visualizations")
    
    args = parser.parse_args()
    
    # 可視化生成
    generator = FuzzingVisualizationGenerator(args.input)
    output_dir = generator.generate_all_visualizations(args.output)
    
    print(f"\n🎉 Visualization generation completed!")
    print(f"📁 All files saved to: {output_dir}")
    print(f"📊 Generated visualizations:")
    print(f"  • Page structure diagram")
    print(f"  • Fuzzing targets analysis")
    print(f"  • Vulnerability distribution")
    print(f"  • Security dashboard")
    print(f"  • Frame relationship graph")
    print(f"  • Comprehensive report")

if __name__ == "__main__":
    main()