"""trivAIa: scheduled technology news briefing for Telegram."""
import logging
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from news_sources import fetch_articles
from storage import init_db, get_recent_links, save_articles
from briefing import build_briefing

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("trivaia")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TIMEZONE_NAME = os.getenv("TIMEZONE", "Asia/Kolkata")
DELIVERY_HOUR = int(os.getenv("DELIVERY_HOUR", "7"))
DELIVERY_MINUTE = int(os.getenv("DELIVERY_MINUTE", "0"))


def send_telegram_message(text: str) -> None:
    """Send a Telegram message, splitting it to stay under Telegram's message limit."""
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your .env file.")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # Keep comfortably below Telegram's 4096-character message limit.
    chunks, remaining = [], text
    while remaining:
        if len(remaining) <= 3800:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n", 0, 3800)
        if split_at < 1000:
            split_at = 3800
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:].lstrip()

    for chunk in chunks:
        response = requests.post(
            url,
            json={"chat_id": CHAT_ID, "text": chunk, "disable_web_page_preview": True},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram API error: {payload}")


def run_briefing() -> None:
    log.info("Starting trivAIa news collection")
    now_utc = datetime.now(timezone.utc)
    lookback_hours = int(os.getenv("LOOKBACK_HOURS", "30"))
    cutoff = now_utc - timedelta(hours=lookback_hours)

    articles = fetch_articles(cutoff=cutoff)
    known_links = get_recent_links()
    fresh = [a for a in articles if a["link"] not in known_links]

    # Save all collected items so repeated runs don't resend the same stories.
    save_articles(articles)
    log.info("Fetched %s articles; %s are new", len(articles), len(fresh))

    max_stories = int(os.getenv("MAX_STORIES", "25"))
    message = build_briefing(fresh, max_stories=max_stories)
    send_telegram_message(message)
    log.info("Briefing sent to Telegram")


def main() -> None:
    init_db()
    if not BOT_TOKEN or not CHAT_ID:
        raise SystemExit(
            "Missing Telegram configuration. Copy .env.example to .env and set "
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
        )

    # Send a test briefing immediately when run with --now.
    import sys
    if "--now" in sys.argv:
        run_briefing()
        return

    scheduler = BlockingScheduler(timezone=ZoneInfo(TIMEZONE_NAME))
    scheduler.add_job(
        run_briefing,
        "cron",
        hour=DELIVERY_HOUR,
        minute=DELIVERY_MINUTE,
        id="daily_trivaia_briefing",
        misfire_grace_time=3600,
        max_instances=1,
        coalesce=True,
    )
    log.info("trivAIa scheduler active; daily delivery at %02d:%02d (%s)",
             DELIVERY_HOUR, DELIVERY_MINUTE, TIMEZONE_NAME)
    scheduler.start()


if __name__ == "__main__":
    main()
