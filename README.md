# Auto-updating news feed

Static site that refreshes itself on a schedule.

- `fetch_feeds.py` pulls RSS feeds (standard library only) into `data/items.json`.
- `.github/workflows/update.yml` runs it every hour and commits the result.
- `index.html` renders cards with topic/source/date filters, search and sorting.

Run locally: `python fetch_feeds.py && python -m http.server 8000`, then open http://localhost:8000.
Add a source: append a `(name, topic, url)` tuple to `FEEDS` in `fetch_feeds.py`.
