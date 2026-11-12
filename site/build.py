#!/usr/bin/env python3
"""Render the ModelLeague site from data/league.json into docs/.

Standard library only. The rendered pages are committed; CI rebuilds and
fails when docs/ drifts from the data file.

Usage:
    python3 site/build.py            # render into docs/
    python3 site/build.py --out DIR  # render into DIR instead
"""
import argparse
import html
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "league.json"
ASSETS_DIR = ROOT / "site" / "assets"

PAGES = [
    "index.html",
    "rules.html",
    "methodology.html",
    "frontier/index.html",
    "open/index.html",
    "assets/style.css",
    "assets/gate.js",
]


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def points_badge(points):
    cls = "pos" if points >= 0 else "neg"
    sign = "+" if points >= 0 else "-"
    return '<span class="pts %s">%s%d</span>' % (cls, sign, abs(points))


def doc(prefix, title, body, league_class="", gate_json="{}"):
    """Wrap a page body in the shared header/footer. `prefix` is '' at the
    site root and '../' from subpages, so all links stay relative. The inline
    head script runs before first paint: if the password gate is on and this
    browser session is not authenticated, it marks <html> as gated and the
    CSS hides the league content, leaving only the lock screen."""
    nav = [
        ("Home", "%s" % prefix),
        ("Frontier", "%sfrontier/" % prefix),
        ("Open Source", "%sopen/" % prefix),
        ("Draft", "%sdraft.html" % prefix),
        ("Rules", "%srules.html" % prefix),
        ("The Index", "%smethodology.html" % prefix),
    ]
    nav_html = "".join('<a href="%s">%s</a>' % (href, label) for label, href in nav)
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<script>
  (function () {
    var g = %s;
    window.__ML_GATE__ = g;
    if (g.enabled && g.sha256) {
      try {
        if (sessionStorage.getItem("modelleague-auth") !== "1") {
          document.documentElement.classList.add("gated");
        }
      } catch (e) {}
    }
  })();
</script>
<link rel="stylesheet" href="%sassets/style.css">
<script src="%sassets/gate.js" defer></script>
</head>
<body class="%s">
<div class="gate" id="ml-gate">
  <form class="gate-box" id="ml-gate-form" autocomplete="off">
    <div class="gate-logo">ModelLeague</div>
    <h1>Members only</h1>
    <p class="gate-sub">This league is private. Enter the password to see the
    boards.</p>
    <input type="password" id="ml-gate-pass" name="password"
           placeholder="Password" required>
    <button type="submit">Enter</button>
    <p class="gate-error" id="ml-gate-error" hidden>Wrong password &mdash; try
    again.</p>
    <p class="gate-foot">Forgot it? Ask the league owner.</p>
  </form>
</div>
<header>
  <div class="wrap header-inner">
    <a class="brand" href="%s">ModelLeague</a>
    <nav class="nav">%s</nav>
  </div>
</header>
<main class="wrap">
%s
</main>
<footer>
  <div class="wrap">
    ModelLeague is a points-only game: no real money, ever. Every number on
    this site is dated and sourced; the rules and the scoring formula are
    public. Built by Colton Kawamura.
    <a href="https://github.com/ColtonKawamura/modelleague">Repository</a>
    &middot; <a href="%srules.html">Rules</a>
    &middot; <a href="%smethodology.html">The Index</a>
  </div>
</footer>
</body>
</html>
""" % (
        esc(title),
        gate_json,
        prefix,
        prefix,
        league_class,
        prefix,
        nav_html,
        body,
        prefix,
        prefix,
    )


def banner(data):
    s = data["site"]
    return (
        '<div class="banner"><strong>Season %d &middot; %s</strong> &mdash; '
        "pools are provisional and the baseline is not yet set. "
        "Data as of %s.</div>" % (s["season"], esc(s["season_status"]), esc(s["as_of"]))
    )


def home(data, gate_json):
    s = data["site"]
    leagues_html = ""
    for lid in ("frontier", "open"):
        lg = data["leagues"][lid]
        open_slots = sum(1 for t in lg["teams"] if t["status"] == "open")
        leagues_html += (
            '  <a class="card league-card card-%s" href="%s/">\n'
            '    <div class="card-title">%s</div>\n'
            '    <div class="card-sub">%s</div>\n'
            '    <div class="card-meta">%d candidate models &middot; %d of %d founder spots open</div>\n'
            "  </a>\n"
        ) % (
            lid,
            lid,
            esc(lg["name"]),
            esc(lg["slugline"]),
            len(lg["pool"]),
            open_slots,
            len(lg["teams"]),
        )
    body = """
