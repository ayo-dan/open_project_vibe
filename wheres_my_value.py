#DESCRIPTION: This is a simple webcrawler that find values/strings/etc by searching through a domain and then its pages.
#REASON: This script was originally created to locate a form by its ID on a company website that was getting hit with mass spam. The goal was to find the form by its ID via this script as opposed to looking through many different pages. Once found the form could have reCAPTCHA applied to it.
#DISCLAIMER: This script was created with the help of Cursor (AI)

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from requests.exceptions import RequestException
from typing import List, Optional, Set, Dict, Union, Tuple, Any, Callable
from urllib.parse import urljoin, urlparse
import time
import json
import os
import sys
from datetime import datetime
from urllib.robotparser import RobotFileParser
import concurrent.futures
from queue import Queue
import threading
from dataclasses import dataclass
from collections import defaultdict

# Common non-HTML file extensions to skip
SKIP_EXTENSIONS = {
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # Archives
    '.zip', '.rar', '.7z', '.tar', '.gz',
    # Media
    '.mp3', '.mp4', '.wav', '.avi', '.mov',
    # Code and Data
    '.css', '.js', '.json', '.xml', '.csv', '.txt',
    # Other
    '.ico', '.woff', '.woff2', '.ttf', '.eot', '.map'
}

# Default headers
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

@dataclass
class CrawlerConfig:
    """Configuration settings for the web crawler"""
    base_url: str
    search_values: List[str]
    sleep_time: float
    timeout: float
    max_pages: int
    max_depth: int
    max_workers: int
    verbose: bool
    export_results: bool
    respect_robots: bool
    use_history: bool
    history_file: Optional[str]

class CrawlerStats:
    """Track crawler statistics"""
    def __init__(self):
        self.pages_visited: int = 0
        self.error_count: int = 0
        self.start_time: float = time.time()
        self.error_log: List[str] = []
        self._lock = threading.Lock()
        self._last_print_time = 0
        self._last_pages = 0

    def increment_pages(self) -> None:
        with self._lock:
            self.pages_visited += 1

    def add_error(self, error_msg: str) -> None:
        with self._lock:
            self.error_count += 1
            self.error_log.append(error_msg)

    def get_elapsed_time(self) -> float:
        return time.time() - self.start_time

    def get_pages_per_minute(self) -> float:
        elapsed = self.get_elapsed_time()
        return self.pages_visited / (elapsed / 60) if elapsed > 0 else 0

    def should_print_progress(self, total: int, sleep_time: float) -> bool:
        current_time = time.time()
        time_elapsed = current_time - self._last_print_time >= sleep_time
        pages_changed = self.pages_visited > self._last_pages
        
        if time_elapsed and pages_changed:
            self._last_print_time = current_time
            self._last_pages = self.pages_visited
            return True
        return False

