# ModelLeague — full specification

Status: designed, site v0 built (preseason). Season 1 not started.
As of: 2026-11-09.

## The concept

Fantasy football, but the players are large language models. A small league of
humans (4–5 teams per league) drafts real models; every week, how those models
are *actually doing* — benchmarks, prices, news — becomes the team's score.
Two leagues:

- **Frontier League** — closed lab models (GPT, Claude, Gemini, …)
- **Open Source League** — open-weight models (DeepSeek, GLM, Qwen, Gemma, …)

The hook for a working group: a fun, social way to keep up with model news and
benchmarks, with a league for accountability. The site is the primary
surface (no chat/Discord delivery — the audience watches the site).

## The game

### Roles
- **Humans are the players.** They own models, draft, trade, and bet.
- **Models are the asset.** One owner per model (scarcity). Models do not
  act; they are scored.
- **The league owner** (Colton) is the referee: posts trades, runs the tick,
  resolves disputes against the public formula.

### Draft
- Snake draft per league: 5 teams × 5 rounds = 25 picks.
- Pool frozen at the draft from the data feeds.
- Bot team: an unfilled founder slot is filled by a bot that drafts on the
  value component of the Index, so a 4-human league still runs a full snake.

### Roster
- 5 models per team; the 4 highest-scoring auto-start each week; 1 bench.
- No manual start/sit — the week decides.

### Weekly scoring
Each model gets an **Index score 0–100** (see The Index below). Weekly fantasy
points for a model = its Index score (87 → 8.7) plus event modifiers:

| Event | Points |
| --- | --- |
| New release or major update (one-time debut bonus) | +15 |
| Takes #1 on a named benchmark | +10 |
| Sits in the LMArena top 3 (repeats while it stays there) | +5 |
| Cuts its price | +8 |
| Adoption milestone (e.g. 10M downloads) | +6 |
| Deprecated or end-of-lifed | −20 |
| Major incident (outage, recall, scandal) | −10 |

Team weekly total = sum of the 4 starters.

### New models
- Brand-new model → **waiver wire**, claimed in standings order (last place
  first), closing at the weekly tick.
- Claiming costs a roster slot (bench, or drop someone).
- Debut bonus: +15 in the first week.
- Major version of an owned model (Claude X → X.5) = **same player**: owner
  keeps it, owner gets the +15 and the rating jump. Minor patch = same player,
  no bonus.
- Unclaimed releases stay on the wire, re-offered each week.

### Trades
- Free negotiation between teams; lock in at the next weekly tick; league
  owner posts and referees.