%s
<section class="hero">
  <h1>%s</h1>
  <p class="lede">You and a few friends draft real AI models. Every week, how those
  models are <em>actually doing</em> &mdash; benchmarks, prices, news &mdash; becomes
  your team's score. Two leagues: one for closed frontier models, one for open
  weights.</p>
</section>

<section>
  <h2>How it works</h2>
  <ol class="steps">
    <li><strong>You draft AI models.</strong> On draft night you and your
    league-mates take turns picking from a list of real models &mdash; GPT, Claude,
    Gemini, DeepSeek, Llama, and the rest &mdash; until you each own five.
    Each model can be owned by exactly one person, so the hot ones get sniped.</li>
    <li><strong>Every week, each model gets a score out of 100.</strong> The score
    &mdash; <a href="methodology.html">the Index</a> &mdash; measures how good the model is
    <em>right now</em>: how well it does on the standard tests, how much it costs,
    whether it is getting better than last week, and whether people are using it.</li>
    <li><strong>Your team's points are the scores of your four best models,
    added up.</strong> On top of that, news moves the score: a new version
    releases (+15), a model takes the top of a big test (+10), a price cut (+8).
    Penalties too: a model gets shut down (&minus;20) or has a scandal (&minus;10).
    Your fifth model sits on the bench.</li>
    <li><strong>Most points that week wins the week. Most points over
    13 weeks wins the season.</strong> That is the whole game.</li>
    <li><strong>Optional: bet points on predictions.</strong> &ldquo;Will GPT-6.1 go up
    or down next week?&rdquo; &ldquo;Which model leads the Index at the end of the
    season?&rdquo; Bets settle automatically from the next week's data. Bragging
    rights and small perks &mdash; never real money.</li>
  </ol>
</section>

<section>
  <h2>How to get started</h2>
  <ol class="steps">
    <li><strong>Claim a founder spot.</strong> Each league has five slots and
    first come, first served: %s. You can run a team in both leagues if you
    want &mdash; it is just double the drafts.</li>
    <li><strong>Pick a team name.</strong> Send it with your claim. A good name
    helps; it is the only requirement.</li>
    <li><strong>Show up to the draft.</strong> One snake draft, five rounds,
    about an hour. You do not need to be an LLM expert &mdash; the Index table
    tells you what each model is worth at the moment.</li>
    <li><strong>Then every Sunday a new week lands on this site:</strong> the
    scores, the news that caused them, the standings, and settled bets. If you
    play, that is your result. If you only follow, that is your model-news
    digest.</li>
  </ol>
  <p class="aside">Not playing? The site still works as a spectator: the Index
  table and the weekly review are the product, and the league is the reason to
  come back.</p>
</section>

<section>
  <h2>The leagues</h2>
  <div class="cards">%s</div>
</section>
""" % (banner(data), esc(s["tagline"]), esc(s["contact"]), leagues_html)
    return doc("", "ModelLeague — fantasy football for large language models", body, gate_json=gate_json)


def rules(data, gate_json):
    sc = data["scoring"]
    event_rows = "".join(
        "<tr><td>%s</td><td class='num'>%s</td></tr>" % (esc(e["event"]), points_badge(e["points"]))
        for e in sc["events"]
    )
    body = """
%s
<section>
  <h1>Rules</h1>
  <p class="lede">The whole rulebook, in plain language. The scoring numbers
  below are the published ones &mdash; the weekly tick scores against them.</p>
</section>

<section>
  <h2>The draft</h2>
  <ul>
    <li>One snake draft per league: five teams, five rounds, 25 picks. Snake
    order (last pick in round one goes first in round two).</li>
    <li>The pool is frozen at the draft from the data feeds. Every model in the
    pool can be owned by <strong>exactly one</strong> team &mdash; there is no duplication,
    so the strongest models are gone by the first round and everyone else has
    to diversify.</li>
    <li>A model that ships <em>after</em> the draft does not re-draft; it hits the
    waiver wire (below).</li>
  </ul>
</section>

