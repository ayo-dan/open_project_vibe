import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException

# Allow import from repository root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wheres_my_value import WebCrawler, CrawlerConfig


def make_config(**overrides) -> CrawlerConfig:
    base = dict(
        base_url="https://example.com",
        search_values=[],
        sleep_time=0.0,
        timeout=1.0,
        max_pages=10,
        max_depth=2,
        max_workers=1,
        verbose=False,
        export_results=False,
        respect_robots=False,
        use_history=False,
        history_file=None,
    )
    base.update(overrides)
    return CrawlerConfig(**base)


@pytest.fixture
def mock_request_success(monkeypatch):
    def _mock(url: str, text: str = "ok", status: int = 200):
        response = requests.Response()
        response.status_code = status
        response._content = text.encode()
        response.url = url
        response.raise_for_status = lambda: None

        def fake_get(*args, **kwargs):
            return response

        monkeypatch.setattr(requests, "get", fake_get)
        return response

    return _mock


@pytest.fixture
def mock_request_failure(monkeypatch):
    def _mock():
        def fake_get(*args, **kwargs):
            raise RequestException("boom")

        monkeypatch.setattr(requests, "get", fake_get)

    return _mock


def test_is_valid_url():
    crawler = WebCrawler(make_config())
    assert crawler.is_valid_url("https://example.com/page")
    assert not crawler.is_valid_url("https://other.com/page")
    assert not crawler.is_valid_url("https://example.com/image.jpg")


def test_get_links():
    crawler = WebCrawler(make_config())
    html = """
    <html><body>
    <a href="/page1">one</a>
    <a href="https://example.com/page2">two</a>
    <a href="https://other.com/page3">three</a>
    <a href="/file.pdf">skip</a>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = crawler.get_links(soup, "https://example.com", 0)
    assert links == {
        "https://example.com/page1": 1,
        "https://example.com/page2": 1,
    }


def test_history_save_and_load(tmp_path):
    history = tmp_path / "history.json"
    config = make_config(use_history=True, history_file=str(history))
    crawler = WebCrawler(config)
    crawler.visited_urls = {"https://example.com"}
    crawler.save_history()
    assert history.exists()

    new_crawler = WebCrawler(config)
    new_crawler.load_history()
    assert new_crawler.visited_urls == {"https://example.com"}


def test_make_request_success(mock_request_success):
    crawler = WebCrawler(make_config())
    url = "https://example.com/page"
    mock_request_success(url, "hello", 200)
    resp = crawler.make_request(url)
    assert resp is not None and resp.status_code == 200


def test_make_request_failure(mock_request_failure):
    crawler = WebCrawler(make_config())
    url = "https://example.com/bad"
    mock_request_failure()
    resp = crawler.make_request(url)
    assert resp is None
    assert crawler.stats.error_count == 1
