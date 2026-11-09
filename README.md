# ModelLeague

Fantasy football, but for large language models. You and a few friends draft real
AI models; every week, how those models are actually doing — benchmarks, prices,
news — becomes your team's score. Two leagues: **Frontier** (closed lab models)
and **Open Source** (open weights).

Live site: <https://coltonkawamura.github.io/modelleague/>

## How it works (short version)

- **Draft:** snake draft, 5 rounds, 5 teams per league. Each model is owned by
  exactly one team.
- **Weekly score:** every model gets a 0–100 composite ("the Index"): 50%
  quality (Artificial Analysis index + LMArena Elo), 25% value per dollar,
  15% week-over-week momentum, 10% adoption. A team's weekly points are the
  Index scores of its top 4 models, plus news bonuses (new release +15,
  benchmark #1 +10, price cut +8, …) and penalties (deprecation −20, incident −10).
- **Winning:** most points that week wins the week; most total over 13 weeks
  wins the season. Optional point-bets on predictions settle automatically.

No real money, ever. Full rules on the site; the complete design is in
[`SPEC.md`](SPEC.md).

## Repository layout

```
SPEC.md                 The full game spec (design, prior art, phases).
                        Lives in the repo root on purpose: GitHub Pages
                        serves docs/, so a root-level file is never public.

data/
  league.json           THE data: site settings (including the password-gate
                        hash), both leagues (teams, pools, standings, weeks),
                        and the scoring table. One file.

site/
  build.py              Renders every page into docs/ from league.json.
                        Standard library only, no dependencies.
  assets/style.css      The site's stylesheet (copied verbatim into docs/).
  assets/gate.js        The password gate: verifies the entered password
                        against the SHA-256 hash from league.json and
                        releases the page for the browser session.

docs/                   The built site. Committed; GitHub Pages serves
                        `main /docs`. Do not hand-edit — regenerate.

.github/workflows/ci.yml    Rebuilds on push/PR and fails if docs/ drifted.
.github/workflows/deploy.yml  Publishes docs/ to Pages on push to main.
```

## Build

```sh
python3 site/build.py        # render docs/ from data/league.json
```

Python 3.9+ standard library. CI does the same thing and runs
`git diff --exit-code docs/` — if the committed site does not match the data,
the build fails.

## Data policy

The site never fabricates a score. Before Season 1 starts there are no scores
on the site at all — the pools are provisional and the baseline is unset. Once
the weekly tick lands (phase 2), every number on the site is dated, sourced,
and carries its input's fetch status: a source that fails shows as a coverage
gap, and the last known value is reused and labeled, never replaced with
invention.
