from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from wheres_my_value import CrawlerConfig, crawl_with_config

app = FastAPI()

class CrawlerConfigModel(BaseModel):
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


def serialize_results(results: Dict[str, List[tuple]]) -> Dict[str, List[Dict[str, Any]]]:
    serialized: Dict[str, List[Dict[str, Any]]] = {}
    for key, matches in results.items():
        search_type, value = key.split(":", 1)
        for url, element in matches:
            text = element.get_text(strip=True) if hasattr(element, "get_text") else str(element).strip()
            serialized.setdefault(value, []).append({
                "search_type": search_type,
                "url": url,
                "text": text,
            })
    return serialized


@app.post("/crawl")
async def crawl(config: CrawlerConfigModel):
    crawler_config = CrawlerConfig(**config.model_dump())
    results, _ = crawl_with_config(crawler_config)
    return serialize_results(results)
