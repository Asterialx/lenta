"""Fetch RSS feeds and write data/items.json. Standard library only."""
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# (source name, topic, feed url)
FEEDS = [
    ("Хабр", "Технологии", "https://habr.com/ru/rss/news/?fl=ru"),
    ("3DNews", "Технологии", "https://3dnews.ru/news/rss/"),
    ("Lenta.ru", "Общество", "https://lenta.ru/rss/news"),
    ("РБК", "Экономика", "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"),
    ("Спорт-Экспресс", "Спорт", "https://www.sport-express.ru/services/materials/news/se/"),
]
MAX_PER_FEED = 25
OUT = Path(__file__).parent / "data" / "items.json"
TAG_RE = re.compile(r"<[^>]+>")


def clean(text: str) -> str:
    text = html.unescape(TAG_RE.sub("", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def parse_date(value: str) -> str:
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def fetch(name: str, topic: str, url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "auto-feed-demo/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        root = ET.fromstring(resp.read())
    items = []
    for node in root.iter("item"):
        title = clean(node.findtext("title"))
        link = (node.findtext("link") or "").strip()
        if not title or not link:
            continue
        summary = clean(node.findtext("description"))[:240]
        image = ""
        enclosure = node.find("enclosure")
        if enclosure is not None and "image" in (enclosure.get("type") or "image"):
            image = enclosure.get("url") or ""
        items.append({
            "title": title,
            "url": link,
            "summary": summary,
            "image": image,
            "source": name,
            "topic": topic,
            "date": parse_date(node.findtext("pubDate") or ""),
        })
        if len(items) >= MAX_PER_FEED:
            break
    return items


def main() -> int:
    all_items, ok = [], 0
    for name, topic, url in FEEDS:
        try:
            got = fetch(name, topic, url)
            all_items.extend(got)
            ok += 1
            print(f"ok   {name}: {len(got)}")
        except Exception as exc:  # one broken feed must not stop the rest
            print(f"FAIL {name}: {exc}", file=sys.stderr)
    if not ok:
        return 1
    seen, unique = set(), []
    for item in sorted(all_items, key=lambda i: i["date"], reverse=True):
        if item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)
    payload = {"updated": datetime.now(timezone.utc).isoformat(), "items": unique}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(unique)} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