def print_progress(
    stats: CrawlerStats,
    total: int,
    sleep_time: float,
    bar_length: int = 50,
    callback: Optional[Callable[[int, int], None]] = None,
) -> None:
    if not stats.should_print_progress(total, sleep_time):
        return

    percentage = (stats.pages_visited / total) * 100
    filled_length = int(bar_length * stats.pages_visited // total)
    bar = '=' * filled_length + '-' * (bar_length - filled_length)

    print(
        f'\rProgress: [{bar}] {percentage:.1f}% | {stats.pages_visited}/{total} pages | '
        f'{stats.get_pages_per_minute():.1f} pages/min | {stats.get_elapsed_time():.1f}s',
        end='',
        flush=True,
    )

    if callback:
        try:
            callback(stats.pages_visited, total)
        except Exception:
            pass

class WebCrawler:
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.base_domain = urlparse(config.base_url).netloc
        self.visited_urls: Set[str] = set()
        self.url_queue = Queue()
        self.queued_urls: Set[str] = set()
        self.results_lock = threading.Lock()
        self.visited_lock = threading.Lock()
        self.queue_lock = threading.Lock()
        # Lock to guard writes to the history file
        self._history_lock = threading.Lock()
        self.stats = CrawlerStats()
        self.found_values: Set[str] = set()
        self._last_save_count = 0
        self._stop_requested = False
        self.headers = DEFAULT_HEADERS.copy()
        self._active_tasks = 0
        self._active_lock = threading.Lock()
        
        # Initialize robots.txt parser
        self.robots_parser = RobotFileParser() if config.respect_robots else None
        if config.respect_robots:
            try:
                robots_url = urljoin(config.base_url, '/robots.txt')
                self.robots_parser.set_url(robots_url)
                self.robots_parser.read()
                print("Successfully loaded robots.txt")
            except Exception as e:
                print(f"Warning: Could not load robots.txt: {e}")
                self.robots_parser = None
        
        if config.use_history:
            print(f"History file location: {config.history_file}")
            self.load_history()
        else:
            print("History tracking disabled")

    def load_history(self) -> None:
        if not self.config.use_history or not self.config.history_file:
            return
            
        try:
            if os.path.exists(self.config.history_file):
                with open(self.config.history_file, 'r') as f:
                    history = json.load(f)
                    self.visited_urls = set(history.get('visited_urls', []))
                    self._last_save_count = len(self.visited_urls)
                    print(f"Loaded {len(self.visited_urls)} previously visited URLs")
            else:
                print("No history file found. Starting fresh.")
        except Exception as e:
            print(f"Error loading history: {e}")

    def save_history(self) -> None:
        if not self.config.use_history or not self.config.history_file:
            return

        with self._history_lock:
            try:
                if self._last_save_count == len(self.visited_urls):
                    return
                with open(self.config.history_file, 'w') as f:
                    json.dump({'visited_urls': list(self.visited_urls)}, f)
                self._last_save_count = len(self.visited_urls)
                print(f"Saved {len(self.visited_urls)} visited URLs to history")
            except Exception as e:
                print(f"Error saving history: {e}")

    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            if any(url.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
                return False
            if parsed.netloc != self.base_domain:
                return False
            if self.robots_parser and not self.robots_parser.can_fetch(self.headers['User-Agent'], url):
                if self.config.verbose:
                    print(f"\nSkipping blocked URL: {url}")
                return False
            return True
        except:
            return False

    def get_links(self, soup: BeautifulSoup, current_url: str, current_depth: int) -> Dict[str, int]:
        links = {}
        max_links_per_page = 50
        try:
            for a_tag in soup.find_all('a', href=True):
                if len(links) >= max_links_per_page:
                    break
                url = urljoin(current_url, a_tag['href'])
                if self.is_valid_url(url) and current_depth < self.config.max_depth:
                    links[url] = current_depth + 1
        except Exception as e:
            if self.config.verbose:
                print(f"\nError extracting links from {current_url}: {str(e)}")
        return links

    def make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with configured settings"""
        try:
            print(f"Requesting: {url}")  # Debug line
            response = requests.get(
                url=url,
                headers=self.headers,
                timeout=self.config.timeout,
                verify=True
            )
            response.raise_for_status()
            print(f"Request successful: {url}")  # Debug line
            return response
        except Exception as e:
            print(f"Request failed: {url} - {str(e)}")  # Debug line
            self.stats.add_error(f"Error fetching {url}: {str(e)}")
            return None

    def stop(self) -> None:
        self._stop_requested = True
        while not self.url_queue.empty():
            try:
                url, _ = self.url_queue.get_nowait()
                with self.queue_lock:
                    self.queued_urls.discard(url)
            except:
                pass

    def active_task_count(self) -> int:
        with self._active_lock:
            return self._active_tasks

    def worker(self, searches: List[Tuple[str, str]], results: Dict[str, List[Tuple[str, Any]]]) -> None:
        """Worker function for concurrent crawling"""
        while not self._stop_requested:
            try:
                # Check page limit before processing new URLs
                with self.visited_lock:
                    if self.stats.pages_visited >= self.config.max_pages:
                        print(f"\nReached maximum pages limit ({self.config.max_pages})")
                        self.stop()
                        break

                # Get URL from queue with timeout
                try:
                    current_url, current_depth = self.url_queue.get(timeout=1)
                    with self.queue_lock:
                        self.queued_urls.discard(current_url)
                except:
                    continue

                with self._active_lock:
                    self._active_tasks += 1

                if current_url in self.visited_urls:
                    with self._active_lock:
                        self._active_tasks -= 1
                    continue

                print(f"\nProcessing: {current_url}")

                response = self.make_request(current_url)
                if not response:
                    with self._active_lock:
                        self._active_tasks -= 1
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Process search results
                page_results = self.search_page(soup, searches)
                with self.results_lock:
                    for search_type, value in searches:
                        key = f"{search_type}:{value}"
                        if key not in results:
                            results[key] = []
                        if page_results.get(key):
                            results[key].extend((current_url, element) for element in page_results[key])
                            if search_type == 'text':
                                self.found_values.add(value)
                                print(f"\n🎉 Found value: '{value}'!")
                                self.save_history()

                # Only add new links if we haven't reached the page limit
                if self.stats.pages_visited < self.config.max_pages:
                    if current_depth < self.config.max_depth:
                        new_links = self.get_links(soup, current_url, current_depth)
                        for url, depth in new_links.items():
                            with self.queue_lock:
                                if url not in self.visited_urls and url not in self.queued_urls:
                                    self.url_queue.put((url, depth))
                                    self.queued_urls.add(url)

                # Mark URL as visited
                with self.visited_lock:
                    self.visited_urls.add(current_url)
                    self.stats.increment_pages()

                with self._active_lock:
                    self._active_tasks -= 1

                time.sleep(self.config.sleep_time)

            except Exception as e:
                print(f"\nError in worker: {str(e)}")
                with self._active_lock:
                    if self._active_tasks > 0:
                        self._active_tasks -= 1
                continue

    def search_page(self, soup: BeautifulSoup, searches: List[Tuple[str, str]]) -> Dict[str, List[Any]]:
        results = defaultdict(list)
        for search_type, value in searches:
            key = f"{search_type}:{value}"
            results[key] = search_html(soup, search_type, value)
        return dict(results)

    def crawl_and_search(
        self,
        searches: List[Tuple[str, str]],
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, List[Tuple[str, Any]]]:
        """Crawl pages and perform searches"""
        results = defaultdict(list)
        
        print("\nStarting crawl...")
        print("Press Ctrl+C to stop at any time\n")
        
        # Test initial connection
        try:
            print(f"Testing connection to {self.config.base_url}...")
            response = self.make_request(self.config.base_url)
            if not response:
                print("Failed to connect to the base URL. Please check the URL and try again.")
                return results
            print("Successfully connected to base URL")
        except Exception as e:
            print(f"Error connecting to base URL: {str(e)}")
            return results

        # Initialize URL queue with base URL
        with self.queue_lock:
            if self.config.base_url not in self.visited_urls and self.config.base_url not in self.queued_urls:
                self.url_queue.put((self.config.base_url, 0))
                self.queued_urls.add(self.config.base_url)
        
        try:
            # Create and start worker threads
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []
                for _ in range(self.config.max_workers):
                    futures.append(executor.submit(self.worker, searches, results))
                
                # Monitor progress
                while not self._stop_requested:
                    try:
                        print_progress(
                            self.stats,
                            self.config.max_pages,
                            self.config.sleep_time,
                            callback=on_progress,
                        )
                        
                        # Check queue and worker status
                        active_workers = sum(1 for f in futures if not f.done())
                        current_queue_size = self.url_queue.qsize()
                        active_tasks = self.active_task_count()

                        print(
                            f"\rActive workers: {active_workers}, Queue size: {current_queue_size}, Processing: {active_tasks}",
                            end='',
                        )

                        if current_queue_size == 0 and active_tasks == 0:
                            print("\nQueue empty and no pages in progress. Stopping crawl...")
                            self.stop()
                            break
                        
                        time.sleep(1)  # Reduced sleep time for more responsive monitoring
                        
                    except KeyboardInterrupt:
                        print("\n\nCtrl+C detected. Stopping crawl...")
                        self.stop()
                        break
                
                # Wait for workers to complete
                for future in futures:
                    future.cancel()
                    try:
                        future.result(timeout=1)
                    except:
                        pass
            
            return dict(results)
            
        except Exception as e:
            print(f"\n\nError during crawl: {str(e)}")
            self.save_history()
            return dict(results)

def is_hidden(element: Tag) -> bool:
    """Check if an element is hidden"""
    if not isinstance(element, Tag):
        return False
        
    return (
        element.get('type') == 'hidden' or
        element.get('style', '').find('display: none') >= 0 or
        element.get('style', '').find('visibility: hidden') >= 0 or
        'hidden' in element.get('class', []) or
        element.get('aria-hidden') == 'true'
    )

def get_hidden_reason(element: Tag) -> str:
    """Determine why an element is hidden"""
    reasons = []
    if element.get('type') == 'hidden':
        reasons.append('Hidden input field')
    if element.get('style', '').find('display: none') >= 0:
        reasons.append('CSS display:none')
    if element.get('style', '').find('visibility: hidden') >= 0:
        reasons.append('CSS visibility:hidden')
    if 'hidden' in element.get('class', []):
        reasons.append('Hidden class')
    if element.get('aria-hidden') == 'true':
        reasons.append('ARIA hidden')
    return ' and '.join(reasons) if reasons else 'Unknown'

def search_html(soup: BeautifulSoup, search_type: str, value: str) -> List[Any]:
    """
    Enhanced search function that finds both visible and hidden elements
    """
    matches = []
    
    if search_type == 'text':
        # Search in all text nodes, including those in hidden elements
        matches.extend(soup.find_all(string=lambda text: value.lower() in str(text).lower()))
        
        # Search in input values
        matches.extend(soup.find_all('input', value=lambda x: x and value.lower() in x.lower()))
        
        # Search in textarea content
        matches.extend(soup.find_all('textarea', string=lambda x: x and value.lower() in x.lower()))
        
        # Search in hidden inputs
        matches.extend(soup.find_all('input', 
                                   type='hidden', 
                                   value=lambda x: x and value.lower() in x.lower()))
        
    elif search_type == 'id':
        # Search for elements with matching ID
        matches.extend(soup.find_all(id=lambda x: x and value.lower() in x.lower()))
        
        # Search for hidden inputs with matching ID
        matches.extend(soup.find_all('input', 
                                   type='hidden',
                                   id=lambda x: x and value.lower() in x.lower()))
        
    elif search_type == 'class':
        # Search for elements with matching class
        matches.extend(soup.find_all(class_=lambda x: x and value in (x if isinstance(x, str) else ' '.join(x))))
        
    elif search_type == 'attr':
        # Find elements by tag name (for custom elements)
        if value.startswith('<') and value.endswith('>'):
            # Extract tag name from <tag-name>
            tag_name = value[1:-1]
            matches.extend(soup.find_all(tag_name))
        elif '=' in value:
            # Search for specific attribute value pairs
            attr_name, attr_value = value.split('=', 1)
            # Remove quotes if present
            attr_value = attr_value.strip('"\'')
            matches.extend(soup.find_all(attrs={attr_name: attr_value}))
            
            # Special handling for custom elements with attributes
            if '-' in attr_name:  # Custom element attributes often contain hyphens
                for tag in soup.find_all():
                    if tag.has_attr(attr_name) and tag[attr_name] == attr_value:
                        matches.append(tag)
        else:
            # Search for elements with the attribute present
            matches.extend(soup.find_all(attrs={value: True}))
            
        # Search in data attributes
        for tag in soup.find_all():
            if hasattr(tag, 'attrs'):
                for attr_name, attr_value in tag.attrs.items():
                    if isinstance(attr_value, str) and value.lower() in attr_value.lower():
                        matches.append(tag)
                        break
    
    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for match in matches:
        if match not in seen:
            seen.add(match)
            unique_matches.append(match)
            
    return unique_matches

def print_element_info(element: Union[Tag, NavigableString], url: Optional[str] = None) -> None:
    """Print detailed information about found elements, including hidden ones"""
    if element is None:
        return
    
    if url:
        print(f"\nFound on page: {url}")
    
    if isinstance(element, NavigableString):
        print("Text content:")
        print(f"  {element.strip()}")
        print(f"Parent element: {element.parent.name}")
        print(f"Visibility: {'Hidden' if is_hidden(element.parent) else 'Visible'}")
        return
    
    print("Element details:")
    print(f"Tag: {element.name}")
    
    # Print attributes
    if element.attrs:
        print("Attributes:")
        for key, value in element.attrs.items():
            print(f"  {key}: {value}")
    
    # Print content
    if element.string:
        print(f"Content: {element.string.strip()}")
    elif element.text:
        print(f"Content: {element.text.strip()}")
    
    # Check if element is hidden
    if is_hidden(element):
        print("Status: Hidden element")
        print("Hidden by:", get_hidden_reason(element))
    else:
        print("Status: Visible element")

def export_results_to_file(results: Dict[str, List[Tuple[str, Any]]], search_values: List[str]) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_results_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== Search Results ===\n\n")
            f.write(f"Search performed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Search values: {', '.join(search_values)}\n\n")
            
            for search_value in search_values:
                f.write(f"\nResults for '{search_value}':\n")
                value_results = []
                
                for search_type in ['text', 'id', 'class', 'attr']:
                    key = f"{search_type}:{search_value}"
                    if key in results:
                        value_results.extend(results[key])
                
                unique_results = []
                seen = set()
                for url, element in value_results:
                    if isinstance(element, NavigableString):
                        content = element.strip()
                    else:
                        content = element.get_text().strip()
                    result_id = f"{url}|{content}"
                    
                    if result_id not in seen:
                        seen.add(result_id)
                        unique_results.append((url, element))
                
                if unique_results:
                    f.write(f"Found {len(unique_results)} unique occurrence(s):\n")
                    for url, element in unique_results:
                        f.write(f"\nFound on page: {url}\n")
                        if isinstance(element, NavigableString):
                            f.write(f"Text content: {element.strip()}\n")
                        else:
                            f.write(f"Tag: {element.name}\n")
                            if element.attrs:
                                f.write("Attributes:\n")
                                for key, value in element.attrs.items():
                                    f.write(f"  {key}: {value}\n")
                            if element.string:
                                f.write(f"Text content: {element.string.strip()}\n")
                            elif element.text:
                                f.write(f"Text content: {element.text.strip()}\n")
                else:
                    f.write("No elements found\n")
                    f.write("Note: The element might be:\n")
                    f.write("1. Not present on any crawled page\n")
                    f.write("2. On pages not yet crawled\n")
                    f.write("3. Dynamically loaded by JavaScript\n")
                    f.write("4. In a different format or have different attributes\n")
        
        print(f"\nResults exported to: {filename}")
    except Exception as e:
        print(f"Error exporting results: {e}")

def get_user_input() -> CrawlerConfig:
    print("\n=== Where's My Value Configuration ===")
    
    def get_valid_input(prompt: str, validator: Callable[[str], bool], default: Any = None) -> Any:
        while True:
            value = input(f"\n{prompt}").strip()
            if not value and default is not None:
                return default
            if validator(value):
                return value
            print("Invalid input. Please try again.")
    
    def validate_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            return (url.startswith(('http://', 'https://')) and 
                   len(url) <= 2048 and
                   bool(parsed.netloc))
        except:
            return False
    
    url = get_valid_input(
        "Enter the website URL to crawl (e.g., https://example.com): ",
        validate_url
    )
    
    def validate_search_values(values: str) -> bool:
        if not values:
            return False
        value_list = [v.strip() for v in values.split(',')]
        return all(0 < len(v) <= 100 for v in value_list)
    
    search_values = get_valid_input(
        "Enter the text or values to search for (comma-separated for multiple): ",
        validate_search_values
    ).split(',')
    
    MAX_PAGES = 1000
    max_pages = int(get_valid_input(
        f"Enter maximum number of pages to search (1-{MAX_PAGES}, default: 100): ",
        lambda x: x.isdigit() and 1 <= int(x) <= MAX_PAGES,
        "100"
    ))
    
    print("\n=== Advanced Settings ===")
    
    MIN_SLEEP = 0.1
    MAX_SLEEP = 10.0
    sleep_time = float(get_valid_input(
        f"Enter time to wait between page searches (in seconds, {MIN_SLEEP}-{MAX_SLEEP}, default: 2): ",
        lambda x: x.replace('.', '').isdigit() and MIN_SLEEP <= float(x) <= MAX_SLEEP,
        "2"
    ))
    
    MAX_WORKERS = 5
    max_workers = int(get_valid_input(
        f"Enter number of concurrent workers (1-{MAX_WORKERS}, default: 1): ",
        lambda x: x.isdigit() and 1 <= int(x) <= MAX_WORKERS,
        "1"
    ))
    
    def validate_yes_no(value: str) -> bool:
        return value.lower() in ['yes', 'no', '']
    
    respect_robots = get_valid_input(
        "Respect robots.txt? (yes/no, default: yes): ",
        validate_yes_no,
        "yes"
    ).lower() != 'no'
    
    use_history = get_valid_input(
        "Store visited URLs in history file? (yes/no, default: no): ",
        validate_yes_no,
        "no"
    ).lower() == 'yes'
    
    print("\n=== Optional Features ===")
    debug_mode = get_valid_input(
        "Enable debug mode? (yes/no, default: no): ",
        validate_yes_no,
        "no"
    ).lower() == 'yes'
    
    export_results = get_valid_input(
        "Export results to file? (yes/no, default: no): ",
        validate_yes_no,
        "no"
    ).lower() == 'yes'
    
    history_file = os.path.join(os.getcwd(), "crawler_history.json")
    if use_history:
        print(f"\nHistory file will be created at: {history_file}")
    
    return CrawlerConfig(
        base_url=url,
        search_values=[v.strip() for v in search_values],
        sleep_time=sleep_time,
        timeout=10.0,
        max_pages=max_pages,
        max_depth=5,
        max_workers=max_workers,
        verbose=debug_mode,
        export_results=export_results,
        respect_robots=respect_robots,
        use_history=use_history,
        history_file=history_file
    )


def run_crawl(config: CrawlerConfig) -> Dict[str, List[Dict[str, str]]]:
    """Run the crawler and return JSON serializable results."""
    crawler = WebCrawler(config)

    searches: List[Tuple[str, str]] = []
    for value in config.search_values:
        searches.extend([
            ("text", value),
            ("id", value),
            ("class", value),
            ("attr", value),
        ])

    raw_results = crawler.crawl_and_search(searches)

    serialized: Dict[str, List[Dict[str, str]]] = {}
    for key, items in raw_results.items():
        serialized[key] = []
        for url, element in items:
            if isinstance(element, NavigableString):
                text = str(element).strip()
            else:
                text = element.get_text(strip=True)
            serialized[key].append({"url": url, "text": text})
    return serialized

def main() -> None:
    config = get_user_input()
    crawler = WebCrawler(config)
    
    searches = []
    for search_value in config.search_values:
        searches.extend([
            ('text', search_value),
            ('id', search_value),
            ('class', search_value),
            ('attr', search_value)
        ])
    
    print("\n=== Crawler Configuration ===")
    print(f"URL: {config.base_url}")
    print(f"Searching for: {', '.join(config.search_values)}")
    print(f"Maximum pages: {config.max_pages}")
    print(f"Concurrent workers: {config.max_workers}")
    print(f"Delay between requests: {config.sleep_time} seconds")
    print(f"Request timeout: {config.timeout} seconds")
    print(f"Maximum crawl depth: {config.max_depth}")
    
    if config.respect_robots:
        print("Respecting robots.txt")
    if config.use_history:
        print("Using history file to avoid duplicates")
    if config.verbose:
        print("Debug mode enabled")
    if config.export_results:
        print("Results will be exported to file")
    
    print("\nPress Ctrl+C to stop at any time")
    
    try:
        results = crawler.crawl_and_search(searches)
        
        print("\n=== Search Results ===")
        for search_value in config.search_values:
            print(f"\nResults for '{search_value}':")
            value_results = []
            
            for search_type in ['text', 'id', 'class', 'attr']:
                key = f"{search_type}:{search_value}"
                if key in results:
                    value_results.extend(results[key])
            
            unique_results = []
            seen = set()
            for url, element in value_results:
                if isinstance(element, NavigableString):
                    content = element.strip()
                else:
                    content = element.get_text().strip()
                result_id = f"{url}|{content}"
                
                if result_id not in seen:
                    seen.add(result_id)
                    unique_results.append((url, element))
            
            if unique_results:
                print(f"Found {len(unique_results)} unique occurrence(s):")
                for url, element in unique_results:
                    print_element_info(element, url)
            else:
                print("No elements found")
                print("Note: The element might be:")
                print("1. Not present on any crawled page")
                print("2. On pages not yet crawled")
                print("3. Dynamically loaded by JavaScript")
                print("4. In a different format or have different attributes")
        
        if config.export_results:
            export_results_to_file(results, config.search_values)
            
    except KeyboardInterrupt:
        print("\n\nCrawl interrupted by user. Stopping...")
        crawler.stop()
        print("Saving progress...")
        crawler.save_history()
        print("Crawl stopped successfully.")
    except Exception as e:
        print(f"\n\nError during crawl: {str(e)}")
        crawler.save_history()

if __name__ == "__main__":
    main()
