#!/usr/bin/env python3
"""Publish a weekly AI Radio episode. Safe to re-run for the same episode.

Run from the repo root:
  python3 scripts/radio.py --mp3 ai_radio.mp3 --notes show_notes.json --cover cover.jpg

What it does
  1. Copies the audio to audio/ and a resized cover to images/.
  2. Writes the episode page radio/<date>-<slug>.html (player, summary, transcript).
  3. Records the episode in radio/episodes.json, then regenerates:
       ai-radio.html   (archive of every episode, newest first)
       radio.xml       (podcast RSS feed with audio enclosures)
       the homepage "Listen to this week's AI Radio" band in index.html
  Afterwards run `python3 scripts/seo.py` (adds Plausible, sitemap, llms.txt) and commit.
"""
import argparse
import html
import json
import re
import shutil
import subprocess
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.youraigap.com"
EPISODES = ROOT / "radio" / "episodes.json"
E = html.escape

AUTHOR_LD = {
    "@type": "Person",
    "name": "Ken Leatherman",
    "url": "https://kenleatherman.com",
}

NAV = """    <nav class="main-nav">
      <a href="{p}start-here.html">Start Here</a>
      <a href="{p}senior-housing.html">Senior Housing</a>
      <a href="{p}governance.html">Governance</a>
      <a href="{p}insurance-coverage.html">Insurance Coverage</a>
      <a href="https://kenleatherman.com" class="nav-cta">About Ken</a>
    </nav>"""

FOOTER = """<footer class="site-footer">
  <div class="container">
    <div class="foot-links">
      <a href="https://kenleatherman.com">kenleatherman.com</a>
      <a href="https://kenleatherman.substack.com/">The LITT Briefing</a>
      <a href="https://linkedin.com/in/kenleatherman">LinkedIn</a>
      <a href="mailto:ken_leatherman@ajg.com">ken_leatherman@ajg.com</a>
    </div>
    <p>Leadership in Tough Times &middot; Senior Housing: The AI Gap &middot; Storify Studio</p>
    <p class="disclosure">Ken Leatherman is Senior Vice President at Gallagher. This site, its books, and The Second Ledger methodology are published independently through Storify Studio. Nothing on this site is a Gallagher product, and nothing here should be read as Gallagher-endorsed.</p>
  </div>
</footer>"""

