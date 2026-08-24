from __future__ import annotations

import logging
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


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
        if parsed.scheme in {"mailto", "tel"}:
            return False

        base_netloc = urlparse(base_url).netloc
        if parsed.netloc and parsed.netloc != base_netloc:
            return False

        return True

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
        title = ""
        try:
            title = await page.title()
        except Exception:
            title = ""

        text = ""
        try:
            text = await page.locator("body").inner_text()
        except Exception:
            text = ""

        if not text.strip():
            try:
                text = await page.evaluate(
                    """
                    () => {
                        const selectors = ['main', 'article', 'section', 'div', 'p', 'li', 'h1', 'h2', 'h3'];
                        const parts = [];
                        for (const selector of selectors) {
                            const nodes = document.querySelectorAll(selector);
                            for (const node of nodes) {
                                const value = (node?.innerText || node?.textContent || '').trim();
                                if (value) parts.push(value);
                            }
                        }
                        return parts.join(' ');
                    }
                    """
                )
            except Exception:
                text = ""

        cleaned_text = " ".join(text.split()) if text else ""
        if cleaned_text:
            self.documents.append(
                CrawledDocument(
                    url=url,
                    title=(title or "Untitled").strip() or "Untitled",
                    text=cleaned_text,
                    source_type="webpage",
                    content_type="text/html",
                    metadata={
                        "source_url": url,
                        "title": (title or "Untitled").strip() or "Untitled",
                    },
                )
            )

        try:
            scripts = await page.locator("script[src]").evaluate_all(
                """
                elements => elements
                    .map(element => element.src)
                    .filter(Boolean)
                """
            )
        except Exception:
            scripts = []

        for script_url in scripts:
            normalized = self.normalize_url(script_url, url)
            if normalized:
                self.js_urls.add(normalized)

        links: list[str] = []
        try:
            hrefs = await page.locator("a[href]").evaluate_all(
                """
                elements => elements
                    .map(element => element.href)
                    .filter(Boolean)
                """
            )
        except Exception:
            hrefs = []

        for href in hrefs:
            normalized = self.normalize_url(href, url)
            if not normalized:
                continue
            if not self.is_internal_link(normalized, url):
                continue
            if normalized not in self.discovered and normalized not in self.visited:
                self.discovered.add(normalized)
            links.append(normalized)

        return links

    async def crawl(self) -> list[CrawledDocument]:
        queue: list[tuple[str, int]] = [(self.start_url, 0)]

        async with async_playwright() as playwright:
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
                    if url in self.visited:
                        continue
                    if depth > self.max_depth:
                        continue

                    self.visited.add(url)
                    logger.info(
                        "Crawling [%d/%d] depth=%d: %s",
                        len(self.visited),
                        self.max_pages,
                        depth,
                        url,
                    )

                    page = None
                    try:
                        page = await context.new_page()
                        page.on("response", self.handle_response)
                        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                        await page.wait_for_timeout(3000)

                        try:
                            max_height = await page.evaluate(
                                """
                                () => {
                                    const body = document.body;
                                    return body ? body.scrollHeight : 0;
                                }
                                """
                            )
                            if max_height:
                                step = max(200, min(1200, int(max_height / 8)))
                                for position in range(step, int(max_height) + step, step):
                                    await page.evaluate(
                                        "(position) => { window.scrollTo(0, position); }",
                                        position,
                                    )
                                    await page.wait_for_timeout(200)
                                await page.evaluate("""() => { window.scrollTo(0, 0); }""")
                        except Exception as exc:
                            logger.warning("Scroll/evaluate failed for %s: %s", url, exc)

                        links = await self.extract_page(page, url)
                        for link in links:
                            if link in self.visited:
                                continue
                            if link in self.discovered:
                                continue
                            if len(self.visited) + len(queue) >= self.max_pages:
                                break
                            self.discovered.add(link)
                            queue.append((link, depth + 1))
                        logger.info("Successfully scraped: %s", url)
                    except Exception as exc:
                        logger.warning("Failed to crawl %s: %s", url, exc)
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

        logger.info(
            "Crawl complete: pages=%d documents=%d",
            len(self.visited),
            len(self.documents),
        )
        return self.documents


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
