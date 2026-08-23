#!/usr/bin/env python3
"""VIA Unified Web Scraping Engine — Playwright-first, local, governed.

合法用途專用：遵守 robots.txt、網站條款、同網域邊界、限速與存取控制。
不破解 CAPTCHA、不繞過登入／付費牆／封鎖；遇到驗證頁即 fail-closed。
所有第三方套件皆為選配能力，標準函式庫仍可完成 HTML 離線解析與自測。
"""

from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# =============================================================================
# def 00 SSOT PARAMETERS
# =============================================================================

import argparse
import asyncio
import csv
import hashlib
import html
import importlib.util
import json
import logging
import random
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Optional, Protocol, Sequence

from VIA_Investment_Report_Classifier import (
    def_classify_investment_report,
    def_split_morning_brief,
)
from VIA_WebScraping_Compliance import (
    def_compliance_payload,
    def_load_compliance_ssot,
    def_scan_terms_text,
    def_validate_consent,
)

ENGINE_NAME = "VIA Unified WebScraping Playwright Engine"
ENGINE_VERSION = "1.0.0"
DEFAULT_USER_AGENT = "VIA-ResearchBot/1.0 (+local governed research crawler)"
DEFAULT_TIMEOUT_MS = 30_000
DEFAULT_WAIT_UNTIL = "domcontentloaded"
DEFAULT_MAX_PAGES = 100
DEFAULT_MAX_DEPTH = 2
DEFAULT_CONCURRENCY = 2
DEFAULT_DELAY_SECONDS = 1.5
DEFAULT_JITTER_SECONDS = 0.5
DEFAULT_RETRIES = 2
DEFAULT_MAX_RESPONSE_BYTES = 20 * 1024 * 1024
DEFAULT_SCROLL_ROUNDS = 4
DEFAULT_SCROLL_DELAY_MS = 700
DEFAULT_CHECKPOINT_EVERY = 5
DEFAULT_OUTPUT_DIR = Path("via_webscraping_output")
DEFAULT_ENCODING = "utf-8-sig"
ALLOWED_SCHEMES = {"http", "https"}
BLOCKED_RESOURCE_TYPES = {"font", "media"}
BLOCK_PAGE_RE = re.compile(r"captcha|verify you are human|access denied|unusual traffic|cloudflare.*challenge", re.I)
ARTICLE_TAGS = {"article", "main"}
NOISE_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "form", "aside"}


# =============================================================================
# def 01 DATA CONTRACTS
# =============================================================================

@dataclass
class CrawlConfig:
    start_urls: list[str]
    output_dir: Path = DEFAULT_OUTPUT_DIR
    backend: str = "auto"
    browser: str = "chromium"
    headless: bool = True
    max_pages: int = DEFAULT_MAX_PAGES
    max_depth: int = DEFAULT_MAX_DEPTH
    concurrency: int = DEFAULT_CONCURRENCY
    delay_seconds: float = DEFAULT_DELAY_SECONDS
    jitter_seconds: float = DEFAULT_JITTER_SECONDS
    retries: int = DEFAULT_RETRIES
    timeout_ms: int = DEFAULT_TIMEOUT_MS
    wait_until: str = DEFAULT_WAIT_UNTIL
    user_agent: str = DEFAULT_USER_AGENT
    obey_robots: bool = True
    same_domain: bool = True
    allow_subdomains: bool = True
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    content_selector: str = ""
    link_selector: str = "a[href]"
    wait_selector: str = ""
    click_selectors: list[str] = field(default_factory=list)
    scroll_rounds: int = DEFAULT_SCROLL_ROUNDS
    screenshot: bool = False
    save_html: bool = True
    capture_json: bool = True
    resume: bool = True
    checkpoint_every: int = DEFAULT_CHECKPOINT_EVERY
    consent_token: str = ""
    purpose: str = ""
    authorization_basis: str = ""
    pii_mode: str = "partial"


@dataclass
class FetchResponse:
    requested_url: str
    final_url: str
    status_code: int
    content_type: str
    html: str
    headers: dict[str, str]
    elapsed_ms: int
    backend: str
    network_json: list[dict[str, Any]] = field(default_factory=list)
    screenshot_path: str = ""
    error: str = ""


