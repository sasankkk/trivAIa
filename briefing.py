"""Importance filtering and optional AI summarization."""
import os
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

# Transparent keyword-based fallback; AI mode can improve ranking and summaries.
CATEGORY_KEYWORDS = {
    "AI & Machine Learning": ["ai", "artificial intelligence", "llm", "model", "agent", "machine learning", "openai", "gemini", "claude", "hugging face"],
    "Software & Developer Tools": ["github", "python", "java", "javascript", "react", "developer", "programming", "open source", "framework", "database"],
    "Cybersecurity": ["security", "cyber", "vulnerability", "breach", "malware", "ransomware", "exploit", "cve"],
    "Cloud & Infrastructure": ["cloud", "aws", "azure", "kubernetes", "docker", "infrastructure", "serverless"],
    "Big Tech, Business & Startups": ["google", "microsoft", "apple", "meta", "amazon", "nvidia", "funding", "startup", "acquisition", "layoff"],
    "Hardware & Emerging Tech": ["chip", "semiconductor", "robot", "quantum", "gpu", "processor", "spacex"],
}
HIGH_SIGNAL = [
    "launch", "announces", "released", "release", "breakthrough", "critical",
    "major", "open source", "funding", "acquisition", "vulnerability", "security",
    "new model", "research", "update", "available"
]


def _category(article):
    text = (article["title"] + " " + article.get("summary", "")).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(k in text for k in keywords):
            return category
    return "Technology & Industry"


def _score(article):
    text = (article["title"] + " " + article.get("summary", "")).lower()
    score = 0
    score += sum(2 for word in HIGH_SIGNAL if word in text)
    score += min(len(article.get("summary", "")) // 300, 2)
    if article["source"] in {"OpenAI", "Google AI Blog", "Microsoft Research", "GitHub Blog", "Cloudflare Blog"}:
        score += 1
    return score


def _ai_summaries(articles):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or not articles:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        payload = "\n".join(
            f'{i+1}. SOURCE: {a["source"]}\nTITLE: {a["title"]}\n'
            f'SUMMARY: {a.get("summary","")[:1000]}\nURL: {a["link"]}'
            for i, a in enumerate(articles)
        )
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            messages=[
                {"role": "system", "content": (
                    "You are the editor of trivAIa, a careful technology-news briefing. "
                    "Use only the supplied article metadata/snippets; do not invent facts. "
                    "Select the most consequential distinct stories across categories. "
                    "Return plain text, grouped by category. For each story include a concise "
                    "headline, 1-2 sentence summary, why it matters, source name, and exact URL. "
                    "If evidence is insufficient, say so. Do not claim this is exhaustive."
                )},
                {"role": "user", "content": (
                    f"Create a daily technology briefing from these collected articles. "
                    f"Keep no more than {int(os.getenv('MAX_STORIES','25'))} stories. "
                    f"Prioritize significance, diversity, recency, and trustworthy sources.\n\n{payload}"
                )},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Keep the system usable even if AI service is unavailable.
        return None


def build_briefing(articles, max_stories=25):
    now = datetime.now(ZoneInfo(os.getenv("TIMEZONE", "Asia/Kolkata")))
    heading = (
        "🚀 trivAIa | DAILY TECHNOLOGY BRIEFING\n"
        f"📅 {now.strftime('%A, %d %B %Y')}  •  🕖 {now.strftime('%I:%M %p %Z')}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )
    if not articles:
        return heading + (
            "No new articles were collected in the lookback window.\n"
            "This may mean a quiet news cycle or a feed/source issue. Check the application logs."
        )

    ranked = sorted(articles, key=_score, reverse=True)[:max_stories]
    ai_text = _ai_summaries(ranked)
    if ai_text:
        return heading + ai_text + "\n\nℹ️ Stories are selected from configured sources; coverage is not guaranteed exhaustive."

    groups = defaultdict(list)
    for article in ranked:
        groups[_category(article)].append(article)
    lines = []
    for category in sorted(groups):
        lines.append(f"\n📌 {category.upper()}")
        for article in groups[category]:
            summary = article.get("summary") or "Open the original source for details."
            if len(summary) > 320:
                summary = summary[:317].rsplit(" ", 1)[0] + "..."
            lines.append(f"\n• {article['title']}\n  {summary}\n  Source: {article['source']}\n  {article['link']}")
    lines.append("\n\nℹ️ Rule-based fallback mode. Add OPENAI_API_KEY for AI-assisted selection and summaries.")
    lines.append("Coverage depends on the configured feeds; this digest is not guaranteed exhaustive.")
    return heading + "\n".join(lines)
