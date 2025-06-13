"""FastAPI server exposing an endpoint to run the crawler.

The ``/crawl`` route accepts crawler configuration fields and returns the
results produced by :func:`run_crawl` as JSON.
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

from wheres_my_value import CrawlerConfig, run_crawl

app = FastAPI()


class CrawlRequest(BaseModel):
    """Parameters accepted by the ``/crawl`` endpoint."""

    base_url: HttpUrl
    search_values: List[str]
    sleep_time: float = 2.0
    timeout: float = 10.0
    max_pages: int = 100
    max_depth: int = 5
    max_workers: int = 1
    verbose: bool = False
    export_results: bool = False
    respect_robots: bool = True
    use_history: bool = False
    history_file: Optional[str] = None


@app.post("/crawl")
def crawl_endpoint(config: CrawlRequest) -> Dict[str, Any]:
    """Execute the crawler with the provided configuration."""

    crawler_config = CrawlerConfig(**config.model_dump())
    return run_crawl(crawler_config)