@dataclass
class ExtractedPage:
    url: str
    canonical_url: str
    status_code: int
    fetched_at_utc: str
    backend: str
    title: str
    author: str
    published_at: str
    modified_at: str
    publisher: str
    description: str
    language: str
    text: str
    markdown: str
    headings: list[dict[str, str]]
    tables: list[list[list[str]]]
    links: list[str]
    images: list[dict[str, str]]
    json_ld: list[Any]
    network_json: list[dict[str, Any]]
    content_sha256: str
    word_count: int
    quality_gate: str
    findings: list[str]
    report_classification: dict[str, Any]
    report_sections: list[dict[str, Any]]
    compliance: dict[str, Any]
    raw_html_path: str = ""
    screenshot_path: str = ""


@dataclass
class CrawlState:
    pending: list[tuple[str, int]] = field(default_factory=list)
    visited: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    content_hashes: list[str] = field(default_factory=list)
    saved_pages: int = 0


class FetchBackend(Protocol):
    name: str
    async def start(self) -> None: ...
    async def close(self) -> None: ...
    async def fetch(self, url: str, config: CrawlConfig, page_index: int) -> FetchResponse: ...


# =============================================================================
# def 02 CAPABILITY REGISTRY — ALL LIBS
# =============================================================================

def def_has_module(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def def_capability_registry() -> dict[str, Any]:
    groups = {
        "dynamic_browser": {
            "Playwright": "playwright", "Selenium": "selenium", "SeleniumBase": "seleniumbase",
            "Crawlee": "crawlee", "Scrapy-Playwright": "scrapy_playwright", "DrissionPage": "DrissionPage",
            "Camoufox": "camoufox", "Crawl4AI": "crawl4ai", "ScrapeGraphAI": "scrapegraphai",
        },
        "http_clients": {
            "urllib": "__stdlib__", "Requests": "requests", "HTTPX": "httpx", "AIOHTTP": "aiohttp",
            "curl_cffi": "curl_cffi", "Scrapy": "scrapy",
        },
        "html_dom": {
            "BeautifulSoup4": "bs4", "lxml": "lxml", "Selectolax": "selectolax", "Parsel": "parsel",
            "PyQuery": "pyquery", "html5lib": "html5lib", "Scrapling": "scrapling",
        },
        "article_extraction": {
            "Trafilatura": "trafilatura", "Newspaper4k": "newspaper", "Readability-lxml": "readability",
            "Extruct": "extruct", "Goose3": "goose3", "Boilerpy3": "boilerpy3", "jusText": "justext",
            "Inscripta": "inscriptis", "html2text": "html2text", "Unstructured": "unstructured",
        },
        "structured_data": {
            "JSON": "__stdlib__", "XML": "__stdlib__", "JMESPath": "jmespath", "JSONPath-NG": "jsonpath_ng",
            "Pydantic": "pydantic", "dateparser": "dateparser",
        },
        "storage": {
            "JSONL": "__stdlib__", "CSV": "__stdlib__", "SQLite": "__stdlib__", "Pandas": "pandas",
            "PyArrow/Parquet": "pyarrow", "DuckDB": "duckdb", "Polars": "polars",
        },
        "quality_and_ops": {
            "Tenacity": "tenacity", "Backoff": "backoff", "DiskCache": "diskcache", "CacheControl": "cachecontrol",
            "tqdm": "tqdm", "Rich": "rich", "Prometheus": "prometheus_client",
        },
        "compliance_privacy": {
            "urllib.robotparser": "__stdlib__", "Protego": "protego", "Presidio": "presidio_analyzer",
            "Scrubadub": "scrubadub", "phonenumbers": "phonenumbers", "validators": "validators",
            "Pydantic": "pydantic", "jsonschema": "jsonschema",
        },
    }
    return {group: {name: {"module": module, "available": module == "__stdlib__" or def_has_module(module)}
                    for name, module in tools.items()} for group, tools in groups.items()}


# =============================================================================
# def 03 URL GOVERNANCE / ROBOTS / RATE LIMIT
# =============================================================================

def def_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def def_normalize_url(url: str, base_url: str = "") -> str:
    absolute = urllib.parse.urljoin(base_url, html.unescape(url.strip()))
    parts = urllib.parse.urlsplit(absolute)
    if parts.scheme.lower() not in ALLOWED_SCHEMES or not parts.netloc:
        return ""
    host = parts.hostname.lower() if parts.hostname else ""
    port = f":{parts.port}" if parts.port and parts.port not in {80, 443} else ""
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    query_pairs = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    query_pairs = [(k, v) for k, v in query_pairs if not re.match(r"^(utm_|fbclid|gclid|ref$)", k, re.I)]
    query = urllib.parse.urlencode(sorted(query_pairs))
    return urllib.parse.urlunsplit((parts.scheme.lower(), host + port, path, query, ""))


def def_registered_domain(host: str) -> str:
    labels = host.lower().split(".")
    return ".".join(labels[-2:]) if len(labels) >= 2 else host.lower()


def def_same_scope(candidate: str, seeds: Sequence[str], allow_subdomains: bool) -> bool:
    host = urllib.parse.urlsplit(candidate).hostname or ""
    seed_hosts = [urllib.parse.urlsplit(seed).hostname or "" for seed in seeds]
    return any(host == x or (allow_subdomains and def_registered_domain(host) == def_registered_domain(x)) for x in seed_hosts)


def def_url_allowed(url: str, config: CrawlConfig) -> bool:
    if not url: return False
    if config.same_domain and not def_same_scope(url, config.start_urls, config.allow_subdomains): return False
    if config.include_patterns and not any(re.search(p, url) for p in config.include_patterns): return False
    if any(re.search(p, url) for p in config.exclude_patterns): return False
    return True


class RobotsGuard:
    def __init__(self, user_agent: str, enabled: bool):
        self.user_agent, self.enabled = user_agent, enabled
        self.cache: dict[str, urllib.robotparser.RobotFileParser] = {}

    async def allowed(self, url: str) -> bool:
        if not self.enabled: return True
        parts = urllib.parse.urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self.cache:
            parser = urllib.robotparser.RobotFileParser(origin + "/robots.txt")
            try: await asyncio.to_thread(parser.read)
            except Exception:
                # Fail closed when robots cannot be established.
                return False
            self.cache[origin] = parser
        return self.cache[origin].can_fetch(self.user_agent, url)


class PoliteRateLimiter:
    def __init__(self, delay: float, jitter: float):
        self.delay, self.jitter = max(0, delay), max(0, jitter)
        self.last_request: dict[str, float] = {}
        self.lock = asyncio.Lock()

    async def wait(self, url: str) -> None:
        host = urllib.parse.urlsplit(url).netloc
        async with self.lock:
            now = time.monotonic(); target = self.last_request.get(host, 0) + self.delay + random.uniform(0, self.jitter)
            if target > now: await asyncio.sleep(target - now)
            self.last_request[host] = time.monotonic()


# =============================================================================
# def 04 FETCH BACKENDS
# =============================================================================

class UrllibBackend:
    name = "urllib"
    async def start(self) -> None: return None
    async def close(self) -> None: return None

    async def fetch(self, url: str, config: CrawlConfig, page_index: int) -> FetchResponse:
        def blocking() -> FetchResponse:
            started = time.monotonic()
            request = urllib.request.Request(url, headers={"User-Agent": config.user_agent, "Accept": "text/html,application/xhtml+xml,application/json"})
            try:
                with urllib.request.urlopen(request, timeout=config.timeout_ms / 1000) as response:
                    data = response.read(DEFAULT_MAX_RESPONSE_BYTES + 1)
                    if len(data) > DEFAULT_MAX_RESPONSE_BYTES: raise ValueError("response exceeds maximum bytes")
                    content_type = response.headers.get_content_type()
                    charset = response.headers.get_content_charset() or "utf-8"
                    body = data.decode(charset, errors="replace")
                    return FetchResponse(url, response.geturl(), response.status, content_type, body,
                                         dict(response.headers.items()), int((time.monotonic() - started) * 1000), self.name)
            except Exception as exc:
                return FetchResponse(url, url, 0, "", "", {}, int((time.monotonic() - started) * 1000), self.name, error=str(exc))
        return await asyncio.to_thread(blocking)


class HttpxBackend:
    name = "httpx"
    def __init__(self): self.client: Any = None
    async def start(self) -> None:
        import httpx
        self.client = httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": DEFAULT_USER_AGENT})
    async def close(self) -> None:
        if self.client: await self.client.aclose()
    async def fetch(self, url: str, config: CrawlConfig, page_index: int) -> FetchResponse:
        started = time.monotonic()
        try:
            response = await self.client.get(url, timeout=config.timeout_ms / 1000, headers={"User-Agent": config.user_agent})
            body = response.content[:DEFAULT_MAX_RESPONSE_BYTES].decode(response.encoding or "utf-8", errors="replace")
            return FetchResponse(url, str(response.url), response.status_code, response.headers.get("content-type", ""), body,
                                 dict(response.headers), int((time.monotonic() - started) * 1000), self.name)
        except Exception as exc:
            return FetchResponse(url, url, 0, "", "", {}, int((time.monotonic() - started) * 1000), self.name, error=str(exc))


class PlaywrightBackend:
    name = "playwright"
    def __init__(self): self.manager: Any = None; self.browser: Any = None
    async def start(self) -> None:
        from playwright.async_api import async_playwright
        self.manager = await async_playwright().start()

    async def close(self) -> None:
        if self.browser: await self.browser.close()
        if self.manager: await self.manager.stop()

    async def _ensure_browser(self, config: CrawlConfig) -> None:
        if not self.browser:
            engine = getattr(self.manager, config.browser)
            self.browser = await engine.launch(headless=config.headless)

    async def fetch(self, url: str, config: CrawlConfig, page_index: int) -> FetchResponse:
        await self._ensure_browser(config)
        context = await self.browser.new_context(user_agent=config.user_agent, java_script_enabled=True)
        page = await context.new_page(); network_json: list[dict[str, Any]] = []

        async def route_handler(route: Any) -> None:
            if route.request.resource_type in BLOCKED_RESOURCE_TYPES: await route.abort()
            else: await route.continue_()

        async def response_handler(response: Any) -> None:
            if not config.capture_json: return
            content_type = response.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                try:
                    payload = await response.json()
                    network_json.append({"url": response.url, "status": response.status, "data": payload})
                except Exception: pass

        await page.route("**/*", route_handler); page.on("response", response_handler)
        started = time.monotonic(); screenshot_path = ""
        try:
            response = await page.goto(url, wait_until=config.wait_until, timeout=config.timeout_ms)
            if config.wait_selector: await page.locator(config.wait_selector).first.wait_for(timeout=config.timeout_ms)
            for selector in config.click_selectors:
                locator = page.locator(selector).first
                if await locator.count(): await locator.click(timeout=config.timeout_ms)
            for _ in range(max(0, config.scroll_rounds)):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(DEFAULT_SCROLL_DELAY_MS)
            content = await page.content(); title = await page.title()
            if BLOCK_PAGE_RE.search(title + " " + content[:5000]):
                raise PermissionError("BLOCKED_REVIEW_REQUIRED: verification or access-control page detected")
            if config.screenshot:
                shot_dir = config.output_dir / "screenshots"; shot_dir.mkdir(parents=True, exist_ok=True)
                shot = shot_dir / f"page_{page_index:06d}.png"; await page.screenshot(path=str(shot), full_page=True); screenshot_path = str(shot)
            headers = await response.all_headers() if response else {}
            result = FetchResponse(url, page.url, response.status if response else 0, headers.get("content-type", "text/html"),
                                   content, headers, int((time.monotonic() - started) * 1000), self.name,
                                   network_json=network_json, screenshot_path=screenshot_path)
        except Exception as exc:
            result = FetchResponse(url, page.url, 0, "", "", {}, int((time.monotonic() - started) * 1000), self.name, error=str(exc))
        await context.close(); return result


def def_choose_backend(name: str) -> FetchBackend:
    if name in {"playwright", "auto"} and def_has_module("playwright"): return PlaywrightBackend()
    if name == "playwright": raise RuntimeError("Playwright 未安裝。請執行 pip install playwright && playwright install chromium")
    if name in {"httpx", "auto"} and def_has_module("httpx"): return HttpxBackend()
    if name == "httpx": raise RuntimeError("HTTPX 未安裝")
    return UrllibBackend()


# =============================================================================
# def 05 HTML EXTRACTION / LAYOUT / STRUCTURED DATA
# =============================================================================

class StandardHTMLExtractor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True); self.base_url = base_url
        self.skip = 0; self.stack: list[str] = []; self.text_parts: list[str] = []; self.title_parts: list[str] = []
        self.links: list[str] = []; self.images: list[dict[str, str]] = []; self.headings: list[dict[str, str]] = []
        self.tables: list[list[list[str]]] = []; self.current_table: list[list[str]] = []; self.current_row: list[str] = []
        self.current_cell: list[str] = []; self.current_heading: list[str] = []; self.json_ld_parts: list[str] = []
        self.in_title = False; self.in_json_ld = False; self.meta: dict[str, str] = {}; self.lang = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        data = {k.lower(): (v or "") for k, v in attrs}; tag = tag.lower(); self.stack.append(tag)
        if tag == "html": self.lang = data.get("lang", "")
        if tag in NOISE_TAGS: self.skip += 1
        if tag == "title": self.in_title = True
        if tag == "script" and "ld+json" in data.get("type", "").lower(): self.in_json_ld = True; self.skip = max(0, self.skip - 1)
        if tag == "a" and data.get("href"):
            normalized = def_normalize_url(data["href"], self.base_url)
            if normalized: self.links.append(normalized)
        if tag == "img" and data.get("src"):
            self.images.append({"src": def_normalize_url(data["src"], self.base_url), "alt": data.get("alt", "")})
        if tag == "meta":
            key = (data.get("property") or data.get("name") or "").lower(); value = data.get("content", "")
            if key and value: self.meta[key] = value
        if tag == "table": self.current_table = []
        if tag == "tr": self.current_row = []
        if tag in {"td", "th"}: self.current_cell = []
        if re.fullmatch(r"h[1-6]", tag): self.current_heading = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "script" and self.in_json_ld: self.in_json_ld = False
        elif tag in NOISE_TAGS and self.skip: self.skip -= 1
        if tag == "title": self.in_title = False
        if tag in {"td", "th"}: self.current_row.append(" ".join(self.current_cell).strip())
        if tag == "tr" and self.current_row: self.current_table.append(self.current_row)
        if tag == "table" and self.current_table: self.tables.append(self.current_table)
        if re.fullmatch(r"h[1-6]", tag) and self.current_heading:
            self.headings.append({"level": tag, "text": " ".join(self.current_heading).strip()})
        if self.stack:
            try:
                reverse_index = self.stack[::-1].index(tag); del self.stack[len(self.stack) - 1 - reverse_index]
            except ValueError: pass

    def handle_data(self, data: str) -> None:
        value = re.sub(r"\s+", " ", data).strip()
        if not value: return
        if self.in_json_ld: self.json_ld_parts.append(value); return
        if self.in_title: self.title_parts.append(value)
        if self.skip: return
        self.text_parts.append(value)
        if self.stack and self.stack[-1] in {"td", "th"}: self.current_cell.append(value)
        if self.stack and re.fullmatch(r"h[1-6]", self.stack[-1]): self.current_heading.append(value)


