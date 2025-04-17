
import streamlit as st
from wheres_my_value import CrawlerConfig, WebCrawler, NavigableString
import os
from typing import Tuple, List

st.set_page_config(page_title="Where's My Value?", layout="wide")
st.title("🔍 Where’s My Value? — Full Crawler Edition")

with st.form("crawler_form"):
    url = st.text_input("Enter a base URL to crawl", "https://example.com")
    search_values_input = st.text_input("Search for (comma-separated)", "contact, form")
    max_pages = st.number_input("Max pages to search", min_value=1, max_value=10000, value=100)
    max_depth = st.slider("Max crawl depth", min_value=1, max_value=10, value=3)
    sleep_time = st.slider("Sleep time between requests (sec)", 0.1, 5.0, 1.0)
    max_workers = st.slider("Number of concurrent workers", 1, 10, 2)
    timeout = st.number_input("Request timeout (sec)", min_value=1, max_value=30, value=10)
    verbose = st.checkbox("Verbose logging", False)
    export_results = st.checkbox("Export results to file", False)
    respect_robots = st.checkbox("Respect robots.txt", False)
    use_history = st.checkbox("Use visited history", False)
    submitted = st.form_submit_button("Start Crawling")

if submitted:
    search_values = [v.strip() for v in search_values_input.split(',') if v.strip()]
    history_file = os.path.join(os.getcwd(), "crawler_history.json") if use_history else None

    config = CrawlerConfig(
        base_url=url,
        search_values=search_values,
        sleep_time=sleep_time,
        timeout=timeout,
        max_pages=max_pages,
        max_depth=max_depth,
        max_workers=max_workers,
        verbose=verbose,
        export_results=export_results,
        respect_robots=respect_robots,
        use_history=use_history,
        history_file=history_file
    )

    searches: List[Tuple[str, str]] = []
    for v in config.search_values:
        searches.extend([
            ('text', v),
            ('id', v),
            ('class', v),
            ('attr', v)
        ])

    st.write("Starting crawl with the following config:")
    st.json(config.__dict__)

    crawler = WebCrawler(config)
    with st.spinner("Crawling in progress..."):
        results = crawler.crawl_and_search(searches)

    st.markdown("### ✅ Results")
    if not results:
        st.warning("No results found.")
    else:
        for key, matches in results.items():
            st.markdown(f"**{key}** – {len(matches)} matches")
            for url, element in matches[:3]:  # Show a sample
                st.markdown(f"🔗 [URL]({url})")
                if isinstance(element, NavigableString):
                    st.code(str(element).strip())
                elif hasattr(element, 'text'):
                    st.code(element.text.strip())
                else:
                    st.code(str(element))
