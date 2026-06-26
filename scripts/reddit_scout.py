#!/usr/bin/env python3
"""Reddit Scout — fetch top posts from subreddits via RSS. No API key required."""

import argparse
import html as html_lib
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


DEFAULT_SUBREDDITS = {
    "unmet_needs": ["SomebodyMakeThis", "sideproject", "SaaS", "Entrepreneur"],
    "consumer":    ["shutupandtakemymoney", "BuyItForLife", "SomebodyMakeThis", "Frugal"],
    "b2b":         ["SaaS", "Entrepreneur", "smallbusiness", "startups"],
    "dev":         ["sideproject", "programming", "webdev", "MacApps"],
    "ai":          ["SaaS", "artificial", "MachineLearning", "sideproject"],
}

# Fix 4: unescape HTML entities before stripping tags, so "don&#39;t" → "don't" not "don t"
def clean_html(text: str) -> str:
    text = html_lib.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_sub(sub: str, sort: str = "top", t: str = "month", limit: int = 25) -> tuple[list[dict], str | None]:
    """Return (posts, error_message). error_message is None on success."""
    url = f"https://www.reddit.com/r/{sub}/{sort}.rss?t={t}&limit={limit}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; research-bot/1.0)"}
    )
    # Fix 3: surface error details instead of swallowing them
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        return [], f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return [], f"URLError: {e.reason}"
    except Exception as e:
        return [], str(e)

    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        return [], f"XML parse error: {e}"

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = []
    for entry in root.findall("atom:entry", ns):
        title   = entry.findtext("atom:title", default="", namespaces=ns)
        link    = entry.find("atom:link", ns)
        url_val = link.get("href") if link is not None else ""
        content = entry.findtext("atom:content", default="", namespaces=ns)
        snippet = clean_html(content)[:500]
        updated = entry.findtext("atom:updated", default="", namespaces=ns)
        entries.append({
            "sub":     sub,
            "title":   title,
            "url":     url_val,
            "date":    updated[:10] if updated else "",
            "snippet": snippet,
        })
    return entries, None


def main() -> None:
    parser = argparse.ArgumentParser(description="Reddit Scout — RSS fetcher")
    parser.add_argument("subreddits", nargs="*", help="Subreddit names (space-separated)")
    parser.add_argument("--preset",  default=None, choices=list(DEFAULT_SUBREDDITS), help="Use a preset subreddit list")
    parser.add_argument("--sort",    default="top",   choices=["top", "hot", "new"])
    parser.add_argument("--time",    default="month", choices=["day", "week", "month", "year", "all"])
    parser.add_argument("--limit",   type=int, default=25)
    # Fix 2: raise default delay to 8s — real-world testing showed 4s triggers 429s
    parser.add_argument("--delay",   type=float, default=8.0, help="Seconds between requests (default 8; increase if hitting 429s)")
    parser.add_argument("--out",     default=None, help="Write JSON output to this file path")
    args = parser.parse_args()

    subs = args.subreddits
    if not subs and args.preset:
        subs = DEFAULT_SUBREDDITS[args.preset]
    if not subs:
        subs = DEFAULT_SUBREDDITS["unmet_needs"]

    all_posts: list[dict] = []
    errors: list[dict] = []

    for i, sub in enumerate(subs):
        if i > 0:
            time.sleep(args.delay)
        sys.stderr.write(f"[reddit-scout] fetching r/{sub} ({args.sort}/{args.time})...\n")
        posts, err = fetch_sub(sub, sort=args.sort, t=args.time, limit=args.limit)
        if err:
            sys.stderr.write(f"[reddit-scout]   → error: {err}\n")
            errors.append({"sub": sub, "error": err})
        else:
            sys.stderr.write(f"[reddit-scout]   → {len(posts)} posts\n")
            all_posts.extend(posts)

    result = {
        "subreddits":  subs,
        "sort":        args.sort,
        "time_range":  args.time,
        "post_count":  len(all_posts),
        "fetched_at":  datetime.now(timezone.utc).isoformat(),
        "errors":      errors,   # Fix 3: agent can distinguish 0-posts vs failed
        "posts":       all_posts,
    }

    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload)
        sys.stderr.write(f"[reddit-scout] saved to {args.out}\n")
    else:
        print(payload)


if __name__ == "__main__":
    main()