def def_parse_json_ld(parts: Sequence[str]) -> list[Any]:
    results = []
    for raw in parts:
        try:
            value = json.loads(raw); results.extend(value if isinstance(value, list) else [value])
        except json.JSONDecodeError: continue
    return results


def def_find_jsonld_value(items: Sequence[Any], keys: Sequence[str]) -> str:
    queue: deque[Any] = deque(items)
    while queue:
        item = queue.popleft()
        if isinstance(item, dict):
            for key in keys:
                value = item.get(key)
                if isinstance(value, str) and value.strip(): return value.strip()
                if isinstance(value, dict) and isinstance(value.get("name"), str): return value["name"].strip()
            queue.extend(item.values())
        elif isinstance(item, list): queue.extend(item)
    return ""


def def_extract_with_optional_libs(raw_html: str, url: str, fallback_text: str) -> tuple[str, str]:
    text, markdown = fallback_text, fallback_text
    if def_has_module("trafilatura"):
        import trafilatura
        extracted = trafilatura.extract(raw_html, url=url, include_links=True, include_tables=True, favor_precision=True)
        if extracted: text = extracted
        md = trafilatura.extract(raw_html, url=url, output_format="markdown", include_links=True, include_tables=True)
        if md: markdown = md
    elif def_has_module("readability") and def_has_module("lxml"):
        from readability import Document
        from lxml import html as lxml_html
        summary = Document(raw_html).summary(); text = lxml_html.fromstring(summary).text_content()
    if def_has_module("html2text"):
        import html2text
        markdown = html2text.html2text(raw_html)
    return re.sub(r"\n{3,}", "\n\n", text).strip(), markdown.strip()


