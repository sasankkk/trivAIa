# trivAIa — AI-powered technology intelligence briefing

A Python starter project that collects articles from RSS feeds, de-duplicates them using SQLite, optionally uses an LLM to select and summarize stories, and sends a daily briefing to Telegram at 7:00 AM IST.

## What this first version does
- Collects from a configurable set of technology, developer, AI, and security RSS feeds.
- Filters articles by a lookback window.
- Avoids sending the same article link again after it has been stored.
- Categorizes and ranks stories using a simple fallback when no AI API key is configured.
- Optionally generates a more readable briefing using an OpenAI-compatible API.
- Sends long briefings as multiple Telegram messages.
- Schedules delivery using `Asia/Kolkata` by default.

## Important limitation
This is a functional starter, not a guarantee of complete global coverage. RSS feeds can be delayed, unavailable, or incomplete. The current ranking is a baseline and should be improved with more sources, source health checks, better deduplication, and evaluation of missed/irrelevant stories.

## 1. Requirements
- Python 3.10+
- A Telegram account
- A Telegram bot token from Telegram's official `@BotFather`
- Your Telegram chat ID
- Optional: an API key for AI summaries

## 2. Setup

### Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and fill in:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_numeric_chat_id
OPENAI_API_KEY=your_api_key_if_using_ai
```

Never share your bot token or commit `.env` to Git.

### Create your Telegram bot
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow the prompts.
3. Copy the token into `.env`.
4. Open your new bot and press **Start**.

### Find your chat ID
1. Send a message to your bot.
2. In a browser, open this API endpoint, replacing `YOUR_TOKEN` with your bot token:
   `https://api.telegram.org/botYOUR_TOKEN/getUpdates`
3. Find `message.chat.id` in the JSON response and put that numeric value in `.env`.
4. Treat the token as a password. Do not paste it into public chats or screenshots.

## 3. Test a briefing immediately
```powershell
python main.py --now
```
The first run may take some time depending on feed response times. Check the terminal logs if no message arrives.

## 4. Run daily at 7:00 AM IST
```powershell
python main.py
```
Keep the process and computer running. If the computer sleeps or shuts down, delivery will not happen. For reliable daily delivery, deploy to an always-on server or scheduled cloud runner.

## 5. Configuration
- `TIMEZONE=Asia/Kolkata`
- `DELIVERY_HOUR=7`
- `DELIVERY_MINUTE=0`
- `MAX_STORIES=25`
- `LOOKBACK_HOURS=30`
- `OPENAI_MODEL=gpt-4o-mini`

If `OPENAI_API_KEY` is empty, the program uses a simple keyword-based fallback. AI API use may incur charges depending on the provider/account.

## 6. Next improvements for a more comprehensive system
1. Expand and health-check source coverage, including official release notes, security advisories, research feeds, and India-specific technology sources.
2. Add story clustering so reports of the same announcement are merged across publishers.
3. Use recency-aware importance ranking and preserve ongoing stories across days.
4. Add source provenance and explicit confidence notes.
5. Track source failures and category coverage in a daily status report.
6. Add Telegram commands such as `/briefing`, `/topics`, `/sources`, and `/help`.
7. Add tests and deploy with monitoring/retries.

## Project structure
```text
trivaia/
├── main.py
├── news_sources.py
├── briefing.py
├── storage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```
