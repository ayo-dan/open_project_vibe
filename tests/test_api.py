import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import api.server as server


def test_crawl_endpoint(monkeypatch):
    def fake_run_crawl(config):
        return {"text:match": [{"url": config.base_url, "text": "match"}]}

    monkeypatch.setattr(server, "run_crawl", fake_run_crawl)
    client = TestClient(server.app)
    payload = {
        "base_url": "https://example.com",
        "search_values": ["match"],
        "max_pages": 5,
    }
    response = client.post("/crawl", json=payload)
    assert response.status_code == 200
    assert response.json() == {
        "text:match": [{"url": "https://example.com/", "text": "match"}]
    }