DISCLOSURE = (
    "AI Radio is an AI-generated audio program. The hosts and callers are synthetic voices, "
    "not real people, and the figures and claims are as stated in the program. "
    "Check them against primary sources before relying on them. "
    "This is general information, not legal, insurance, or compliance advice."
)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def pretty_date(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return d.strftime("%B ") + str(d.day) + d.strftime(", %Y")


def seconds(duration):
    parts = [int(x) for x in duration.split(":")]
    s = 0
    for x in parts:
        s = s * 60 + x
    return s


def head(title, desc, url, image, path_prefix, extra_ld=None, rss=False):
    ld = extra_ld or {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": desc,
        "url": url,
        "author": AUTHOR_LD,
        "isPartOf": {"@type": "WebSite", "name": "AI Implementation", "url": BASE + "/"},
    }
    t = E(title, quote=True)
    d = E(desc, quote=True)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{E(title)}</title>
<meta name="description" content="{d}">
<link rel="stylesheet" href="{path_prefix}styles.css">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="AI Implementation">
<meta property="og:type" content="website">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{image}">
<link rel="alternate" type="application/rss+xml" title="AI Implementation" href="{BASE}/feed.xml">
<link rel="alternate" type="application/rss+xml" title="AI Radio" href="{BASE}/radio.xml">
<script type="application/ld+json">
{json.dumps(ld, indent=2, ensure_ascii=False)}
</script>
</head>
<body>

<header class="site-header">
  <div class="nav-wrap">
    <a href="{path_prefix}index.html" class="brand">AI <span>Implementation</span></a>
    <button class="nav-toggle" aria-label="Toggle menu">Menu</button>
{NAV.format(p=path_prefix)}
  </div>
</header>
"""


def episode_page(ep, notes):
    url = f"{BASE}/radio/{ep['id']}.html"
    image = f"{BASE}/images/radio-{ep['id']}.jpg"
    title = f"AI Radio: {ep['title']} | AI Implementation"
    ld = {
        "@context": "https://schema.org",
        "@type": "PodcastEpisode",
        "name": ep["title"],
        "description": ep["summary"],
        "datePublished": ep["date"],
        "url": url,
        "image": image,
        "duration": "PT%dM%dS" % divmod(seconds(ep["duration"]), 60),
        "associatedMedia": {
            "@type": "AudioObject",
            "contentUrl": f"{BASE}/audio/{ep['id']}.mp3",
            "encodingFormat": "audio/mpeg",
        },
        "partOfSeries": {"@type": "PodcastSeries", "name": "AI Radio", "url": BASE + "/ai-radio.html"},
        "author": AUTHOR_LD,
    }
    rows = []
    for t in notes.get("timecoded_transcript", []):
        rows.append(
            f'      <p><span class="tc">{E(t["timecode"])}</span> <strong>{E(t["speaker"])}:</strong> {E(t["text"])}</p>'
        )
    body = f"""
<div class="hero">
  <div class="container">
    <div class="kicker">AI Radio &middot; {pretty_date(ep['date'])}</div>
    <h1>{E(ep['title'])}</h1>
    <p class="lede">{E(ep['summary'])}</p>
  </div>
</div>

<div class="container">
  <div class="breadcrumb"><a href="../index.html">AI Implementation</a> &rsaquo; <a href="../ai-radio.html">AI Radio</a> &rsaquo; {pretty_date(ep['date'])}</div>

  <section class="block">
    <div class="radio-player">
      <img class="radio-cover" src="../images/radio-{ep['id']}.jpg" alt="AI Radio cover art: {E(ep['title'], quote=True)}" width="220" height="220">
      <div class="radio-controls">
        <p class="radio-meta">{E(ep['duration'])} &middot; MP3</p>
        <audio controls preload="none" src="../audio/{ep['id']}.mp3">Your browser does not support audio playback. <a href="../audio/{ep['id']}.mp3">Download the MP3</a>.</audio>
        <p><a href="../audio/{ep['id']}.mp3" download>Download the MP3</a></p>
      </div>
    </div>
    <p class="radio-note">{E(DISCLOSURE)}</p>
  </section>

  <section class="block shaded">
    <h2>Take the next step</h2>
    <p>Each week's AI Radio follows the same three questions as the written posts: who decides, what is covered, and where the file is. Start with the free <a href="../general-business-packet.html">General Business Starter Packet</a> or, if you run a senior housing organization, the <a href="../starter-packet.html">senior housing packet</a>.</p>
  </section>

  <section class="block">
    <details class="transcript">
      <summary>Read the transcript</summary>
{chr(10).join(rows)}
    </details>
  </section>

  <p style="margin-bottom:60px;"><a href="../ai-radio.html">&larr; All AI Radio episodes</a></p>
</div>

{FOOTER}

<script src="../script.js"></script>
</body>
</html>
"""
    return head(title, ep["summary"], url, image, "../", ld) + body


def archive_page(eps):
    url = f"{BASE}/ai-radio.html"
    desc = "Weekly AI Radio from AI Implementation: a short audio program on AI governance, insurance coverage, and who owns the decision."
    items = []
    for ep in eps:
        items.append(
            f"""      <li class="radio-item">
        <img src="images/radio-{ep['id']}.jpg" alt="" width="96" height="96" loading="lazy">
        <div>
          <a href="radio/{ep['id']}.html"><strong>{E(ep['title'])}</strong></a>
          <span class="archive-date">{pretty_date(ep['date'])} &middot; {E(ep['duration'])}</span>
          <p>{E(ep['summary'])}</p>
        </div>
      </li>"""
        )
    latest = eps[0]
    body = f"""
<div class="hero">
  <div class="container">
    <div class="kicker">AI Radio</div>
    <h1>The week in AI governance, in about ten minutes.</h1>
    <p class="lede">A short weekly audio program on who owns the decision when AI is involved, what your insurance covers, and what to ask next. Listen here, or read the transcript on each episode page.</p>
    <a href="radio/{latest['id']}.html" class="hero-cta">Listen to the latest episode</a>
  </div>
</div>

<div class="container">
  <div class="breadcrumb"><a href="index.html">AI Implementation</a> &rsaquo; AI Radio</div>

  <section class="block">
    <h2>All episodes</h2>
    <ul class="radio-list">
{chr(10).join(items)}
    </ul>
    <p class="radio-note">{E(DISCLOSURE)}</p>
  </section>

  <p style="margin-bottom:60px;"><a href="index.html">&larr; Back to AI Implementation</a></p>
</div>

{FOOTER}

<script src="script.js"></script>
</body>
</html>
"""
    return head("AI Radio: Weekly AI Governance Audio | AI Implementation", desc, url,
                f"{BASE}/images/radio-{latest['id']}.jpg", "") + body


def tile(ep):
    return f"""<!-- radio:start -->
<section class="radio-band">
  <div class="container radio-band-inner">
    <img src="images/radio-{ep['id']}.jpg" alt="" width="140" height="140">
    <div>
      <div class="radio-band-kicker">AI Radio &middot; {pretty_date(ep['date'])} &middot; {E(ep['duration'])}</div>
      <h2>Listen to this week's AI Radio</h2>
      <p>{E(ep['title'])}. {E(ep['summary'])}</p>
      <a href="radio/{ep['id']}.html" class="radio-btn">Listen now</a>
      <a href="ai-radio.html" class="radio-band-more">All episodes &rarr;</a>
    </div>
  </div>
</section>
<!-- radio:end -->"""


def update_home(ep):
    p = ROOT / "index.html"
    s = p.read_text(encoding="utf-8")
    block = tile(ep)
    if "<!-- radio:start -->" in s:
        s = re.sub(r"<!-- radio:start -->.*?<!-- radio:end -->", lambda m: block, s, flags=re.S)
    else:
        marker = '<div class="hero">'
        assert marker in s, "hero not found in index.html"
        s = s.replace(marker, block + "\n\n" + marker, 1)
    p.write_text(s, encoding="utf-8")


def write_feed(eps):
    items = []
    for ep in eps[:50]:
        pub = format_datetime(datetime.strptime(ep["date"], "%Y-%m-%d").replace(hour=12))
        size = (ROOT / "audio" / f"{ep['id']}.mp3").stat().st_size
        url = f"{BASE}/radio/{ep['id']}.html"
        items.append(
            f"    <item><title>{E(ep['title'])}</title><link>{url}</link><guid>{url}</guid>"
            f"<pubDate>{pub}</pubDate><description>{E(ep['summary'])}</description>"
            f'<enclosure url="{BASE}/audio/{ep["id"]}.mp3" length="{size}" type="audio/mpeg"/>'
            f"<itunes:duration>{E(ep['duration'])}</itunes:duration></item>"
        )
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"><channel>\n'
        "    <title>AI Radio from AI Implementation</title>\n"
        f"    <link>{BASE}/ai-radio.html</link>\n"
        "    <description>A short weekly AI-generated audio program on AI governance, insurance coverage, and decision ownership.</description>\n"
        "    <language>en-us</language>\n"
        "    <itunes:author>Ken Leatherman</itunes:author>\n"
        f'    <itunes:image href="{BASE}/images/radio-{eps[0]["id"]}.jpg"/>\n'
        + "\n".join(items)
        + "\n</channel></rss>\n"
    )
    (ROOT / "radio.xml").write_text(feed, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp3", required=True)
    ap.add_argument("--notes", required=True)
    ap.add_argument("--cover", required=True)
    a = ap.parse_args()

    notes = json.loads(Path(a.notes).read_text(encoding="utf-8"))
    title = notes["show_title"].strip()
    date = notes["date_of_generation"]
    ep = {
        "id": f"{date}-{slugify(title)}",
        "title": title,
        "date": date,
        "duration": notes["show_duration"],
        "summary": notes["two_sentence_summary"].strip(),
    }

    (ROOT / "audio").mkdir(exist_ok=True)
    (ROOT / "images").mkdir(exist_ok=True)
    (ROOT / "radio").mkdir(exist_ok=True)
    shutil.copyfile(a.mp3, ROOT / "audio" / f"{ep['id']}.mp3")

    from PIL import Image
    im = Image.open(a.cover).convert("RGB")
    im.thumbnail((800, 800))
    im.save(ROOT / "images" / f"radio-{ep['id']}.jpg", "JPEG", quality=85, optimize=True)

    (ROOT / "radio" / f"{ep['id']}.html").write_text(episode_page(ep, notes), encoding="utf-8")

    eps = json.loads(EPISODES.read_text()) if EPISODES.exists() else []
    eps = [e for e in eps if e["id"] != ep["id"]] + [ep]
    eps.sort(key=lambda e: e["date"], reverse=True)
    EPISODES.write_text(json.dumps(eps, indent=2) + "\n", encoding="utf-8")

    (ROOT / "ai-radio.html").write_text(archive_page(eps), encoding="utf-8")
    write_feed(eps)
    update_home(eps[0])
    print("published", ep["id"], f"({len(eps)} episode(s))")


if __name__ == "__main__":
    main()
