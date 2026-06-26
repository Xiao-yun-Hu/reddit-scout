# reddit-scout

An AI agent skill that crawls Reddit subreddits via public RSS feeds and generates a scored **unmet-needs opportunity report** — no API key, no authentication required.

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
#   --sort     top | hot | new                   (default: top)
#   --time     day | week | month | year | all   (default: month)
#   --limit    posts per subreddit               (default: 25)
#   --delay    seconds between requests          (default: 4.0)
#   --out      save JSON to file instead of stdout
```

## How the RSS approach works

Reddit exposes public RSS/Atom feeds that require no authentication:

```
https://www.reddit.com/r/{subreddit}/top.rss?t=month&limit=25
```

The script parses these feeds, strips HTML from post bodies, and emits clean JSON. A configurable delay between requests (default **8s**) reduces the chance of hitting Reddit's rate limits. If you see frequent 429 errors, increase `--delay` to 12–15s or spread requests across sessions.

The JSON output shape:

```json
{
  "subreddits": ["SomebodyMakeThis", "sideproject"],
  "errors": [{"sub": "SaaS", "error": "HTTP 429: Too Many Requests"}],
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
  SKILL.md              ← Claude Code skill contract (detailed agent instructions)
  README.md
  scripts/
    reddit_scout.py     ← RSS fetcher (stdlib only, no deps)
```

---

<!-- agent-instructions-start -->
## Agent instructions

> This section is written for AI agents (Claude Code, Codex, Hermes, or any tool-calling LLM). Read it top to bottom before invoking any tool. Do not skip steps.

### When to trigger this skill

Trigger when the user asks for any of:
- Market gap analysis, unmet needs research, demand signal scanning
- "What are people complaining about on Reddit"
- "Find me trending pain points in [domain]"
- "What should someone build in [space]"
- Competitive intelligence via social listening

Do NOT trigger for: fetching a single subreddit for browsing, general Reddit search, or news monitoring (use `last30days` for that).

### Step 0: Resolve paths

```bash
SKILL_DIR="$HOME/.agents/skills/reddit-scout"
[ ! -f "$SKILL_DIR/scripts/reddit_scout.py" ] && \
  SKILL_DIR="$HOME/.claude/skills/reddit-scout"
[ ! -f "$SKILL_DIR/scripts/reddit_scout.py" ] && \
  echo "ERROR: reddit_scout.py not found" >&2 && exit 1

for py in python3.14 python3.13 python3.12 python3; do
  command -v "$py" >/dev/null 2>&1 && SCOUT_PYTHON="$py" && break
done
```

### Step 1: Map user intent to subreddits

Parse the user's message for a **topic** and **domain**. Then choose subreddits:

| If the topic is about... | Use preset or these subs |
|---|---|
| General unmet needs / no clear domain | `--preset=unmet_needs` |
| Physical products, consumer goods | `--preset=consumer` |
| B2B, SaaS, startups | `--preset=b2b` |
| Developer tools, open source | `--preset=dev` |
| AI, machine learning | `--preset=ai` |
| User named specific subreddits | Pass them as positional args |

If the topic implies a domain not covered by presets, choose 3–5 relevant subreddits from your knowledge and pass them as positional args.

### Step 2: Fetch

```bash
OUT_FILE=$(mktemp /tmp/reddit-scout-XXXXXX.json)

"$SCOUT_PYTHON" "$SKILL_DIR/scripts/reddit_scout.py" \
  --preset=unmet_needs \
  --sort=top \
  --time=month \
  --limit=25 \
  --delay=4 \
  --out="$OUT_FILE"
```

Then read the output:

```bash
cat "$OUT_FILE"
```

If a subreddit returns 0 posts due to HTTP 429, note it in the final report footer. Do not retry immediately — move on.

### Step 3: Cluster the posts

Read every post's `title` and `snippet`. Group posts that share the same **underlying unmet need** (not the same surface topic).

Clustering rules:
- Minimum viable cluster: 2 posts, OR 1 post with explicit commercial-intent language
- Ignore: pure showcases with no problem statement, monthly meta-threads, memes, job posts
- Name clusters as **problem phrases**, not solution names — "no subscription tracker without bank link" not "subscription manager app"
- Maximum 6 clusters in the output; if more exist, keep top 6 by composite score

### Step 4: Score each cluster

Rate each dimension 0.0–1.0:

**Pain intensity (0–1)**
- 0.9+: "insane", "hate this so much", multiple people describing the same personal story with frustration
- 0.7: clear frustration, specific examples of the problem causing real cost/effort
- 0.5: mild annoyance, single mention
- 0.3: theoretical / hypothetical pain

**Velocity (0–1)**
- 0.9+: 3+ posts on the same theme all dated within the last 14 days
- 0.7: posts spread across the month but at least 2 within last 2 weeks
- 0.5: posts spread evenly across the month
- 0.3: most posts are older than 3 weeks

**Commercial intent (0–1)**
- 0.9+: explicit "I'd pay", "currently paying $X for a worse solution", "if someone built this I'd buy immediately"
- 0.7: existing products named as inadequate + user has clear need
- 0.5: problem is real but no explicit purchase signal
- 0.3: nice-to-have, no financial pain

**Composite = (Pain × 0.3) + (Velocity × 0.3) + (Commercial × 0.4)**

### Step 5: Output format

Emit the report in this exact shape. Do not add section headers or restructure it.

```
🔍 reddit-scout v{VERSION} · {YYYY-MM-DD}

Scanned {N} posts across {subreddit list} · {sort}/{time_range}
{list any subreddits that failed with reason}

---

**Cluster 1 — {problem phrase}** · Score {X.XX}

Problem: {1–2 sentences}

Evidence:
- [{sub}] "{direct quote, max 120 chars}" ({date})
- [{sub}] "{direct quote, max 120 chars}" ({date})

Gap: {what existing solutions miss, 1 sentence}

Opportunity angle: {concrete product/service idea, 1–2 sentences}

Risk: {main blocker, 1 sentence}

Pain {X.X} · Velocity {X.X} · Commercial {X.X}

---

**Cluster 2 — ...** · Score {X.XX}
...

---

KEY PATTERNS:
1. {cross-cluster pattern}
2. {cross-cluster pattern}
3. {cross-cluster pattern}

Posts analyzed: {N} · Clusters found: {N} · Skipped (noise/meta): {N}
```

### Output rules

- Every evidence line must be a **direct quote** from the fetched data, not a paraphrase. If no good quote exists, use the post title verbatim.
- If a cluster has only 1 post, append `(thin signal — 1 source)` to the cluster name.
- Write in the same language the user wrote in (Chinese → Chinese output, English → English output).
- Do not append a Sources block. The evidence lines in each cluster are the citations.
- Do not add `##` section headers inside the report body.
<!-- agent-instructions-end -->

---

## Privacy & data

- Only accesses **public Reddit RSS feeds** — no login, no Reddit account, no OAuth
- Does not collect, store, or transmit any personal data
- No credentials of any kind are required or used
- Network access is limited to one endpoint: `reddit.com` RSS feeds

## License

MIT — see [LICENSE](LICENSE)