def def_extract_page(response: FetchResponse, pii_mode: str = "partial") -> ExtractedPage:
    parser = StandardHTMLExtractor(response.final_url or response.requested_url); parser.feed(response.html)
    json_ld = def_parse_json_ld(parser.json_ld_parts)
    fallback_text = "\n".join(parser.text_parts)
    text, markdown = def_extract_with_optional_libs(response.html, response.final_url, fallback_text)
    title = (parser.meta.get("og:title") or def_find_jsonld_value(json_ld, ["headline", "name"]) or " ".join(parser.title_parts)).strip()
    canonical = parser.meta.get("og:url") or response.final_url
    description = parser.meta.get("description") or parser.meta.get("og:description") or def_find_jsonld_value(json_ld, ["description"])
    author = parser.meta.get("author") or def_find_jsonld_value(json_ld, ["author", "creator"])
    published = parser.meta.get("article:published_time") or def_find_jsonld_value(json_ld, ["datePublished", "dateCreated"])
    modified = parser.meta.get("article:modified_time") or def_find_jsonld_value(json_ld, ["dateModified"])
    publisher = def_find_jsonld_value(json_ld, ["publisher"])
    findings = []
    if response.status_code >= 400 or response.status_code == 0: findings.append(f"HTTP_STATUS={response.status_code}")
    if not title: findings.append("TITLE_MISSING")
    if len(text) < 80: findings.append("CONTENT_TOO_SHORT")
    if BLOCK_PAGE_RE.search(title + " " + text[:3000]): findings.append("BLOCKED_REVIEW_REQUIRED")
    redacted_text, compliance = def_compliance_payload(text, pii_mode)
    is_terms_page = bool(re.search(r"(?:terms|conditions|legal|服務條款|使用條款)", response.final_url, re.I))
    if not is_terms_page:
        compliance["terms_scan"] = {"risk": "NOT_SCANNED_NON_TERMS_PAGE", "score": 0, "evidence": [],
                                    "legal_review_required": False, "disclaimer": "Automated ToS screening is not a legal opinion."}
        compliance["gate"] = "PASS"
    elif compliance["terms_scan"]["legal_review_required"]:
        findings.append("TOS_PROHIBITION_REVIEW_REQUIRED")
    text = redacted_text
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    report_classification = asdict(def_classify_investment_report(title, text))
    report_sections = def_split_morning_brief(title, text, response.final_url)
    return ExtractedPage(response.final_url, def_normalize_url(canonical, response.final_url), response.status_code, def_now_iso(), response.backend,
                         title, author, published, modified, publisher, description, parser.lang, text, markdown,
                         parser.headings, parser.tables, list(dict.fromkeys(parser.links)), parser.images, json_ld,
                         response.network_json, content_hash, len(re.findall(r"\w+", text)),
                         "PASS" if not findings else "REVIEW_REQUIRED", findings,
                         report_classification, report_sections, compliance, screenshot_path=response.screenshot_path)