<section>
  <h2>The roster</h2>
  <ul>
    <li>Each team owns <strong>five</strong> models.</li>
    <li>Every week the <strong>four</strong> highest-scoring models on your roster
    auto-start; the fifth sits on the bench. There are no start/sit calls to
    make &mdash; the week decides.</li>
  </ul>
</section>

<section>
  <h2>Weekly scoring</h2>
  <p>Each model gets an <a href="methodology.html">Index score from 0 to 100</a>
  every week. A model's weekly fantasy points are its Index score (an 87 means
  8.7 points), plus the event modifiers below, which come from that week's
  news:</p>
  <table>
    <thead><tr><th>Event</th><th>Points</th></tr></thead>
    <tbody>%s</tbody>
  </table>
  <p class="aside">Event modifiers are one-time for the event that triggers
  them (a release bonus pays once; the top-3 arena bonus repeats each week the
  model stays in the top 3).</p>
</section>

<section>
  <h2>New models</h2>
  <ul>
    <li><strong>Waiver wire.</strong> A brand-new model goes to the waiver wire,
    claimed in strict order: last-place team first, then up the standings.
    Claiming closes at the weekly tick.</li>
    <li><strong>It costs a slot.</strong> A new model takes a bench spot, or you
    drop someone to make room. If you pass, the next team in line gets a
    chance. Only one team can own a model, so a hot release is a race down the
    priority list.</li>
    <li><strong>The debut bonus.</strong> A brand-new model earns the +15 release
    bonus in its first week &mdash; front-running the hype is a real strategy.</li>
    <li><strong>Upgrades keep ownership.</strong> A major version of a model you
    already own (Claude X &rarr; Claude X.5) is the <em>same</em> player: nobody else can
    take it, and <em>you</em> collect the +15 and the rating jump. A minor patch is
    the same player with no bonus &mdash; just a normal score wobble.</li>
    <li><strong>Unwanted models sit.</strong> A release nobody claims stays on the
    wire, offered again each week, until someone wants it.</li>
  </ul>
</section>

<section>
  <h2>Trades</h2>
  <ul>
    <li>Teams may trade models with each other, freely, by negotiation.</li>
    <li>Trades lock in at the next weekly tick and score from that week.</li>
    <li>The league owner is the referee: a trade is valid when both sides say
    yes and the owner posts it.</li>
  </ul>
</section>

