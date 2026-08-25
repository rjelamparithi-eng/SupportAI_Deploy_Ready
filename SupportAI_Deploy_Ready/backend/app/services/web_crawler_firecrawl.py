from __future__ import annotations

import asyncio
import logging
import os
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


FIRECRAWL_API_KEY = os.getenv(
    "FIRECRAWL_API_KEY", ""
).strip()

FIRECRAWL_BASE_URL = os.getenv(
    "FIRECRAWL_BASE_URL",
    "https://api.firecrawl.dev"
).rstrip("/")


@dataclass
class CrawledDocument:
    url: str
    title: str
    text: str
    source_type: str = "webpage"
    content_type: str = "text/markdown"
    metadata: dict = field(default_factory=dict)


def normalize_url(
    url: str,
    base_url: str | None = None
) -> str:

    if not url:
        return ""

    candidate = url.strip()

    if base_url and not urlparse(candidate).scheme:
        candidate = urljoin(base_url, candidate)

    parsed = urlparse(candidate)

    if parsed.scheme not in {"http", "https"}:
        return ""

    return urlunparse(
        parsed._replace(fragment="")
    )


# ─────────────────────────────────────────────
# FIRECRAWL - JAVASCRIPT WEBSITE CRAWLER
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# FIRECRAWL URL DISCOVERY
# ─────────────────────────────────────────────

async def firecrawl_map(
    url: str,
    max_pages: int
) -> list[str]:

    print(f"[FIRECRAWL] Mapping website: {url}")

    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }

    # Start with max 30 pages while testing
    limit = min(max_pages, 30)

    payload = {
        "url": url,
        "sitemap": "include",
        "includeSubdomains": True,
        "ignoreQueryParameters": True,
        "ignoreCache": True,
        "limit": limit,
        "timeout": 60000
    }

    async with httpx.AsyncClient(
        timeout=70.0,
        follow_redirects=True
    ) as client:

        response = await client.post(
            f"{FIRECRAWL_BASE_URL}/v2/map",
            headers=headers,
            json=payload
        )

        response.raise_for_status()

        data = response.json()

    urls = []

    for item in data.get("links", []) or []:

        if isinstance(item, str):
            page_url = item

        elif isinstance(item, dict):
            page_url = item.get("url")

        else:
            page_url = None

        if page_url and page_url not in urls:
            urls.append(page_url)

    print(
        f"[FIRECRAWL] Map discovered {len(urls)} URLs"
    )

    return urls[:limit]


# ─────────────────────────────────────────────
# FIRECRAWL BATCH SCRAPER
# ─────────────────────────────────────────────

async def firecrawl_batch_scrape(
    urls: list[str]
) -> list[CrawledDocument]:

    if not urls:
        return []

    print(
        f"[FIRECRAWL] Batch scraping {len(urls)} URLs"
    )

    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "urls": urls,
        "ignoreInvalidURLs": True,
        "formats": [
            "markdown",
            "html"
        ],
        "onlyMainContent": False,
        "waitFor": 5000,
        "timeout": 120000,
        "parsers": ["pdf"]
    }

    async with httpx.AsyncClient(
        timeout=150.0,
        follow_redirects=True
    ) as client:

        start_response = await client.post(
            f"{FIRECRAWL_BASE_URL}/v2/batch/scrape",
            headers=headers,
            json=payload
        )

        start_response.raise_for_status()

        start_data = start_response.json()

        job_id = start_data.get("id")

        if not job_id:
            raise RuntimeError(
                "Firecrawl batch scrape did not return job ID."
            )

        print(
            f"[FIRECRAWL] Batch Job ID: {job_id}"
        )

        status_data = None

        for _ in range(90):

            await asyncio.sleep(2)

            response = await client.get(
                f"{FIRECRAWL_BASE_URL}/v2/batch/scrape/{job_id}",
                headers=headers
            )

            response.raise_for_status()

            status_data = response.json()

            state = status_data.get("status")

            completed = status_data.get(
                "completed",
                0
            )

            total = status_data.get(
                "total",
                0
            )

            print(
                f"[FIRECRAWL] "
                f"Batch Status={state} "
                f"Completed={completed} "
                f"Total={total}"
            )

            if state == "completed":
                break

            if state in {
                "failed",
                "cancelled"
            }:
                raise RuntimeError(
                    f"Firecrawl batch scrape {state}"
                )

        else:
            raise TimeoutError(
                "Firecrawl batch scrape timed out."
            )

        documents = []

        current = status_data or {}

        while True:

            data = current.get(
                "data",
                []
            ) or []

            for item in data:

                markdown = (
                    item.get("markdown")
                    or ""
                ).strip()

                html = (
                    item.get("html")
                    or ""
                ).strip()

                # If markdown is too small,
                # extract text from rendered HTML
                if len(markdown.split()) < 40 and html:

                    soup = BeautifulSoup(
                        html,
                        "html.parser"
                    )

                    for tag in soup([
                        "script",
                        "style",
                        "noscript",
                        "svg",
                        "canvas"
                    ]):
                        tag.decompose()

                    html_text = " ".join(
                        soup.get_text(
                            " ",
                            strip=True
                        ).split()
                    )

                    if len(html_text) > len(markdown):
                        markdown = html_text

                # Ignore useless tiny JS pages
                if len(markdown.split()) < 20:

                    print(
                        "[FIRECRAWL] "
                        "Skipping tiny page | "
                        f"Characters={len(markdown)}"
                    )

                    continue

                metadata = (
                    item.get("metadata")
                    or {}
                )

                page_url = (
                    metadata.get("sourceURL")
                    or metadata.get("url")
                    or ""
                )

                # DEBUG
                print(
                    f"[FIRECRAWL] CONTENT "
                    f"{page_url} | "
                    f"Words={len(markdown.split())} | "
                    f"Characters={len(markdown)}"
                )

                title = (
                    metadata.get("title")
                    or "Untitled"
                )

                documents.append(
                    CrawledDocument(
                        url=page_url,
                        title=title,
                        text=markdown,
                        metadata={
                            **metadata,
                            "source_url": page_url,
                            "title": title,
                            "scrape_mode":
                                "firecrawl-map-batch"
                        }
                    )
                )

            next_url = current.get("next")

            if not next_url:
                break

            response = await client.get(
                next_url,
                headers=headers
            )

            response.raise_for_status()

            current = response.json()

    print(
        f"[FIRECRAWL] Batch scraped "
        f"{len(documents)} pages"
    )

    return documents
    