# =============================================================================
# def 06 STORAGE / CHECKPOINT / EXPORT
# =============================================================================

class OutputStore:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir; output_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = output_dir / "pages.jsonl"; self.csv_path = output_dir / "pages.csv"
        self.db_path = output_dir / "crawl.sqlite"; self.html_dir = output_dir / "html"; self.html_dir.mkdir(exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute("""CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY, canonical_url TEXT, status_code INTEGER, fetched_at_utc TEXT, backend TEXT,
            title TEXT, author TEXT, published_at TEXT, publisher TEXT, text TEXT, markdown TEXT,
            content_sha256 TEXT, quality_gate TEXT, raw_json TEXT)""")
        self.connection.commit()

    def save(self, page: ExtractedPage, raw_html: str, save_html: bool) -> ExtractedPage:
        if save_html:
            name = hashlib.sha256(page.url.encode()).hexdigest()[:20] + ".html"
            path = self.html_dir / name; path.write_text(raw_html, encoding="utf-8"); page.raw_html_path = str(path)
        payload = asdict(page)
        with self.jsonl_path.open("a", encoding="utf-8") as handle: handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.connection.execute("INSERT OR REPLACE INTO pages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                (page.url, page.canonical_url, page.status_code, page.fetched_at_utc, page.backend, page.title,
                                 page.author, page.published_at, page.publisher, page.text, page.markdown,
                                 page.content_sha256, page.quality_gate, json.dumps(payload, ensure_ascii=False)))
        self.connection.commit(); return page

    def export(self) -> dict[str, str]:
        rows = self.connection.execute("SELECT url,canonical_url,status_code,fetched_at_utc,backend,title,author,published_at,publisher,content_sha256,quality_gate FROM pages").fetchall()
        columns = [x[0] for x in self.connection.execute("SELECT url,canonical_url,status_code,fetched_at_utc,backend,title,author,published_at,publisher,content_sha256,quality_gate FROM pages").description]
        with self.csv_path.open("w", encoding=DEFAULT_ENCODING, newline="") as handle:
            writer = csv.writer(handle); writer.writerow(columns); writer.writerows(rows)
        outputs = {"jsonl": str(self.jsonl_path), "csv": str(self.csv_path), "sqlite": str(self.db_path)}
        if def_has_module("pyarrow"):
            import pyarrow as pa; import pyarrow.parquet as pq
            records = [dict(zip(columns, row)) for row in rows]; path = self.output_dir / "pages.parquet"
            pq.write_table(pa.Table.from_pylist(records), path); outputs["parquet"] = str(path)
        return outputs

    def close(self) -> None: self.connection.close()


