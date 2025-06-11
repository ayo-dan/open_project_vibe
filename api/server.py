from typing import List, Optional, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel

from wheres_my_value import CrawlerConfig, run_crawl

app = FastAPI()

class CrawlRequest(BaseModel):
    base_url: str
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
    crawler_config = CrawlerConfig(
        base_url=config.base_url,
        search_values=config.search_values,
        sleep_time=config.sleep_time,
        timeout=config.timeout,
        max_pages=config.max_pages,
        max_depth=config.max_depth,
        max_workers=config.max_workers,
        verbose=config.verbose,
        export_results=config.export_results,
        respect_robots=config.respect_robots,
        use_history=config.use_history,
        history_file=config.history_file,
    )

    return run_crawl(crawler_config)
