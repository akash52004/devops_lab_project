import os
import feedparser
from typing import List, Tuple, Set

def _get_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)

def get_default_feeds() -> List[str]:
    raw = _get_env("FEEDS", "")
    feeds = [u.strip() for u in raw.split(",") if u.strip()]
    return feeds

def fetch_headlines(feeds: List[str], max_items: int = 5) -> List[Tuple[str, str]]:
    """Return list of (title, link) tuples from the given feeds, de-duplicated by title."""
    items = []
    seen: Set[str] = set()
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries:
                title = (getattr(entry, "title", "") or "").strip()
                link = (getattr(entry, "link", "") or "").strip()
                if title and title not in seen:
                    seen.add(title)
                    items.append((title, link))
                    if len(items) >= max_items:
                        break
        except Exception as e:
            # Skip bad feeds; in 1-day MVP we don't log persistently
            continue
        if len(items) >= max_items:
            break
    return items

def format_sms(headlines: List[Tuple[str, str]], prefix: str = "") -> str:
    bullets = []
    for i, (title, link) in enumerate(headlines, start=1):
        # Keep each line compact; some carriers count segments; avoid long URLs if possible
        bullets.append(f"{i}) {title}")
    body = "\n".join(bullets)
    if prefix:
        return f"{prefix}\n{body}"
    return body
