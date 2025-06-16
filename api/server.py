"""FastAPI server exposing an endpoint to run the crawler.

The ``/crawl`` route accepts crawler configuration fields and returns the
results produced by :func:`run_crawl` as JSON.
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from wheres_my_value import CrawlerConfig, run_crawl, WebCrawler

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_index() -> FileResponse:
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


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


class CrawlSummary(BaseModel):
    """Simplified crawl results."""

    found_values: List[str]
    pages_visited: int
    errors: int


@app.post("/crawl")
def crawl_endpoint(config: CrawlRequest) -> Dict[str, Any]:
    """Execute the crawler with the provided configuration."""

    crawler_config = CrawlerConfig(**config.model_dump())
    return run_crawl(crawler_config)


@app.post("/crawl-summary", response_model=CrawlSummary)
def crawl_summary(config: CrawlRequest) -> CrawlSummary:
    """Execute the crawler and return a simplified summary."""

    crawler_config = CrawlerConfig(
        base_url=str(config.base_url),
        search_values=config.search_values,
        sleep_time=1.0,
        timeout=10.0,
        max_pages=config.max_pages or 100,
        max_depth=5,
        max_workers=1,
        verbose=False,
        export_results=False,
        respect_robots=True,
        use_history=False,
        history_file=None,
    )

    crawler = WebCrawler(crawler_config)
    searches: List[tuple[str, str]] = []
    for val in crawler_config.search_values:
        searches.extend([
            ("text", val),
            ("id", val),
            ("class", val),
            ("attr", val),
        ])

    try:
        crawler.crawl_and_search(searches)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return CrawlSummary(
        found_values=sorted(list(crawler.found_values)),
        pages_visited=crawler.stats.pages_visited,
        errors=crawler.stats.error_count,
    )
