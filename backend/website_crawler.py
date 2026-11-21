
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import json
import time
import requests

from bs4 import BeautifulSoup


# Project configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent

START_URLS = [
    "https://www.ctuniversity.in/",
    "https://www.ctuniversity.in/quick-link/sitemap-2"
]

BASE_DOMAIN = "ctuniversity.in"

OUTPUT_FILE = PROJECT_ROOT / "data" / "website_pages.json"

MAX_PAGES = 200
REQUEST_DELAY = 1.5
REQUEST_TIMEOUT = 25

USER_AGENT = "CampusGPTAcademicResearchBot/1.0"


# Create HTTP session with retry support
session = requests.Session()

session.headers.update({
    "User-Agent": USER_AGENT
})

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)

session.mount("https://", adapter)
session.mount("http://", adapter)


# Store robots rules separately for each domain
robots_cache = {}


def is_allowed_url(url: str) -> bool:
    """
    Allow only CT University and its official subdomains.
    """

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False

    hostname = (parsed.hostname or "").lower()

    if not (
        hostname == BASE_DOMAIN
        or hostname.endswith("." + BASE_DOMAIN)
    ):
        return False

    # Skip URLs with query parameters
    if parsed.query:
        return False

    blocked_extensions = (
        ".pdf", ".jpg", ".jpeg", ".png", ".gif",
        ".webp", ".svg", ".zip", ".doc", ".docx",
        ".xls", ".xlsx", ".mp4", ".mp3", ".css", ".js"
    )

    if parsed.path.lower().endswith(blocked_extensions):
        return False

    return True


def normalize_url(url: str) -> str:
    """
    Remove fragments and normalize URLs.
    """

    url, _ = urldefrag(url)

    parsed = urlparse(url)

    # Normalize hostname and remove default ports
    hostname = (parsed.hostname or "").lower()

    netloc = hostname

    if parsed.port and parsed.port not in (80, 443):
        netloc = f"{hostname}:{parsed.port}"

    path = parsed.path or "/"

    return parsed._replace(
        netloc=netloc,
        path=path,
        query="",
        fragment=""
    ).geturl()


def can_crawl(url: str) -> bool:
    """
    Check the robots.txt rules for the URL's domain.
    """

    parsed = urlparse(url)

    origin = f"{parsed.scheme}://{parsed.netloc}"

    if origin not in robots_cache:

        robots_url = urljoin(origin, "/robots.txt")

        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            response = session.get(
                robots_url,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            parser.parse(response.text.splitlines())

        except requests.RequestException:
            print("Could not read robots.txt:", robots_url)
            return False

        robots_cache[origin] = parser

    return robots_cache[origin].can_fetch(
        USER_AGENT,
        url
    )


def extract_page_content(html: str) -> tuple[str, str]:
    """
    Extract page title and readable text.
    """

    soup = BeautifulSoup(html, "html.parser")

    title = ""

    if soup.title:
        title = soup.title.get_text(" ", strip=True)

    for element in soup.select(
        "script, style, noscript, nav, footer, "
        "header, aside, iframe, form, svg"
    ):
        element.decompose()

    main_content = soup.select_one(
        "main, article, [role='main']"
    )

    if main_content:
        content = main_content.get_text(
            separator=" ",
            strip=True
        )
    else:
        content = soup.body.get_text(
            separator=" ",
            strip=True
        ) if soup.body else ""

    return title, content


def get_page_links(html: str, current_url: str) -> list[str]:
    """
    Discover internal links from a page.
    """

    soup = BeautifulSoup(html, "html.parser")

    links = []

    for anchor in soup.find_all("a", href=True):

        absolute_url = urljoin(
            current_url,
            anchor["href"]
        )

        absolute_url = normalize_url(absolute_url)

        if is_allowed_url(absolute_url):
            links.append(absolute_url)

    return links


def crawl_website():
    """
    Crawl CT University pages and save extracted content.
    """

    print("Starting CT University website crawler...")

    queue = deque(
        normalize_url(url) for url in START_URLS
    )

    queued = set(queue)
    visited = set()
    collected_pages = []

    while queue and len(visited) < MAX_PAGES:

        current_url = queue.popleft()

        if current_url in visited:
            continue

        visited.add(current_url)

        if not can_crawl(current_url):
            print("Not allowed or robots.txt unavailable:", current_url)
            continue

        try:
            print("\nCrawling:", current_url)

            response = session.get(
                current_url,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            final_url = normalize_url(response.url)

            # Do not follow redirects outside official domains
            if not is_allowed_url(final_url):
                print("Skipped external redirect:", final_url)
                continue

            content_type = response.headers.get(
                "Content-Type", ""
            ).lower()

            if "text/html" not in content_type:
                print("Skipped non-HTML resource")
                continue

            title, text = extract_page_content(
                response.text
            )

            if len(text) >= 200:

                collected_pages.append({
                    "title": title,
                    "url": final_url,
                    "text": text,
                    "crawled_at": datetime.now(
                        timezone.utc
                    ).isoformat()
                })

                print("Saved:", title)

            else:
                print("Skipped: insufficient text")

            links = get_page_links(
                response.text,
                final_url
            )

            for link in links:

                if (
                    link not in visited
                    and link not in queued
                ):
                    queue.append(link)
                    queued.add(link)

            time.sleep(REQUEST_DELAY)

        except requests.RequestException as error:
            print("Request failed:", current_url)
            print("Reason:", error)

    # Save collected website pages
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            collected_pages,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nCrawling completed!")
    print("URLs visited:", len(visited))
    print("Pages collected:", len(collected_pages))
    print("URLs remaining in queue:", len(queue))
    print("Saved file:", OUTPUT_FILE)


if __name__ == "__main__":
    crawl_website()
