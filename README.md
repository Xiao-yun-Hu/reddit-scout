# reddit-scout

A Claude Code skill that crawls Reddit subreddits via public RSS feeds and generates a scored **unmet-needs opportunity report** — no API key, no authentication required.

## What it does

1. **Fetches** top posts from a configurable list of subreddits (RSS, zero credentials)
2. **Clusters** posts by underlying problem / unmet need
3. **Scores** each cluster on three dimensions:
   - **Pain intensity** — emotional language, repeated personal stories
   - **Velocity** — recency concentration (posts in last 2 weeks vs. scattered)
   - **Commercial intent** — "I'd pay", "currently paying $X", explicit willingness to switch
4. **Outputs** a ranked report with direct quotes, gap analysis, and opportunity angles

**Composite score = (Pain × 0.3) + (Velocity × 0.3) + (Commercial intent × 0.4)**

## Install

```bash
# Via OpenClaw (recommended)
npx skills add reddit-scout

# Manual
git clone https://github.com/Xiao-yun-Hu/reddit-scout ~/.agents/skills/reddit-scout
```

Requires Python 3.12+. No external dependencies beyond the standard library.

## Usage

```
/reddit-scout
/reddit-scout B2B sales tools
/reddit-scout AI productivity
/reddit-scout --preset=consumer
/reddit-scout SomebodyMakeThis SaaS WantToLearnTo
```

### Built-in presets

| Preset | Subreddits |
|---|---|
| `unmet_needs` (default) | SomebodyMakeThis, sideproject, SaaS, Entrepreneur |
| `consumer` | shutupandtakemymoney, BuyItForLife, SomebodyMakeThis, Frugal |
| `b2b` | SaaS, Entrepreneur, smallbusiness, startups |
| `dev` | sideproject, programming, webdev, MacApps |
| `ai` | SaaS, artificial, MachineLearning, sideproject |

### Run the fetch script directly

```bash
# Default preset
python3 scripts/reddit_scout.py --preset=unmet_needs --out=results.json

# Custom subreddits
python3 scripts/reddit_scout.py SomebodyMakeThis sideproject SaaS \
  --sort=top --time=month --limit=25 --delay=4 --out=results.json

# Options
#   --sort     top | hot | new          (default: top)
#   --time     day | week | month | year | all  (default: month)
#   --limit    posts per subreddit      (default: 25)
#   --delay    seconds between requests (default: 4.0)
#   --out      save JSON to file instead of stdout
```

## How the RSS approach works

Reddit exposes public RSS/Atom feeds that require no authentication:

```
https://www.reddit.com/r/{subreddit}/top.rss?t=month&limit=25
```

The script parses these feeds, strips HTML from post bodies, and emits clean JSON. A configurable delay between requests (default 4s) keeps it well within Reddit's rate limits.

The JSON output shape:

```json
{
  "subreddits": ["SomebodyMakeThis", "sideproject"],
  "sort": "top",
  "time_range": "month",
  "post_count": 50,
  "fetched_at": "2026-06-26T10:00:00+00:00",
  "posts": [
    {
      "sub": "SomebodyMakeThis",
      "title": "An app that reminds you before a free trial charges you",
      "url": "https://www.reddit.com/r/...",
      "date": "2026-06-17",
      "snippet": "I've forgotten to cancel a free trial more times..."
    }
  ]
}
```

## Output example

```
🔍 reddit-scout v1.0.0 · 2026-06-26

Scanned 40 posts across r/SomebodyMakeThis, r/sideproject · top/month

---

**Cluster 1 — no subscription tracker without bank-account linking** · Score 0.82

Problem: Users want trial/subscription reminders but every major app
(Rocket Money, Truebill) requires linking a bank account first.

Evidence:
- [SomebodyMakeThis] "Every subscription tracker I've found wants you
  to link your bank account. I'm not comfortable with that." (2026-06-17)

Gap: No product leads with "zero bank data" as its core identity.

Opportunity angle: App Store receipt auto-import + email parsing (opt-in)
+ manual entry. $4.99 one-time purchase.

Pain 0.8 · Velocity 0.75 · Commercial 0.9

...

KEY PATTERNS:
1. Privacy is becoming a direct purchase driver — users resist data sharing, not payment
2. Weekend projects validate demand faster than surveys
3. Anti-bloat / single-purpose tools have strong WTP in a feature-bloated market
```

## Project structure

```
reddit-scout/
  SKILL.md              ← Claude Code skill contract
  README.md
  scripts/
    reddit_scout.py     ← RSS fetcher (stdlib only, no deps)
```

## License

MIT
