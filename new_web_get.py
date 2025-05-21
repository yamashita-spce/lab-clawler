#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discover_endpoints_fixed_all.py

Selenium を使って、JavaScript 実行後の全フレームを巡回し、
各フレームが最終的に読み込んでいる URL（エンドポイント）を取得し、
すべてのフレームの HTML を保存するスクリプトです。
"""

import os
import time
import argparse
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def sanitize_filename(url: str) -> str:
    p = urlparse(url)
    name = p.netloc + p.path
    # ファイル名に使えない文字をアンダースコアに置換
    return name.strip('/').replace('/', '_').replace(':', '_') + '.html'

def discover_endpoints(base_url: str, wait: int, output_dir: str):
    # ヘッドレス Chrome 起動
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=opts)

    try:
        driver.get(base_url)
        time.sleep(wait)

        # まずは全フレーム要素を取得
        frames = driver.find_elements(By.TAG_NAME, 'frame')
        print(f"[+] Found {len(frames)} frames after {wait}s")
        ensure_dir(output_dir)

        for frame in frames:
            # ループのたびに必ずデフォルトコンテキストへ
            driver.switch_to.default_content()

            # 属性名を先に取得しておく
            name = frame.get_attribute('name') or '(no-name)'
            src  = frame.get_attribute('src')  or '(no-src)'

            # フレームに切り替え
            driver.switch_to.frame(frame)

            # 実際に読み込まれた URL を取得
            current_url = driver.execute_script("return window.location.href;")
            print(f"  - frame '{name}' (src={src}): {current_url}")

            # 全フレームの HTML を保存
            html = driver.page_source
            fn = sanitize_filename(current_url)
            path = os.path.join(output_dir, fn)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"      → Saved frame '{name}' HTML to: {path}")

    finally:
        driver.quit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Selenium で動的フレームの最終 URL を取得し、全フレームの HTML を保存します"
    )
    parser.add_argument('url', help='ベース URL（例: http://192.168.0.1/）')
    parser.add_argument('-w', '--wait', type=int, default=3,
                        help='JavaScript 実行待機秒数 (デフォルト: 3秒)')
    parser.add_argument('-o', '--output', default='frames_html',
                        help='HTML 保存ディレクトリ (デフォルト: frames_html)')
    args = parser.parse_args()

    discover_endpoints(args.url, args.wait, args.output)
