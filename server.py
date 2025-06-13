from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from typing import List, Optional

from wheres_my_value import WebCrawler, CrawlerConfig

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_index() -> FileResponse:
    """Serve the main HTML page."""
    return FileResponse("static/index.html")

class CrawlRequest(BaseModel):
    base_url: HttpUrl
    search_values: List[str]
    max_pages: Optional[int] = 100

class CrawlResult(BaseModel):
    found_values: List[str]
    pages_visited: int
    errors: int

@app.post('/crawl', response_model=CrawlResult)
def crawl(request: CrawlRequest):
    """Run a crawl job and return the summarized results.

    Parameters
    ----------
    request: CrawlRequest
        Crawler settings provided by the API client.

    Returns
    -------
    CrawlResult
        Summary of found values, pages visited and error count.
    """
    config = CrawlerConfig(
        base_url=str(request.base_url),
        search_values=request.search_values,
        sleep_time=1.0,
        timeout=10.0,
        max_pages=request.max_pages or 100,
        max_depth=5,
        max_workers=1,
        verbose=False,
        export_results=False,
        respect_robots=True,
        use_history=False,
        history_file=None,
    )

    crawler = WebCrawler(config)
    searches = []
    for val in config.search_values:
        searches.extend([
            ('text', val),
            ('id', val),
            ('class', val),
            ('attr', val),
        ])

    try:
        results = crawler.crawl_and_search(searches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return CrawlResult(
        found_values=sorted(list(crawler.found_values)),
        pages_visited=crawler.stats.pages_visited,
        errors=crawler.stats.error_count,
    )
