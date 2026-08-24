from __future__ import annotations

import logging
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
except Exception:
    async_playwright = None


@dataclass
class CrawledDocument:
    url: str
    title: str
    text: str
    source_type: str = "webpage"
    content_type: str = "text/html"
    metadata: dict = field(default_factory=dict)


class WebsiteCrawler:
    def __init__(
        self,
        url: str,
        max_pages: int = 100,
        max_depth: int = 10,
    ) -> None:
        self.start_url = self.normalize_url(url)
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited: set[str] = set()
        self.discovered: set[str] = set()
        self.documents: list[CrawledDocument] = []
        self.js_urls: set[str] = set()
        self.api_responses: list[dict] = []

        if self.start_url:
            self.discovered.add(self.start_url)

    @staticmethod
    def normalize_url(url: str, base_url: str | None = None) -> str:
        if not url:
            return ""

        candidate = url.strip()
        if base_url and not urlparse(candidate).scheme:
            candidate = urljoin(base_url, candidate)

        parsed = urlparse(candidate)
        if parsed.scheme not in {"http", "https"}:
            return ""

        return urlunparse(parsed._replace(fragment=""))

    def is_internal_link(self, link: str, base_url: str) -> bool:
        normalized = self.normalize_url(link, base_url)
        if not normalized:
            return False

        parsed = urlparse(normalized)
        base_netloc = urlparse(base_url).netloc
        return not parsed.netloc or parsed.netloc == base_netloc

    def _reset_for_fallback(self) -> None:
        self.visited.clear()
        self.discovered = {self.start_url} if self.start_url else set()
        self.documents.clear()
        self.js_urls.clear()
        self.api_responses.clear()

    async def _crawl_http(self) -> list[CrawledDocument]:
        """Render-friendly fallback that does not require Chromium."""
        if not self.start_url:
            return []

        queue: list[tuple[str, int]] = [(self.start_url, 0)]
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(30.0),
            headers=headers,
        ) as client:
            while queue and len(self.visited) < self.max_pages:
                url, depth = queue.pop(0)
                if url in self.visited or depth > self.max_depth:
                    continue

                self.visited.add(url)
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                except Exception as exc:
                    logger.warning("HTTP fallback failed for %s: %s", url, exc)
                    continue

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type.lower():
                    continue

                soup = BeautifulSoup(response.text, "html.parser")

                for tag in soup(["script", "style", "noscript", "svg", "canvas"]):
                    tag.decompose()

                title = "Untitled"
                if soup.title and soup.title.string:
                    title = soup.title.string.strip() or "Untitled"

                text = " ".join(soup.get_text(" ", strip=True).split())
                if text:
                    self.documents.append(
                        CrawledDocument(
                            url=str(response.url),
                            title=title,
                            text=text,
                            metadata={
                                "source_url": str(response.url),
                                "title": title,
                                "scrape_mode": "http-fallback",
                            },
                        )
                    )

                for anchor in soup.find_all("a", href=True):
                    normalized = self.normalize_url(anchor.get("href", ""), str(response.url))
                    if not normalized or not self.is_internal_link(normalized, self.start_url):
                        continue
                    if normalized in self.visited or normalized in self.discovered:
                        continue
                    if len(self.visited) + len(queue) >= self.max_pages:
                        break
                    self.discovered.add(normalized)
                    queue.append((normalized, depth + 1))

        logger.info(
            "HTTP fallback crawl complete: pages=%d documents=%d",
            len(self.visited),
            len(self.documents),
        )
        return self.documents

    async def handle_response(self, response) -> None:
        try:
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type.lower():
                return

            payload = await response.json()
            self.api_responses.append(
                {
                    "url": response.url,
                    "status": response.status,
                    "content_type": content_type,
                    "body": payload,
                }
            )
        except Exception:
            pass

    async def extract_page(self, page, url: str) -> list[str]:
        try:
            title = await page.title()
        except Exception:
            title = ""

        try:
            text = await page.locator("body").inner_text()
        except Exception:
            text = ""

        cleaned_text = " ".join(text.split()) if text else ""
        if cleaned_text:
            clean_title = (title or "Untitled").strip() or "Untitled"
            self.documents.append(
                CrawledDocument(
                    url=url,
                    title=clean_title,
                    text=cleaned_text,
                    metadata={
                        "source_url": url,
                        "title": clean_title,
                        "scrape_mode": "playwright",
                    },
                )
            )

        links: list[str] = []
        try:
            hrefs = await page.locator("a[href]").evaluate_all(
                "elements => elements.map(e => e.href).filter(Boolean)"
            )
        except Exception:
            hrefs = []

        for href in hrefs:
            normalized = self.normalize_url(href, url)
            if not normalized or not self.is_internal_link(normalized, self.start_url):
                continue
            links.append(normalized)

        return links

    async def _crawl_playwright(self) -> list[CrawledDocument]:
        if async_playwright is None:
            raise RuntimeError("Playwright package is unavailable")

        queue: list[tuple[str, int]] = [(self.start_url, 0)]

        async with async_playwright() as playwright:
            # This may fail on hosts where the Chromium binary is not bundled.
            # crawl() catches that and automatically uses the HTTP fallback.
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1440, "height": 1200},
            )

            try:
                while queue and len(self.visited) < self.max_pages:
                    url, depth = queue.pop(0)
                    if url in self.visited or depth > self.max_depth:
                        continue

                    self.visited.add(url)
                    page = None
                    try:
                        page = await context.new_page()
                        page.on("response", self.handle_response)
                        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                        await page.wait_for_timeout(1500)

                        links = await self.extract_page(page, url)
                        for link in links:
                            if link in self.visited or link in self.discovered:
                                continue
                            if len(self.visited) + len(queue) >= self.max_pages:
                                break
                            self.discovered.add(link)
                            queue.append((link, depth + 1))
                    except Exception as exc:
                        logger.warning("Failed to crawl %s with Playwright: %s", url, exc)
                    finally:
                        if page is not None:
                            try:
                                if not page.is_closed():
                                    await page.close()
                            except Exception:
                                pass
            finally:
                try:
                    await context.close()
                except Exception:
                    pass
                try:
                    await browser.close()
                except Exception:
                    pass

        return self.documents

    async def crawl(self) -> list[CrawledDocument]:
        if not self.start_url:
            return []

        # Try Playwright first. On Render/free hosting, Chromium may not be
        # available in the runtime image, so automatically fall back to HTTP.
        try:
            documents = await self._crawl_playwright()
            if documents:
                return documents
        except Exception as exc:
            logger.warning("Playwright unavailable; using HTTP fallback: %s", exc)

        self._reset_for_fallback()
        return await self._crawl_http()


async def crawl_website(
    url: str,
    max_pages: int = 100,
    max_depth: int = 10,
) -> list[CrawledDocument]:
    return await WebsiteCrawler(
        url,
        max_pages=max_pages,
        max_depth=max_depth,
    ).crawl()