def def_state_path(output_dir: Path) -> Path: return output_dir / "checkpoint.json"


def def_save_state(state: CrawlState, output_dir: Path) -> None:
    path = def_state_path(output_dir); temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8"); temp.replace(path)


def def_load_state(config: CrawlConfig) -> CrawlState:
    path = def_state_path(config.output_dir)
    if config.resume and path.exists():
        data = json.loads(path.read_text(encoding="utf-8")); data["pending"] = [tuple(x) for x in data.get("pending", [])]
        return CrawlState(**data)
    return CrawlState(pending=[(def_normalize_url(url), 0) for url in config.start_urls])


# =============================================================================
# def 07 ORCHESTRATOR
# =============================================================================

async def def_fetch_with_retry(backend: FetchBackend, url: str, config: CrawlConfig, index: int) -> FetchResponse:
    response = FetchResponse(url, url, 0, "", "", {}, 0, backend.name, error="not attempted")
    for attempt in range(config.retries + 1):
        response = await backend.fetch(url, config, index)
        if not response.error and response.status_code < 500: return response
        if attempt < config.retries: await asyncio.sleep(min(2 ** attempt, 10))
    return response


async def def_run_crawl(config: CrawlConfig) -> dict[str, Any]:
    consent_findings = def_validate_consent(config.consent_token, config.purpose, config.authorization_basis)
    if consent_findings:
        raise PermissionError("COMPLIANCE_CONSENT_FAIL_CLOSED:" + json.dumps([asdict(x) for x in consent_findings], ensure_ascii=False))
    config.start_urls = [def_normalize_url(x) for x in config.start_urls if def_normalize_url(x)]
    if not config.start_urls: raise ValueError("沒有合法的 http/https URL")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    state = def_load_state(config); store = OutputStore(config.output_dir); backend = def_choose_backend(config.backend)
    robots = RobotsGuard(config.user_agent, config.obey_robots); limiter = PoliteRateLimiter(config.delay_seconds, config.jitter_seconds)
    queue = deque(state.pending); visited = set(state.visited); hashes = set(state.content_hashes)
    await backend.start()
    try:
        while queue and state.saved_pages < config.max_pages:
            url, depth = queue.popleft(); state.pending = list(queue)
            if url in visited or depth > config.max_depth or not def_url_allowed(url, config): continue
            if not await robots.allowed(url): state.failed[url] = "ROBOTS_DISALLOWED_OR_UNAVAILABLE"; visited.add(url); continue
            await limiter.wait(url); response = await def_fetch_with_retry(backend, url, config, state.saved_pages + 1); visited.add(url)
            if response.error:
                state.failed[url] = response.error; state.visited = sorted(visited); def_save_state(state, config.output_dir); continue
            page = def_extract_page(response, config.pii_mode)
            if page.content_sha256 not in hashes:
                store.save(page, response.html, config.save_html); hashes.add(page.content_sha256); state.saved_pages += 1
            terms_links, normal_links = [], []
            for link in page.links:
                if link not in visited and def_url_allowed(link, config):
                    (terms_links if re.search(r"(?:terms|conditions|legal|服務條款|使用條款)", link, re.I) else normal_links).append(link)
            for link in reversed(terms_links): queue.appendleft((link, depth + 1))
            for link in normal_links: queue.append((link, depth + 1))
            if "TOS_PROHIBITION_REVIEW_REQUIRED" in page.findings:
                state.failed[url] = "TOS_PROHIBITION_REVIEW_REQUIRED"; state.pending = list(queue); break
            state.pending = list(queue); state.visited = sorted(visited); state.content_hashes = sorted(hashes)
            if state.saved_pages % config.checkpoint_every == 0: def_save_state(state, config.output_dir)
    finally:
        await backend.close(); def_save_state(state, config.output_dir); outputs = store.export(); store.close()
    return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, "backend": backend.name, "saved_pages": state.saved_pages,
            "visited": len(visited), "failed": state.failed, "pending": len(queue), "outputs": outputs,
            "capabilities": def_capability_registry(), "gate": "PASS" if not state.failed else "COMPLETED_WITH_FINDINGS"}