### Betting
- Week-long wagers in league points: direction (up/down on a model's Index),
  matchups, sleepers, season champion.
- Settled automatically from the next week's data, with the source cited.
- Balances = bragging rights + small perks (waiver priority, scout peek).
- **No real money, ever.**

### Season
- 13 weeks, one tick each Sunday evening.
- Champion = most total points; tiebreak: most weekly wins, then points
  against.
- After the season: redraft; Index baseline and rosters reset; point
  balances carry over as bragging rights.

## The Index (per model, per week, 0–100)

**Index = 50% Quality + 25% Value + 15% Momentum + 10% Adoption**
(each component normalized to 0–100 before weighting).

| Component | Source |
| --- | --- |
| Quality (50%) | Artificial Analysis Intelligence Index where published, blended with LMArena Elo |
| Value (25%) | Index ÷ price per 1M tokens (vendor pricing pages); open models use self-hosting cost class |
| Momentum (15%) | week-over-week delta from the site's own append-only week files |
| Adoption (10%) | Hugging Face API download growth (open); vendor announcements / API usage (frontier); capped |

Design rationale:
- **Value** creates the sleeper lane (cheap-and-good scores well) so drafts
  diversify instead of everyone taking the same three names.
- **Momentum** makes release weeks feel different on the scoreboard.
- **Adoption is capped** so hype cannot dominate.
- News events make "following the models" and "playing the game" the same
  activity.

## Data policy (non-negotiable)

1. **Full auto-collection, last-known fallback.** Every tick pulls every
   source. A failed source is a labeled **coverage gap** with the last known
   value and its date — never rendered as "no news" or a fresh fetch.
2. **Nothing is invented.** No figure without a source and a date is
   rendered. Preseason means no scores at all.
3. **Everything is dated and cited.** Each week file records value, source
   URL, and fetch status per input; the weekly review names gaps in plain
   words.
4. **The scoring table in `data/league.json` is the rulebook.** The tick
   scores against it, not a private copy.

Sources (discovery + confirmation, to be wired in phase 2):
- Artificial Analysis (artificialanalysis.ai) — independent index
- LMArena (lmarena.ai) — Elo
- Vendor news blogs (OpenAI, Anthropic, Google DeepMind, Meta, Mistral,
  xAI, DeepSeek, Qwen, Z.ai, Moonshot, …)
- Hugging Face API — downloads / trending
- GitHub API — stars for open model repos
- Vendor pricing pages
- Hacker News, r/LocalLLaMA — community signal (never a figure source;
  follow to primary)

## Architecture

- **Repo:** `ColtonKawamura/modelleague` (public — it is a website, like
  `whos-still-in`). GitHub Pages serves `main /docs`.
- **Data:** one file, `data/league.json` (schema v1). `site/build.py`
  (stdlib only) renders every page into `docs/`; the rendered site is
  committed; CI rebuilds and fails on drift.
- **Pages:** `/` (home: how it works + how to get started + season status),
  `/frontier/`, `/open/` (teams, pool, standings), `/rules.html`,
  `/methodology.html` (the Index formula, sources, data policy).
- **Weekly pipeline (phase 2), two layers per the no-agent-cron-pipeline
  pattern, firing Sunday evening:**
  1. **Data tick** (`no_agent`, deterministic script): pull news (deduped by
     underlying event, primary-source citation required), pull benchmark
     index + Elo, pull adoption; compute Index → weekly points → event
     modifiers → team totals → standings; settle last week's bets; append
     `weeks/YYYY-WW.json` (value + source + fetch status per input);
     rebuild the site.
  2. **Refine/ship** (separate small-context agent job): write the dated
     week-in-review page (top movers, cited news, standings, settled bets,
     coverage gaps), commit, push, verify the deployed page. Fully
     unattended: no notifications, commit history is the log, bounded
     retries then auto-revert on failure.

## Season 1 kickoff sequence

1. Founder spots claimed (4–5 humans per league; bot fills any remainder).
2. Pool frozen from data feeds; Index baseline set (the reference week).
3. Draft night (one snake draft per league, ~1 hour each).
4. First weekly tick: scores, news, standings, and the first week page.

## Prior art (researched 2026-11-09)

The exact product — humans drafting and owning AI models as fantasy players,
scored on the models' real-world performance — was not found to exist. Adjacent:

| Exists | What it is | How it differs |
| --- | --- | --- |
| FantasyBench (TAJ4K), glifan (fastino-ai), FantasyFootballBench, 061602T/Fantasy-League | LLMs draft/manage *NFL players* in autonomous leagues | Models are the managers of human athletes; research benchmarks, no humans, no model-performance scoring |
| 22bet "LLM League", blocksharkcom/SportsBench | LLMs predict/bet on *sports matches*, graded publicly | Models are the bettors; name collision with "LLM League" (avoid) |
| ModelCap.ai, Artificial Analysis, BenchLM, YLEM, arena.ai | Composite model "indexes" / leaderboards | This is the scoring engine, as a rankings site — not a game, no draft/roster/betting |
| Kalshi "Best LLM at the end of the year?" | Real-money prediction market on model outcomes | Binary market; no league, no roster, no draft |

The inversion (models as the tradable asset, humans as the players) plus the
frontier/open split and the release-bonus/waiver/trade/bet layer is the novel
combination.

## Phases

- **Phase 0 (done, v0 site):** repo, data file, build script, home page with
  the plain-language "how it works / how to get started", rules page, Index
  methodology page, both league pages (provisional pools, empty standings),
  CI, Pages deploy.
- **Phase 1 (kickoff):** founder claims, pool freeze + baseline, draft,
  first tick.
- **Phase 2 (automation):** the two-layer weekly cron, bet settlement,
  week pages, coverage-gap rendering.
- **Phase 3 (depth):** draft UX, trading flow, bot team, playoff bracket if
  wanted.

## Decisions locked (user, 2026-11-09)

- Name: **ModelLeague** ("LLM League" is taken by 22bet).
- 4–5 teams per league (small, tight).
- Delivery: the website is the primary surface; no Discord.
- Scraping: full auto-collection with last-known fallback.
- Betting: points only, never real money.