async def firecrawl_crawl(
    url: str,
    max_pages: int,
    max_depth: int
) -> list[CrawledDocument]:

    print(
        f"[FIRECRAWL] Starting JavaScript crawl: {url}"
    )

    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "url": url,

        "limit": max(
            1,
            min(max_pages, 100)
        ),

        "maxDiscoveryDepth": max_depth,

        "crawlEntireDomain": True,

        "allowSubdomains": False,

        "sitemap": "include",

        "ignoreQueryParameters": True,

        "scrapeOptions": {
            "formats": [
                "markdown",
                "html"
            ],
        
            "onlyMainContent": False,
        
            # Give React/JavaScript more time to load
            "waitFor": 5000,
        
            "parsers": ["pdf"]
        }

    timeout = httpx.Timeout(
        90.0,
        connect=20.0
    )

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True
    ) as client:

        start_response = await client.post(
            f"{FIRECRAWL_BASE_URL}/v2/crawl",
            headers=headers,
            json=payload
        )

        start_response.raise_for_status()

        start_data = start_response.json()

        job_id = start_data.get("id")

        if not job_id:
            raise RuntimeError(
                "Firecrawl did not return crawl ID."
            )

        print(
            f"[FIRECRAWL] Job ID: {job_id}"
        )

        status_data = None

        # Wait maximum ~3 minutes
        for _ in range(90):

            await asyncio.sleep(2)

            response = await client.get(
                f"{FIRECRAWL_BASE_URL}/v2/crawl/{job_id}",
                headers=headers
            )

            response.raise_for_status()

            status_data = response.json()

            state = status_data.get("status")

            completed = status_data.get(
                "completed",
                0
            )

            total = status_data.get(
                "total",
                0
            )

            print(
                f"[FIRECRAWL] "
                f"Status={state} "
                f"Completed={completed} "
                f"Total={total}"
            )

            if state == "completed":
                break

            if state in {
                "failed",
                "cancelled"
            }:
                raise RuntimeError(
                    status_data.get("error")
                    or
                    f"Firecrawl {state}"
                )

        else:
            raise TimeoutError(
                "Firecrawl crawl timed out."
            )

        documents = []

        current = status_data or {}

        while True:

            data = current.get(
                "data",
                []
            ) or []

            for item in data:

                markdown = (
                    item.get("markdown")
                    or ""
                ).strip()

                metadata = (
                    item.get("metadata")
                    or {}
                )

                source_url = (
                    metadata.get("sourceURL")
                    or
                    metadata.get("url")
                    or
                    url
                )

                title = (
                    metadata.get("title")
                    or
                    "Untitled"
                )

                if not markdown:
                    continue

                documents.append(
                    CrawledDocument(
                        url=source_url,
                        title=title,
                        text=markdown,
                        metadata={
                            **metadata,
                            "source_url": source_url,
                            "title": title,
                            "scrape_mode":
                                "firecrawl-js"
                        }
                    )
                )

            next_url = current.get("next")

            if not next_url:
                break

            response = await client.get(
                next_url,
                headers=headers
            )

            response.raise_for_status()

            current = response.json()

        print(
            f"[FIRECRAWL] "
            f"Pages scraped: {len(documents)}"
        )

        return documents


# ─────────────────────────────────────────────
# NORMAL HTML FALLBACK
# ─────────────────────────────────────────────

