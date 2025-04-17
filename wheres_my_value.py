import streamlit as st
from bs4 import BeautifulSoup, NavigableString, Tag
from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import requests

# ========== Simplified CrawlerConfig and WebCrawler ==========
@dataclass
class CrawlerConfig:
    base_url: str
    search_values: List[str]
    sleep_time: float
    timeout: float
    max_pages: int
    max_depth: int
    max_workers: int
    verbose: bool
    export_results: bool
    respect_robots: bool
    use_history: bool
    history_file: Optional[str]

class WebCrawler:
    def __init__(self, config: CrawlerConfig):
        self.config = config

    def crawl_and_search(self, searches: List[Tuple[str, str]]) -> Dict[str, List[Tuple[str, Any]]]:
        try:
            res = requests.get(self.config.base_url, timeout=self.config.timeout)
            soup = BeautifulSoup(res.text, 'html.parser')
            results = {}
            for search_type, value in searches:
                if search_type == 'text':
                    matches = soup.find_all(string=lambda text: value.lower() in str(text).lower())
                elif search_type == 'id':
                    matches = soup.find_all(id=lambda x: x and value.lower() in x.lower())
                elif search_type == 'class':
                    matches = soup.find_all(class_=lambda x: x and value in (x if isinstance(x, str) else ' '.join(x)))
                elif search_type == 'attr':
                    matches = soup.find_all(attrs={value: True})
                else:
                    matches = []
                results[f"{search_type}:{value}"] = [(self.config.base_url, m) for m in matches]
            return results
        except Exception as e:
            return {"error": [(self.config.base_url, str(e))]}
# =============================================================

# ========== Streamlit UI ==========
st.set_page_config(page_title="Where’s My Value?", layout="centered")
st.title("🔍 Where’s My Value?")

url = st.text_input("Enter a URL to crawl (e.g., https://example.com)")
search_values_input = st.text_input("Enter values to search for (comma-separated)")
start_button = st.button("Start Crawling")

if start_button and url and search_values_input:
    search_values = [v.strip() for v in search_values_input.split(',')]

    config = CrawlerConfig(
        base_url=url,
        search_values=search_values,
        sleep_time=1.0,
        timeout=10.0,
        max_pages=30,
        max_depth=1,
        max_workers=1,
        verbose=False,
        export_results=False,
        respect_robots=False,
        use_history=False,
        history_file=None
    )

    crawler = WebCrawler(config)
    searches = [(t, v) for v in config.search_values for t in ['text', 'id', 'class', 'attr']]
    results = crawler.crawl_and_search(searches)

    st.markdown("### ✅ Results")
    for key, matches in results.items():
        st.markdown(f"**{key}** – {len(matches)} matches")
        for url, el in matches[:3]:
            if isinstance(el, NavigableString):
                st.write(f"🔗 URL: {url}")
                st.code(str(el).strip())
            elif hasattr(el, 'text'):
                st.write(f"🔗 URL: {url}")
                st.code(el.text.strip())
            else:
                st.write(f"🔗 URL: {url}")
                st.code(str(el))
