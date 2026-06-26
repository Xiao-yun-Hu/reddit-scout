---
name: reddit-scout
version: "1.0.0"
description: "Crawl Reddit subreddits via RSS and generate scored unmet-needs opportunity clusters. No API key required. Use to find market gaps, validate demand signals, or surface trending pain points."
argument-hint: "reddit-scout unmet needs in B2B tools | reddit-scout AI productivity | reddit-scout --preset=consumer"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  openclaw:
    emoji: "🔍"
    tags: [reddit, market-research, unmet-needs, opportunity, signal]
---

# Reddit Scout — Unmet Needs Signal Finder

Crawls Reddit via public RSS (no API key), clusters posts by theme, scores each cluster on Pain × Velocity × Commercial Intent, and outputs a ranked opportunity report.

---

## STEP 0: Resolve runtime

```bash
SKILL_DIR="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)"
# Fallback: search known install paths
for d in \
  "$HOME/.agents/skills/reddit-scout" \
  "$HOME/.claude/skills/reddit-scout" \
  "$HOME/.codex/skills/reddit-scout"; do
  [ -f "$d/scripts/reddit_scout.py" ] && SKILL_DIR="$d" && break
done

if [ ! -f "$SKILL_DIR/scripts/reddit_scout.py" ]; then
  echo "ERROR: reddit_scout.py not found. Expected under $SKILL_DIR/scripts/" >&2
  exit 1
fi

for py in python3.14 python3.13 python3.12 python3; do
  command -v "$py" >/dev/null 2>&1 && SCOUT_PYTHON="$py" && break
done
[ -z "${SCOUT_PYTHON:-}" ] && echo "ERROR: python3 not found" >&2 && exit 1
```

---

## STEP 1: Parse user intent

Extract from the user's message:
- **TOPIC** — what domain / problem space to scan (e.g. "B2B sales tools", "AI productivity", "consumer health")
- **SUBREDDITS** — explicit overrides if user names specific subs; otherwise derive from TOPIC
- **PRESET** — if user says a category keyword, map to preset:
  - "consumer" / "物理产品" / "product" → `--preset=consumer`
  - "developer" / "dev" / "开发者" → `--preset=dev`
  - "AI" / "人工智能" → `--preset=ai`
  - "B2B" / "startup" / "创业" → `--preset=b2b`
  - anything else → `--preset=unmet_needs` (default)

**Default subreddit sets (built into the script):**
- `unmet_needs`: SomebodyMakeThis, sideproject, SaaS, Entrepreneur
- `consumer`: shutupandtakemymoney, BuyItForLife, SomebodyMakeThis, Frugal
- `b2b`: SaaS, Entrepreneur, smallbusiness, startups
- `dev`: sideproject, programming, webdev, MacApps
- `ai`: SaaS, artificial, MachineLearning, sideproject

If the user wants custom subreddits, pass them as positional args: `python3 reddit_scout.py Sub1 Sub2 Sub3`

---

## STEP 2: Fetch data

Run the script. Save output to a temp file so it doesn't flood stdout.

```bash
OUT_FILE=$(mktemp /tmp/reddit-scout-XXXXXX.json)
"$SCOUT_PYTHON" "$SKILL_DIR/scripts/reddit_scout.py" \
  --preset=unmet_needs \
  --sort=top \
  --time=month \
  --limit=25 \
  --delay=4 \
  --out="$OUT_FILE"
echo "Saved to: $OUT_FILE"
```

For custom subs:
```bash
"$SCOUT_PYTHON" "$SKILL_DIR/scripts/reddit_scout.py" Sub1 Sub2 Sub3 \
  --sort=top --time=month --limit=25 --delay=4 --out="$OUT_FILE"
```

After the script runs, read the file:
```bash
cat "$OUT_FILE"
```

---

## STEP 3: Analyze — cluster and score

Read the JSON. For each post, extract:
- Title
- Snippet (first 400 chars of body)
- Subreddit
- Date

**Clustering rules:**
1. Group posts that share a common underlying problem or unmet need.
2. Ignore posts that are: pure showcases with no problem statement, meta-discussions about the subreddit, memes, monthly threads.
3. Minimum cluster size: 2 posts OR 1 post with very strong signal (high upvote language, explicit "I'd pay").
4. Name each cluster as a short problem phrase, not a solution (e.g. "can't track subscriptions without bank link" not "subscription manager").

**Scoring rubric (0–1 each):**

| Dimension | What to look for |
|---|---|
| **Pain intensity** | Emotional language ("insane", "hate", "so frustrated"), repeated personal stories, multiple people describing the same situation |
| **Velocity** | Post date recency — if multiple posts on the same theme appear in the last 2 weeks vs scattered over the month, velocity is higher |
| **Commercial intent** | "I'd pay", "currently paying $X for", "switched from X", "if someone built this I'd buy it immediately", "no good tool exists" |

**Composite score = (Pain × 0.3) + (Velocity × 0.3) + (Commercial × 0.4)**

---

## STEP 4: Output format

Produce the report in this exact structure. No `##` section headers in body. Bold lead-ins only.

```
🔍 reddit-scout v1.0.0 · {YYYY-MM-DD}

Scanned {N} posts across {subreddit list} · top/{time_range}

---

**Cluster 1 — {cluster name}** · Score {X.XX}

Problem: {1–2 sentences describing the unmet need}

Evidence:
- [{sub}] "{direct quote or paraphrase}" (date)
- [{sub}] "{direct quote or paraphrase}" (date)

Gap: {what existing solutions miss}

Opportunity angle: {concrete product/service idea, 1–2 sentences}

Risk: {main blockers}

Pain {X.X} · Velocity {X.X} · Commercial {X.X}

---

**Cluster 2 — {cluster name}** · Score {X.XX}
...

---

KEY PATTERNS:
1. {pattern}
2. {pattern}
3. {pattern}

Subreddits: {list} · Posts analyzed: {N} · Clusters found: {N}
```

---

## Output rules

- Always include raw quotes from actual posts — never paraphrase without quoting
- If a cluster has only 1 post, mark it `(thin signal — 1 source)`
- If a subreddit returned 0 posts (rate limit / error), say so in the footer
- Max 6 clusters — if more exist, show top 6 by score
- Chinese or English output based on what language the user wrote in

---

## Quick invocation examples

```
/reddit-scout
/reddit-scout B2B sales tools
/reddit-scout --preset=consumer
/reddit-scout SomebodyMakeThis SaaS WantToLearnTo
/reddit-scout AI tools for solo founders
```