# =============================================================================
# def 08 OFFLINE SELF-TEST
# =============================================================================

def def_self_test() -> None:
    sample = """<!doctype html><html lang='zh-Hant'><head><title>台積電研究更新</title>
    <meta name='author' content='VIA Research'><meta property='article:published_time' content='2026-08-19'>
    <script type='application/ld+json'>{"@type":"NewsArticle","headline":"台積電研究更新","publisher":{"name":"VIA"}}</script></head>
    <body><nav>選單</nav><main><h1>先進製程需求強勁</h1><p>營收與毛利率展望改善，本文內容足以通過長度檢查並驗證抽取結果。</p>
    <table><tr><th>年度</th><th>EPS</th></tr><tr><td>2027</td><td>50</td></tr></table>
    <a href='/next?utm_source=test'>下一頁</a></main><footer>版權</footer></body></html>"""
    response = FetchResponse("https://example.com/report", "https://example.com/report", 200, "text/html", sample, {}, 10, "offline")
    page = def_extract_page(response)
    assert page.title == "台積電研究更新"
    assert page.author == "VIA Research" and page.publisher == "VIA"
    assert page.links == ["https://example.com/next"]
    assert page.tables[0][1] == ["2027", "50"]
    assert "選單" not in page.text and "版權" not in page.text
    assert def_normalize_url("javascript:alert(1)") == ""
    assert def_same_scope("https://sub.example.com/a", ["https://example.com"], True)
    registry = def_capability_registry(); assert "Playwright" in registry["dynamic_browser"]
    assert page.report_classification["report_type_code"] == "UNCLASSIFIED_RESEARCH"
    assert page.compliance["gate"] == "PASS"


