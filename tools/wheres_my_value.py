#DESCRIPTION: This is a simple webcrawler that find values/strings/etc by searching through a domain and then its pages.
#REASON: This script was originally created to locate a form by its ID on a company website that was getting hit with mass spam. The goal was to find the form by its ID via this script as opposed to looking through many different pages. Once found the form could have reCAPTCHA applied to it.
#DISCLAIMER: This script was created with the help of Cursor (AI)

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from requests.exceptions import RequestException
from typing import List, Optional, Set, Dict, Union, Tuple, Any
from urllib.parse import urljoin, urlparse, urlunparse
import time
import json
import os
import winsound
import sys
from datetime import datetime
from urllib.robotparser import RobotFileParser
import re
import concurrent.futures
from queue import Queue
import threading
import base64
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
    max_workers: int  # Maximum of 5 concurrent workers
    http_method: str
    use_auth: bool
    auth_username: Optional[str]
    auth_password: Optional[str]
    use_proxy: bool
    proxy: Optional[str]
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
        self._last_print_time = 0  # Track last print time
        self._last_pages = 0  # Track last number of pages visited

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
        """Check if progress should be printed based on sleep time"""
        current_time = time.time()
        time_elapsed = current_time - self._last_print_time >= sleep_time
        pages_changed = self.pages_visited > self._last_pages
        
        if time_elapsed and pages_changed:
            self._last_print_time = current_time
            self._last_pages = self.pages_visited
            return True
        return False