async def http_fallback(
    url: str,
    max_pages: int,
    max_depth: int
) -> list[CrawledDocument]:

    print(
        "[HTTP] Using normal HTML crawler"
    )

    start_url = normalize_url(url)

    if not start_url:
        return []

    start_host = urlparse(
        start_url
    ).netloc.lower()

    queue = deque([
        (start_url, 0)
    ])

    queued = {start_url}

    visited = set()

    documents = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/126.0.0.0 "
            "Safari/537.36"
        )
    }

    async with httpx.AsyncClient(
        headers=headers,
        follow_redirects=True,
        timeout=30
    ) as client:

        while (
            queue
            and
            len(visited) < max_pages
        ):

            page_url, depth = (
                queue.popleft()
            )

            if page_url in visited:
                continue

            if depth > max_depth:
                continue

            visited.add(page_url)

            try:

                response = await client.get(
                    page_url
                )

                response.raise_for_status()

            except Exception as e:

                print(
                    f"[HTTP] Failed: "
                    f"{page_url} : {e}"
                )

                continue

            content_type = (
                response.headers.get(
                    "content-type",
                    ""
                ).lower()
            )

            if "text/html" not in content_type:
                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            for tag in soup([
                "script",
                "style",
                "noscript",
                "svg",
                "canvas",
                "template"
            ]):
                tag.decompose()

            title = (
                soup.title.get_text(
                    " ",
                    strip=True
                )
                if soup.title
                else "Untitled"
            )

            main = (
                soup.find("main")
                or
                soup.find("article")
                or
                soup.body
                or
                soup
            )

            text = " ".join(
                main.get_text(
                    " ",
                    strip=True
                ).split()
            )

            # Detect JS-only shell
            lower = text.lower()

            javascript_only = (
                len(text.split()) < 40
                and
                (
                    "enable javascript" in lower
                    or
                    "javascript to run this app"
                    in lower
                )
            )

            if text and not javascript_only:

                documents.append(
                    CrawledDocument(
                        url=str(response.url),
                        title=title,
                        text=text,
                        metadata={
                            "source_url":
                                str(response.url),

                            "title":
                                title,

                            "scrape_mode":
                                "http-fallback"
                        }
                    )
                )

            if depth >= max_depth:
                continue

            for anchor in soup.find_all(
                "a",
                href=True
            ):

                link = normalize_url(
                    anchor.get(
                        "href",
                        ""
                    ),
                    str(response.url)
                )

                if not link:
                    continue

                if (
                    urlparse(link)
                    .netloc
                    .lower()
                    != start_host
                ):
                    continue

                if (
                    link in visited
                    or
                    link in queued
                ):
                    continue

                queued.add(link)

                queue.append(
                    (
                        link,
                        depth + 1
                    )
                )

    print(
        f"[HTTP] Pages scraped: "
        f"{len(documents)}"
    )

    return documents


# ─────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────

async def crawl_website(
    url: str,
    max_pages: int = 100,
    max_depth: int = 5
) -> list[CrawledDocument]:

    print(f"[CRAWLER] Starting: {url}")

    if FIRECRAWL_API_KEY:

        # ─── METHOD 1: MAP + BATCH SCRAPE ───
        try:

            urls = await firecrawl_map(
                url,
                max_pages
            )

            print(
                f"[CRAWLER] URLs discovered: "
                f"{len(urls)}"
            )

            if len(urls) > 1:

                documents = await firecrawl_batch_scrape(
                    urls
                )

                if documents:

                    print(
                        "[CRAWLER] Map + Batch "
                        f"success: {len(documents)} pages"
                    )

                    return documents

            print(
                "[CRAWLER] Map found too few URLs."
            )

        except Exception as e:

            logger.exception(
                "Firecrawl map/batch failed: %s",
                e
            )

            print(
                f"[FIRECRAWL] Map/Batch failed: {e}"
            )

        # ─── METHOD 2: NORMAL FIRECRAWL ───
        try:

            print(
                "[CRAWLER] Trying normal "
                "Firecrawl crawl..."
            )

            documents = await firecrawl_crawl(
                url,
                max_pages,
                max_depth
            )

            if documents:

                print(
                    "[CRAWLER] Normal Firecrawl "
                    f"returned {len(documents)} pages"
                )

                return documents

        except Exception as e:

            logger.exception(
                "Normal Firecrawl failed: %s",
                e
            )

            print(
                f"[FIRECRAWL] Crawl failed: {e}"
            )

    else:

        print(
            "[CRAWLER] WARNING: "
            "FIRECRAWL_API_KEY missing"
        )

    # ─── METHOD 3: NORMAL HTML FALLBACK ───

    print(
        "[CRAWLER] Using HTTP fallback"
    )

    documents = await http_fallback(
        url,
        max_pages,
        max_depth
    )

    if not documents:

        raise ValueError(
            "No website content could be scraped."
        )

    return documents
