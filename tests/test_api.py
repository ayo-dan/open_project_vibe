import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server

class DummyCrawler:
    def __init__(self, config):
        self.config = config
        self.stats = type("Stats", (), {"pages_visited": 1, "error_count": 0})()
        self.found_values = {"match"}

    def crawl_and_search(self, searches):
        return {"text:match": [(self.config.base_url, "match")]} 


def test_crawl_endpoint(monkeypatch):
    monkeypatch.setattr(server, "WebCrawler", DummyCrawler)
    client = TestClient(server.app)
    payload = {
        "base_url": "https://example.com",
        "search_values": ["match"],
        "max_pages": 5
    }
    response = client.post("/crawl", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "found_values": ["match"],
        "pages_visited": 1,
        "errors": 0
    }

