"""
scraper.py — Async Playwright scraper for e-commerce product pages.

Extracts: name, price, availability, new_arrival flag, discount info.
Uses multiple fallback CSS selectors to be resilient across different storefronts.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PWTimeout

logger = logging.getLogger(__name__)

TIMEOUT_MS = 30_000

# Ordered fallback selectors — tried in sequence, first match wins
_NAME_SELECTORS = [
    "h1[itemprop='name']",
    "h1.product-title",
    "h1.product-name",
    ".product__title h1",
    ".product-single__title",
    "h1",
]

_PRICE_SELECTORS = [
    "[itemprop='price']",
    ".price__current",
    ".product__price",
    ".woocommerce-Price-amount",
    ".price-box .price",
    ".product-price",
    "span.price",
    ".current-price",
]

_AVAILABILITY_SELECTORS = [
    "[itemprop='availability']",
    ".product-availability",
    ".stock-status",
    ".availability",
    "button[data-add-to-cart]",
    ".add-to-cart",
    ".btn-cart",
]

_DISCOUNT_SELECTORS = [
    ".badge-sale",
    ".discount-badge",
    ".product-label--sale",
    ".sale-badge",
    "[data-badge='sale']",
    ".price__badge--sale",
    ".onsale",
]

_NEW_ARRIVAL_SELECTORS = [
    ".badge-new",
    ".new-badge",
    ".product-label--new",
    "[data-badge='new']",
    ".badge--new",
    ".new-arrival-badge",
]


@dataclass
class ProductSnapshot:
    url: str
    name: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    available: Optional[bool]
    new_arrival: bool
    discount: Optional[str]
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "name": self.name,
            "price": self.price,
            "currency": self.currency,
            "available": self.available,
            "new_arrival": self.new_arrival,
            "discount": self.discount,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProductSnapshot":
        return cls(
            url=data.get("url", ""),
            name=data.get("name"),
            price=data.get("price"),
            currency=data.get("currency"),
            available=data.get("available"),
            new_arrival=data.get("new_arrival", False),
            discount=data.get("discount"),
            error=data.get("error"),
        )


def _parse_price(raw: str) -> tuple[Optional[float], Optional[str]]:
    """Extract a float price and currency symbol from a raw price string."""
    if not raw:
        return None, None
    raw = raw.strip()
    # Find currency symbol
    currency_match = re.search(r"[€$£¥₹]", raw)
    currency = currency_match.group(0) if currency_match else None
    # Extract numeric value (supports European comma-decimal format)
    num_match = re.search(r"[\d.,]+", raw.replace("\xa0", ""))
    if not num_match:
        return None, currency
    num_str = num_match.group(0)
    # Handle European format: 1.234,56 → 1234.56
    if re.search(r"\d{1,3}(\.\d{3})+(,\d+)?$", num_str):
        num_str = num_str.replace(".", "").replace(",", ".")
    elif "," in num_str and "." not in num_str:
        num_str = num_str.replace(",", ".")
    try:
        return float(num_str), currency
    except ValueError:
        return None, currency


async def _try_selectors(page: Page, selectors: list[str]) -> Optional[str]:
    """Return the text of the first matching selector, or None."""
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                text = await el.inner_text()
                if text and text.strip():
                    return text.strip()
        except Exception:
            continue
    return None


async def _scrape_page(page: Page, url: str) -> ProductSnapshot:
    """Navigate to url and extract product data."""
    try:
        await page.goto(url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
        # Allow dynamic content a moment to render
        await asyncio.sleep(1.5)
    except PWTimeout:
        return ProductSnapshot(
            url=url,
            name=None, price=None, currency=None,
            available=None, new_arrival=False, discount=None,
            error="Timeout loading page",
        )
    except Exception as exc:
        return ProductSnapshot(
            url=url,
            name=None, price=None, currency=None,
            available=None, new_arrival=False, discount=None,
            error=str(exc),
        )

    name = await _try_selectors(page, _NAME_SELECTORS)

    raw_price = await _try_selectors(page, _PRICE_SELECTORS)
    price, currency = _parse_price(raw_price or "")

    raw_avail = await _try_selectors(page, _AVAILABILITY_SELECTORS)
    available: Optional[bool] = None
    if raw_avail is not None:
        lower = raw_avail.lower()
        if any(w in lower for w in ["disponibile", "in stock", "available", "aggiungi", "add to cart"]):
            available = True
        elif any(w in lower for w in ["esaurito", "out of stock", "non disponibile", "unavailable"]):
            available = False

    discount_text = await _try_selectors(page, _DISCOUNT_SELECTORS)
    new_arrival_text = await _try_selectors(page, _NEW_ARRIVAL_SELECTORS)

    return ProductSnapshot(
        url=url,
        name=name,
        price=price,
        currency=currency,
        available=available,
        new_arrival=new_arrival_text is not None,
        discount=discount_text,
        error=None,
    )


async def scrape_all(urls: list[str]) -> list[ProductSnapshot]:
    """Scrape all URLs concurrently under a single Playwright instance."""
    results: list[ProductSnapshot] = []

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(headless=True)
        try:
            tasks = []
            for url in urls:
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                )
                page = await context.new_page()
                tasks.append(_scrape_page(page, url))

            snapshots = await asyncio.gather(*tasks, return_exceptions=True)

            for i, snap in enumerate(snapshots):
                if isinstance(snap, Exception):
                    logger.error("Unhandled error scraping %s: %s", urls[i], snap)
                    results.append(
                        ProductSnapshot(
                            url=urls[i],
                            name=None, price=None, currency=None,
                            available=None, new_arrival=False, discount=None,
                            error=str(snap),
                        )
                    )
                else:
                    logger.info("Scraped %s → name=%s price=%s", urls[i], snap.name, snap.price)
                    results.append(snap)
        finally:
            await browser.close()

    return results
