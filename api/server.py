from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from wheres_my_value import CrawlerConfig, run_crawler, element_to_string

app = FastAPI()


class CrawlerRequest(BaseModel):
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
def crawl(config: CrawlerRequest) -> Dict[str, Any]:
    crawler_config = CrawlerConfig(**config.dict())
    results = run_crawler(crawler_config)

    serialized: Dict[str, List[Dict[str, str]]] = {}
    for key, values in results.items():
        serialized[key] = [
            {"url": url, "element": element_to_string(element)}
            for url, element in values
        ]

    return {"results": serialized}