# =============================================================================
# def 09 CLI
# =============================================================================

def def_load_config(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict): raise ValueError("Config 必須是 JSON object")
    return data


def def_parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=ENGINE_NAME)
    parser.add_argument("urls", nargs="*", help="起始 URL")
    parser.add_argument("--config", type=Path, help="JSON 設定檔；CLI URL 優先")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--backend", choices=["auto", "playwright", "httpx", "urllib"], default="auto")
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"], default="chromium")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--ignore-robots", action="store_true", help="僅限已獲站方書面授權的內部網站")
    parser.add_argument("--allow-external", action="store_true")
    parser.add_argument("--selector", default="")
    parser.add_argument("--wait-selector", default="")
    parser.add_argument("--click", action="append", default=[])
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--screenshot", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--list-capabilities", action="store_true")
    parser.add_argument("--consent-token", default="")
    parser.add_argument("--purpose", default="")
    parser.add_argument("--authorization-basis", default="")
    parser.add_argument("--pii-mode", choices=["partial", "full", "off"], default="partial")
    return parser.parse_args(argv)


def def_config_from_args(args: argparse.Namespace) -> CrawlConfig:
    base = def_load_config(args.config) if args.config else {}
    if "output_dir" in base: base["output_dir"] = Path(base["output_dir"])
    config = CrawlConfig(**base) if base else CrawlConfig(start_urls=[])
    if args.urls: config.start_urls = args.urls
    config.output_dir = args.output_dir; config.backend = args.backend; config.browser = args.browser; config.headless = not args.headed
    config.max_pages = max(1, args.max_pages); config.max_depth = max(0, args.max_depth); config.delay_seconds = max(0, args.delay)
    config.obey_robots = not args.ignore_robots; config.same_domain = not args.allow_external
    config.content_selector = args.selector; config.wait_selector = args.wait_selector; config.click_selectors = args.click
    config.include_patterns = args.include; config.exclude_patterns = args.exclude; config.screenshot = args.screenshot
    config.consent_token = args.consent_token; config.purpose = args.purpose
    config.authorization_basis = args.authorization_basis; config.pii_mode = args.pii_mode
    return config


def def_main(argv: Optional[Sequence[str]] = None) -> int:
    args = def_parse_args(argv); logging.basicConfig(level=logging.INFO, format="def [%(levelname)s] %(message)s")
    if args.list_capabilities: print(json.dumps(def_capability_registry(), ensure_ascii=False, indent=2)); return 0
    if args.self_test:
        def_self_test(); print("def SELF_TEST: PASS")
        if not args.urls and not args.config: return 0
    config = def_config_from_args(args)
    if not config.start_urls: print("def ERROR: 請提供 URL 或 --config", file=sys.stderr); return 2
    try:
        result = asyncio.run(def_run_crawl(config)); print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result["gate"] == "PASS" else 3
    except Exception as exc:
        logging.exception("Engine failed: %s", exc); return 1


if __name__ == "__main__":
    raise SystemExit(def_main())
