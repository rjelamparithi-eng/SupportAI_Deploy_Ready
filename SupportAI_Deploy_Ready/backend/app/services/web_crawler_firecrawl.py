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
            "formats": ["markdown"],

            "onlyMainContent": True,

            # Give JavaScript time to render
            "waitFor": 2000,

            # Also support PDF pages when possible
            "parsers": ["pdf"]
        }
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

    # Use Firecrawl first for JavaScript sites
    if FIRECRAWL_API_KEY:

        try:

            documents = await firecrawl_crawl(
                url,
                max_pages,
                max_depth
            )

            if documents:
                return documents

        except Exception as e:

            logger.exception(
                "Firecrawl failed: %s",
                e
            )

            print(
                f"[FIRECRAWL] Failed: {e}"
            )

    # Normal HTML fallback
    documents = await http_fallback(
        url,
        max_pages,
        max_depth
    )

    if not documents:

        if not FIRECRAWL_API_KEY:
            raise ValueError(
                "This website requires "
                "JavaScript. "
                "FIRECRAWL_API_KEY "
                "is not configured."
            )

        raise ValueError(
            "No website content could "
            "be scraped."
        )

    return documents
