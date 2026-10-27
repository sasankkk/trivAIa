"""RSS collection layer. Add/remove feeds in FEEDS as needed."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import logging
import re
import time

import feedparser

log = logging.getLogger("trivaia.sources")

# Initial source set: a mix of technology publications and official engineering/research feeds.
# RSS availability can change; failed feeds are logged and skipped rather than crashing the run.
FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "Hacker News": "https://hnrss.org/frontpage",
    "Google AI Blog": "https://blog.research.google/feeds/posts/default",
    "OpenAI": "https://openai.com/news/rss.xml",
    "Microsoft Research": "https://www.microsoft.com/en-us/research/feed/",
    "GitHub Blog": "https://github.blog/feed/",
    "Cloudflare Blog": "https://blog.cloudflare.com/rss/",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
    "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "Google Developers": "https://developers.googleblog.com/feeds/posts/default",
    "Netflix TechBlog": "https://netflixtechblog.com/feed",
}


def _parse_date(entry):
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if not value:
            continue
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            pass
    # feedparser often provides a parsed struct_time even when raw date format varies.
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            try:
                return datetime.fromtimestamp(time.mktime(value), tz=timezone.utc)
            except (TypeError, ValueError, OverflowError):
                pass
    return None


def _clean_html(value):
    value = re.sub(r"<(script|style).*?</\1>", " ", value or "", flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def fetch_articles(cutoff):
    articles = []
    for source, url in FEEDS.items():
        try:
            parsed = feedparser.parse(url)
            if parsed.bozo and not parsed.entries:
                log.warning("Feed unavailable: %s (%s)", source, url)
                continue
            for entry in parsed.entries:
                link = entry.get("link", "").strip()
                title = _clean_html(entry.get("title", ""))
                if not link or not title:
                    continue
                published = _parse_date(entry)
                # If a feed omits dates, retain the item for this run; it will be deduplicated by link.
                if published and published < cutoff:
                    continue
                summary = _clean_html(entry.get("summary", entry.get("description", "")))
                articles.append({
                    "source": source,
                    "title": title[:400],
                    "summary": summary[:2500],
                    "link": link,
                    "published": published.isoformat() if published else None,
                })
        except Exception as exc:
            log.exception("Could not fetch %s: %s", source, exc)
    # Deduplicate within the current collection by canonical link.
    unique = {}
    for article in articles:
        unique.setdefault(article["link"].split("#")[0].rstrip("/"), article)
    return list(unique.values())