def print_progress(stats: CrawlerStats, total: int, sleep_time: float, bar_length: int = 50) -> None:
    """Print a simple progress bar with statistics"""
    if not stats.should_print_progress(total, sleep_time):
        return
        
    percentage = (stats.pages_visited / total) * 100
    filled_length = int(bar_length * stats.pages_visited // total)
    bar = '=' * filled_length + '-' * (bar_length - filled_length)
    
    print(f'\rProgress: [{bar}] {percentage:.1f}% | {stats.pages_visited}/{total} pages | '
          f'{stats.get_pages_per_minute():.1f} pages/min | {stats.get_elapsed_time():.1f}s', 
          end='', flush=True)

class WebCrawler:
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.base_domain = urlparse(config.base_url).netloc
        self.visited_urls: Set[str] = set()
        self.url_queue = Queue()
        self.results_lock = threading.Lock()
        self.visited_lock = threading.Lock()
        self.stats = CrawlerStats()
        self.found_values: Set[str] = set()
        self._last_save_count = 0
        self._consecutive_errors = 0
        self._max_consecutive_errors = 5
        self._stop_requested = False  # Flag to stop crawling
        
        # Initialize headers
        self.headers = DEFAULT_HEADERS.copy()
        
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
        
        # Load history if enabled
        if config.use_history:
            print(f"History file location: {config.history_file}")
            self.load_history()
        else:
            print("History tracking disabled")

    def load_history(self) -> None:
        """Load previously visited URLs from file"""
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
        """Save visited URLs to file"""
        if not self.config.use_history or not self.config.history_file:
            return
            
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
        """Check if URL is valid and belongs to the same domain"""
        try:
            parsed = urlparse(url)
            # Skip non-HTML content
            if any(url.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
                return False
            # Check domain
            if parsed.netloc != self.base_domain:
                return False
            # Check robots.txt if enabled
            if self.robots_parser and not self.robots_parser.can_fetch(self.headers['User-Agent'], url):
                if self.config.verbose:
                    print(f"\nSkipping blocked URL: {url}")
                return False
            return True
        except:
            return False

    def get_links(self, soup: BeautifulSoup, current_url: str, current_depth: int) -> Dict[str, int]:
        """Extract all links from the page"""
        links = {}
        max_links_per_page = 50  # Reduced from 100
        try:
            for a_tag in soup.find_all('a', href=True):
                if len(links) >= max_links_per_page:
                    break
                url = urljoin(current_url, a_tag['href'])
                # Early robots.txt check before adding to links
                if self.is_valid_url(url) and current_depth < self.config.max_depth:
                    links[url] = current_depth + 1
        except Exception as e:
            if self.config.verbose:
                print(f"\nError extracting links from {current_url}: {str(e)}")
        return links

    def make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with configured settings"""
        try:
            response = requests.get(
                url=url,
                headers=self.headers,
                timeout=self.config.timeout,
                verify=True
            )
            response.raise_for_status()
            self._consecutive_errors = 0
            return response
        except RequestException as e:
            self._consecutive_errors += 1
            self.stats.add_error(f"Error fetching {url}: {str(e)}")
            if self.config.verbose:
                print(f"\nError fetching {url}: {str(e)}")
            
            if self._consecutive_errors >= self._max_consecutive_errors:
                print(f"\nStopping due to {self._max_consecutive_errors} consecutive errors")
                return None
            
            return None

    def stop(self) -> None:
        """Request the crawler to stop"""
        self._stop_requested = True
        # Clear the queue to stop workers
        while not self.url_queue.empty():
            try:
                self.url_queue.get_nowait()
            except:
                pass

    def worker(self, searches: List[Tuple[str, str]], results: Dict[str, List[Tuple[str, Any]]]) -> None:
        """Worker function for concurrent crawling"""
        while not self._stop_requested:
            try:
                # Check if we've found all values
                if len(self.found_values) >= len(self.config.search_values):
                    break
                    
                # Check if we've hit max pages
                if self.stats.pages_visited >= self.config.max_pages:
                    break
                    
                try:
                    current_url, current_depth = self.url_queue.get(timeout=1)
                except:
                    # If queue is empty and we're not stopping, wait a bit
                    if not self._stop_requested:
                        time.sleep(0.1)
                        continue
                    break

                if self._stop_requested:
                    self.url_queue.task_done()
                    break

                if current_url in self.visited_urls:
                    self.url_queue.task_done()
                    continue

                # Early robots.txt check before making request
                if self.robots_parser and not self.robots_parser.can_fetch(self.headers['User-Agent'], current_url):
                    if self.config.verbose:
                        print(f"\nSkipping blocked URL: {current_url}")
                    self.url_queue.task_done()
                    with self.visited_lock:
                        self.visited_urls.add(current_url)
                    continue

                try:
                    response = self.make_request(current_url)
                    if not response:
                        self.url_queue.task_done()
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Add page results to overall results
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
                                    print(f"\n🎉 Found value: '{value}'! ({len(self.found_values)}/{len(self.config.search_values)} found)")
                                    try:
                                        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
                                    except:
                                        print("\a")
                                    self.save_history()
                                    if len(self.found_values) == len(self.config.search_values):
                                        print("\n🎉 Found all target values! Stopping crawl...")
                                        self.stop()
                                        break

                    if not self._stop_requested and len(self.found_values) < len(self.config.search_values):
                        new_links = self.get_links(soup, current_url, current_depth)
                        for url, depth in new_links.items():
                            if not self._stop_requested:
                                self.url_queue.put((url, depth))

                    with self.visited_lock:
                        self.visited_urls.add(current_url)
                        self.stats.increment_pages()
                    
                    self.url_queue.task_done()
                    time.sleep(self.config.sleep_time)
                except Exception as e:
                    self.url_queue.task_done()
                    if not self._stop_requested:
                        self.stats.add_error(f"Error processing {current_url}: {str(e)}")
                    continue
            except Exception as e:
                if not self._stop_requested:
                    self.stats.add_error(f"Worker error: {str(e)}")
                continue

    def search_page(self, soup: BeautifulSoup, searches: List[Tuple[str, str]]) -> Dict[str, List[Any]]:
        """Search a single page for all search criteria"""
        results = defaultdict(list)
        for search_type, value in searches:
            key = f"{search_type}:{value}"
            results[key] = search_html(soup, search_type, value)
        return dict(results)

    def crawl_and_search(self, searches: List[Tuple[str, str]]) -> Dict[str, List[Tuple[str, Any]]]:
        """Crawl pages and perform searches"""
        results = defaultdict(list)
        
        print("\nStarting crawl...")
        print("Press Ctrl+C to stop at any time\n")
        
        # Check if base URL is allowed by robots.txt
        if self.robots_parser and not self.robots_parser.can_fetch(self.headers['User-Agent'], self.config.base_url):
            print(f"\n⚠️ Warning: The base URL '{self.config.base_url}' is blocked by robots.txt!")
            print("The crawler may not be able to access any pages on this site.")
            proceed = input("Do you want to continue anyway? (yes/no): ").lower()
            if proceed != 'yes':
                print("Crawl cancelled.")
                return results
        
        # Initialize URL queue with base URL
        self.url_queue.put((self.config.base_url, 0))
        
        try:
            # Create and start worker threads
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []
                for _ in range(self.config.max_workers):
                    futures.append(executor.submit(self.worker, searches, results))
                
                # Monitor progress
                last_progress_time = time.time()
                last_pages_visited = 0
                no_progress_threshold = 30  # seconds
                last_queue_size = 0
                stuck_counter = 0
                completion_check_counter = 0
                
                while not self._stop_requested:
                    try:
                        print_progress(self.stats, self.config.max_pages, self.config.sleep_time)
                        
                        # Save history periodically
                        if self.stats.pages_visited % 10 == 0:
                            self.save_history()
                        
                        # Check for completion conditions
                        if (len(self.found_values) >= len(self.config.search_values) or 
                            self.stats.pages_visited >= self.config.max_pages):
                            print("\nCrawl completed - target reached!")
                            self.stop()
                            break
                        
                        # Check for stuck condition
                        current_time = time.time()
                        current_queue_size = self.url_queue.qsize()
                        active_workers = sum(1 for f in futures if not f.done())
                        
                        # Check if we're stuck (no new pages and queue size hasn't changed)
                        if current_time - last_progress_time > no_progress_threshold:
                            if self.stats.pages_visited == last_pages_visited and current_queue_size == last_queue_size:
                                stuck_counter += 1
                                if stuck_counter >= 2:  # Only warn after being stuck twice
                                    print(f"\n⚠️ Warning: No new pages visited for {no_progress_threshold} seconds")
                                    print("This might indicate that:")
                                    print("1. The crawler has reached the end of accessible pages")
                                    print("2. The site is blocking requests")
                                    print("3. Network issues are preventing access")
                                    print("\nCurrent status:")
                                    print(f"- Pages visited: {self.stats.pages_visited}/{self.config.max_pages}")
                                    print(f"- Values found: {len(self.found_values)}/{len(self.config.search_values)}")
                                    print(f"- Queue size: {current_queue_size}")
                                    print(f"- Active workers: {active_workers}")
                                    
                                    # Check if all workers are done
                                    if active_workers == 0:
                                        print("\nAll workers have completed. No more pages to process.")
                                        self.stop()
                                        break
                                        
                                    proceed = input("\nDo you want to continue waiting? (yes/no): ").lower()
                                    if proceed != 'yes':
                                        print("Stopping crawl...")
                                        self.stop()
                                        break
                                    stuck_counter = 0
                            else:
                                stuck_counter = 0
                                last_queue_size = current_queue_size
                        
                        # Check if all workers are done and queue is empty
                        if active_workers == 0 and self.url_queue.empty():
                            completion_check_counter += 1
                            if completion_check_counter >= 3:  # Wait for 3 consecutive checks
                                print("\nAll workers have completed and queue is empty.")
                                self.stop()
                                break
                        else:
                            completion_check_counter = 0
                        
                        last_pages_visited = self.stats.pages_visited
                        last_progress_time = current_time
                        time.sleep(0.1)
                    except KeyboardInterrupt:
                        print("\n\nCtrl+C detected. Stopping crawl...")
                        self.stop()
                        break
                
                # Wait for all workers to complete
                for future in futures:
                    future.cancel()
                    try:
                        future.result(timeout=1)  # Add timeout to prevent hanging
                    except:
                        pass
                
                # Clear any remaining items in the queue
                while not self.url_queue.empty():
                    try:
                        self.url_queue.get_nowait()
                    except:
                        pass
            
            print("\n\nCrawl completed!")
            if self.stats.error_count > 0:
                print(f"\nEncountered {self.stats.error_count} errors during crawl")
                if self.config.verbose:
                    print("\nError log:")
                    for error in self.stats.error_log:
                        print(f"- {error}")
            
            # Print summary of found values
            print("\n=== Search Summary ===")
            print(f"Found {len(self.found_values)} out of {len(self.config.search_values)} values:")
            for value in self.config.search_values:
                if value in self.found_values:
                    print(f"✓ Found: '{value}'")
                else:
                    print(f"✗ Not found: '{value}'")
            
            self.save_history()
            return dict(results)
            
        except KeyboardInterrupt:
            print("\n\nCtrl+C detected. Stopping crawl...")
            self.stop()
            print("Saving progress...")
            self.save_history()
            print("Crawl stopped successfully.")
            return dict(results)
        except Exception as e:
            print(f"\n\nError during crawl: {str(e)}")
            self.save_history()
            return dict(results)

def search_html(soup: BeautifulSoup, search_type: str, value: str) -> List[Any]:
    """Search HTML content based on different criteria"""
    if search_type == 'text':
        return soup.find_all(string=lambda text: value.lower() in str(text).lower())
    elif search_type == 'id':
        return soup.select(f"#{value}")
    elif search_type == 'class':
        return soup.select(f".{value}")
    elif search_type == 'attr':
        if '=' in value:
            attr_name, attr_value = value.split('=', 1)
            return soup.select(f"[{attr_name}='{attr_value}']")
        return soup.find_all(attrs={value: True})
    return []

def print_element_info(element: Union[Tag, NavigableString], url: Optional[str] = None) -> None:
    """Print detailed information about an HTML element"""
    if element is None:
        return
    
    if url:
        print(f"\nFound on page: {url}")
    
    if isinstance(element, NavigableString):
        print("Text content:")
        print(f"  {element.strip()}")
        return
    
    print("Element details:")
    print(f"Tag: {element.name}")
    
    if element.attrs:
        print("Attributes:")
        for key, value in element.attrs.items():
            print(f"  {key}: {value}")
    
    if element.string:
        print(f"Text content: {element.string.strip()}")
    elif element.text:
        print(f"Text content: {element.text.strip()}")

def export_results_to_file(results: Dict[str, List[Tuple[str, Any]]], search_values: List[str]) -> None:
    """Export search results to a file"""
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
                
                # Collect all results for this search value
                for search_type in ['text', 'id', 'class', 'attr']:
                    key = f"{search_type}:{search_value}"
                    if key in results:
                        value_results.extend(results[key])
                
                # Deduplicate results based on URL and element content
                unique_results = []
                seen = set()
                for url, element in value_results:
                    # Create a unique identifier for this result
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
    """Get user input for crawler configuration"""
    print("\n=== Where's My Value Configuration ===")
    
    def get_valid_input(prompt: str, validator: callable, default: Any = None) -> Any:
        while True:
            value = input(f"\n{prompt}").strip()
            if not value and default is not None:
                return default
            if validator(value):
                return value
            print("Invalid input. Please try again.")
    
    # URL validation
    def validate_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            return (url.startswith(('http://', 'https://')) and 
                   len(url) <= 2048 and  # Standard URL length limit
                   bool(parsed.netloc) and  # Must have a domain
                   not any(c in url for c in ['<', '>', '"', "'"]))  # Basic security check
        except:
            return False
    
    url = get_valid_input(
        "Enter the website URL to crawl (e.g., https://example.com): ",
        validate_url
    )
    
    # Search values validation
    def validate_search_values(values: str) -> bool:
        if not values:
            return False
        # Split and validate each value
        value_list = [v.strip() for v in values.split(',')]
        return all(
            0 < len(v) <= 100 and  # Reasonable length limit
            not any(c in v for c in ['<', '>', '"', "'"])  # Basic security check
            for v in value_list
        )
    
    search_values = get_valid_input(
        "Enter the text or values to search for (comma-separated for multiple): ",
        validate_search_values
    ).split(',')
    
    # Max pages validation
    MAX_PAGES = 1000  # Reasonable maximum limit
    max_pages = int(get_valid_input(
        f"Enter maximum number of pages to search (1-{MAX_PAGES}, default: 100): ",
        lambda x: x.isdigit() and 1 <= int(x) <= MAX_PAGES,
        "100"
    ))
    
    # Advanced settings
    print("\n=== Advanced Settings ===")
    
    # Sleep time validation
    MIN_SLEEP = 0.1
    MAX_SLEEP = 10.0
    sleep_time = float(get_valid_input(
        f"Enter time to wait between page searches (in seconds, {MIN_SLEEP}-{MAX_SLEEP}, default: 2): ",
        lambda x: x.replace('.', '').isdigit() and MIN_SLEEP <= float(x) <= MAX_SLEEP,
        "2"
    ))
    
    # Max workers validation (already good)
    MAX_WORKERS = 5
    max_workers = int(get_valid_input(
        f"Enter number of concurrent workers (1-{MAX_WORKERS}, default: 1): ",
        lambda x: x.isdigit() and 1 <= int(x) <= MAX_WORKERS,
        "1"
    ))
    
    # Yes/No validations
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
    
    # Optional features
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
    
    # Handle history file
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
        http_method='GET',
        use_auth=False,
        auth_username=None,
        auth_password=None,
        use_proxy=False,
        proxy=None,
        verbose=debug_mode,
        export_results=export_results,
        respect_robots=respect_robots,
        use_history=use_history,
        history_file=history_file
    )

def main() -> None:
    # Get user input for configuration
    config = get_user_input()
    
    # Initialize crawler with user settings
    crawler = WebCrawler(config)
    
    # Define searches for each search value (simplified to core search types)
    searches = []
    for search_value in config.search_values:
        searches.extend([
            ('text', search_value),  # Main search for the specific text
            ('id', search_value),    # Check if it's an ID
            ('class', search_value), # Check if it's a class
            ('attr', search_value)   # Check for any attribute with this value
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
        # Perform crawl and search
        results = crawler.crawl_and_search(searches)
        
        # Organize and deduplicate results by search value
        print("\n=== Search Results ===")
        for search_value in config.search_values:
            print(f"\nResults for '{search_value}':")
            value_results = []
            
            # Collect all results for this search value
            for search_type in ['text', 'id', 'class', 'attr']:
                key = f"{search_type}:{search_value}"
                if key in results:
                    value_results.extend(results[key])
            
            # Deduplicate results based on URL and element content
            unique_results = []
            seen = set()
            for url, element in value_results:
                # Create a unique identifier for this result
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
        
        # Export results if requested
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
