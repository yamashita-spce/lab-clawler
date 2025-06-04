import requests
import argparse
import os

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def fetch_page(url: str) -> str:
    """
    指定されたURLのHTMLコンテンツを取得する
    """
    try:
        response = requests.get(url)
        response.raise_for_status() # HTTPエラーが発生した場合に例外を発生させる
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def save_html(url: str, html_content: str, output_dir: str = "crawl_output"):
    """
    取得したHTMLコンテンツをファイルに保存する
    """
    ensure_dir(output_dir)
    # URLからファイル名を生成 (簡易版)
    filename = url.replace("http://", "").replace("https://", "").replace("/", "_").replace(":", "_") + ".html"
    filepath = os.path.join(output_dir, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Saved HTML to {filepath}")
    except IOError as e:
        print(f"Error saving HTML to {filepath}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="シンプルなWebクローラー"
    )
    parser.add_argument('url', help='対象のURL')
    parser.add_argument('-o', '--output', default='crawl_output',
                        help='結果保存ディレクトリ (デフォルト: crawl_output)')

    args = parser.parse_args()

    print(f"Fetching {args.url}...")
    html_content = fetch_page(args.url)

    if html_content:
        save_html(args.url, html_content, args.output)
    else:
        print("Failed to fetch page.")