<section>
  <h2>Betting</h2>
  <ul>
    <li>Each week, players may bet their league points on predictions:
    direction (up/down on a model's Index), matchups (will A out-score B?),
    sleepers (will a non-top-5 model crack the top 5 by week N?), and the
    season champion.</li>
    <li>Bets settle automatically from the next week's data, with the source
    cited. No disputes: the Index formula and the published data are the
    referee.</li>
    <li>Point balances are bragging rights plus small perks (waiver priority,
    a &ldquo;scout&rdquo; peek at the next week's preview). <strong>No real money, ever.</strong></li>
  </ul>
</section>

<section>
  <h2>The season</h2>
  <ul>
    <li><strong>13 weeks</strong>, one tick each Sunday evening. The season
    champion is the team with the most total points; ties break by most
    weekly wins, then by fewest points against.</li>
    <li>An unfilled founder slot is taken by a <strong>bot team</strong> that drafts
    on the value component of the Index, so a four-human league still runs a
    full snake.</li>
    <li>After the season: redraft. Pools, rosters and the Index baseline all
    reset; point balances carry over as bragging rights.</li>
  </ul>
</section>
""" % (banner(data), event_rows)
    return doc("", "Rules — ModelLeague", body, gate_json=gate_json)


def methodology(data, gate_json):
    sc = data["scoring"]
    comp_rows = "".join(
        "<tr><td><strong>%s</strong> &mdash; %d%%</td><td>%s</td></tr>"
        % (esc(c["label"]), c["weight"], esc(c["plain"]))
        for c in sc["index_components"]
    )
    body = """
%s
<section>
  <h1>The Index</h1>
  <p class="lede">One number, per model, per week, from 0 to 100. This is the
  page that makes the betting fair: the formula is public, every input is dated
  and sourced, and a failed source shows up as a gap instead of a silent
  &ldquo;no change.&rdquo;</p>
</section>

<section>
  <h2>The formula</h2>
  <p><strong>Index = 50%%&nbsp;Quality + 25%%&nbsp;Value + 15%%&nbsp;Momentum + 10%%&nbsp;Adoption</strong>,
  each component normalized to 0&ndash;100 before the weights are applied.</p>
  <table>
    <thead><tr><th>Component</th><th>What it measures</th></tr></thead>
    <tbody>%s</tbody>
  </table>
</section>

<section>
  <h2>Where the inputs come from</h2>
  <ul>
    <li><strong>Quality:</strong> the
    <a href="https://artificialanalysis.ai">Artificial Analysis</a> Intelligence
    Index where published, blended with
    <a href="https://lmarena.ai">LMArena</a> Elo (the crowd-sourced
    head-to-head vote) for the feel component.</li>
    <li><strong>Value:</strong> the Index score divided into the published API
    price per million tokens (frontier) or the self-hosting cost class (open).
    Vendor pricing pages are the source.</li>
    <li><strong>Momentum:</strong> this week's composite minus last week's, from
    the site's own archive &mdash; the week files are append-only.</li>
    <li><strong>Adoption:</strong> the Hugging Face API for download growth on
    open models; vendor announcements and API-usage reporting for frontier.
    Capped so hype cannot dominate.</li>
    <li><strong>News events</strong> (the +15/&minus;20 modifiers): vendor news blogs,
    Hacker News, and r/LocalLLaMA, deduplicated by underlying event and
    required to cite a primary source.</li>
  </ul>
</section>

<section>
  <h2>The data policy</h2>
  <ul>
    <li><strong>Full auto-collection, last-known fallback.</strong> Every tick
    pulls every source. A source that fails does not become &ldquo;no news&rdquo;: the
    table shows a <em>coverage gap</em> with the last known value and its date,
    labeled as stale.</li>
    <li><strong>Nothing is invented.</strong> A figure without a source and a
    date is not a figure; it is not rendered. Preseason means no scores at
    all &mdash; until the baseline is set, the standings are empty by design.</li>
    <li><strong>Everything is dated and cited.</strong> Each week file records, per
    input: the value, the source URL, and the fetch status. The weekly review
    names any coverage gaps in plain words.</li>
  </ul>
  <p class="aside">Reference points, so the raw inputs are not abstract: the
  Artificial Analysis Intelligence Index on 5 Nov 2026 had the top open-weight
  models at DeepSeek V4.1 Flash (33), GLM-5.3 (32) and MiMo-V2.6-Pro (30), per
  the <a href="https://hokai.io/guides/best-open-weight-models">hokai.io roundup of
  5 Nov 2026</a>; the overall index on 8 Nov 2026 had Gemini 4 Carbon at 60,
  per <a href="https://ylem.si/models/">YLEM's tracker</a>. These are dated
  snapshots of the raw inputs &mdash; not ModelLeague scores, which start at the
  Season 1 baseline.</p>
</section>

<section>
  <h2>Why this shape makes a good game</h2>
  <ul>
    <li><strong>The value component creates the sleeper lane.</strong> A cheap
    model that is close to the flagships scores well and is the reason nobody
    has to draft the same three names.</li>
    <li><strong>Momentum makes weeks matter.</strong> A lab's big release week
    moves several models at once, so a &ldquo;quiet&rdquo; week and a release week feel
    different on the scoreboard.</li>
    <li><strong>News is a score, not a newsletter.</strong> The event modifiers are
    why the league and the news are the same activity: you follow the models
    <em>because</em> the follow is the game.</li>
  </ul>
</section>
""" % (banner(data), comp_rows)
    return doc("", "The Index — ModelLeague", body, gate_json=gate_json)


def league_page(data, lid, gate_json):
    lg = data["leagues"][lid]
    prefix = "../"
    cls = "league-frontier" if lid == "frontier" else "league-open"

    team_rows = ""
    for t in lg["teams"]:
        name = esc(t["name"]) if t["name"] else "&mdash;"
        owner = esc(t["owner"]) if t["owner"] else "&mdash;"
        if t["status"] == "open":
            pill = '<span class="pill open">founder spot open</span>'
        else:
            pill = '<span class="pill claimed">claimed</span>'
        team_rows += "<tr><td class='num'>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            t["slot"], name, owner, pill
        )

    pool_rows = ""
    for m in lg["pool"]:
        note = " &mdash; %s" % esc(m["note"]) if m.get("note") else ""
        pool_rows += "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(m["name"]), esc(m["lab"]), note
        )

    if lg["standings"]:
        st_rows = ""
        for i, row in enumerate(lg["standings"], 1):
            st_rows += (
                "<tr><td class='num'>%d</td><td>%s</td><td class='num'>%.1f</td>"
                "<td class='num'>%d</td></tr>" % (i, esc(row["team"]), row["points"], row["wins"])
            )
        standings = (
            "<table><thead><tr><th>#</th><th>Team</th><th>Points</th><th>Weeks won</th></tr></thead>"
            "<tbody>%s</tbody></table>" % st_rows
        )
    else:
        standings = (
            '<p class="empty">Season %d has not started. Standings appear here from the '
            "first weekly tick after the draft.</p>" % data["site"]["season"]
        )

    body = """
%s
<section class="league-hero">
  <h1>%s</h1>
  <p class="lede">%s</p>
</section>

<section>
  <h2>Teams</h2>
  <table>
    <thead><tr><th>Slot</th><th>Team</th><th>Owner</th><th>Status</th></tr></thead>
    <tbody>%s</tbody>
  </table>
</section>

<section>
  <h2>Model pool</h2>
  <p class="aside">%s</p>
  <table>
    <thead><tr><th>Model</th><th>Lab</th><th>Note</th></tr></thead>
    <tbody>%s</tbody>
  </table>
</section>

<section>
  <h2>Standings</h2>
  %s
</section>

<section>
  <h2>What happens next</h2>
  <ol class="steps">
    <li><strong>Founder spots are claimed</strong> &mdash; first come, first served.</li>
    <li><strong>The pool is frozen</strong> from the data feeds and the baseline Index
    is set.</li>
    <li><strong>Draft night:</strong> one snake draft, five rounds.</li>
    <li><strong>First week lands</strong> on the next Sunday tick: scores, news,
    standings.</li>
  </ol>
</section>

<section>
  <a class="draft-btn" href="%sdraft.html?league=%s">Draft a Team &rarr;</a>
</section>
""" % (banner(data), esc(lg["name"]), esc(lg["slugline"]), team_rows, esc(lg["pool_status"]), pool_rows, standings, prefix, lid)
    return doc(prefix, "%s — ModelLeague" % lg["name"], body, league_class=cls, gate_json=gate_json)


def build(out_dir):
    data = load_data()
    s = data["site"]
    gate_json = json.dumps(
        {"enabled": bool(s.get("gate_enabled", False)), "sha256": s.get("gate_sha256")}
    )
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "frontier").mkdir(parents=True, exist_ok=True)
    (out_dir / "open").mkdir(parents=True, exist_ok=True)
    (out_dir / "assets").mkdir(parents=True, exist_ok=True)

    pages = {
        "index.html": home(data, gate_json),
        "rules.html": rules(data, gate_json),
        "methodology.html": methodology(data, gate_json),
        "frontier/index.html": league_page(data, "frontier", gate_json),
        "open/index.html": league_page(data, "open", gate_json),
    }
    for rel, content in pages.items():
        path = out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    shutil.copyfile(ASSETS_DIR / "style.css", out_dir / "assets" / "style.css")
    shutil.copyfile(ASSETS_DIR / "gate.js", out_dir / "assets" / "gate.js")

    # Copy draft page if it exists
    draft_src = ROOT / "site" / "draft.html"
    draft_dst = out_dir / "draft.html"
    if draft_src.exists():
        draft_dst.write_text(draft_src.read_text(encoding="utf-8"), encoding="utf-8")

    # Copy data file so draft.html can fetch it
    data_src = ROOT / "data" / "league.json"
    data_dst = out_dir / "data" / "league.json"
    if data_src.exists():
        data_dst.parent.mkdir(parents=True, exist_ok=True)
        data_dst.write_text(data_src.read_text(encoding="utf-8"), encoding="utf-8")

    for rel in PAGES:
        if not (out_dir / rel).exists():
            raise SystemExit("build error: missing %s" % rel)
    print("rendered %d pages into %s" % (len(pages), out_dir))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "docs"), help="output directory (default: docs/)")
    args = parser.parse_args()
    build(args.out)


if __name__ == "__main__":
    sys.exit(main())
