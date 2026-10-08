#!/usr/bin/env python3
"""Regenerate SEO files for the static site. Safe to re-run (idempotent).

Run from the repo root:  python3 scripts/seo.py

What it does
  1. Adds canonical, Open Graph, Twitter and JSON-LD tags to the <head> of every
     page that does not have them yet (new weekly posts get them automatically).
  2. Adds the Plausible analytics script to any page missing it.
  3. Adds the "free Starter Packet" signup box after the CTA box on posts that lack it.
  4. Writes sitemap.xml, feed.xml (RSS) and llms.txt from the files in the repo.
"""
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.youraigap.com"
SITE_NAME = "AI Implementation"
AUTHOR = {
    "@type": "Person",
    "name": "Ken Leatherman",
    "url": "https://kenleatherman.com",
    "sameAs": [
        "https://linkedin.com/in/kenleatherman",
        "https://kenleatherman.substack.com/",
    ],
}
PUBLISHER = {"@type": "Organization", "name": "Storify Studio", "url": "https://kenleatherman.com"}
IMAGE = BASE + "/images/og-share.png"
BOOK_URL = "https://www.amazon.com/dp/0998810371"

SECTION_LABEL = {
    "senior-housing": "Senior Housing",
    "insurance-coverage": "Insurance Coverage",
    "governance": "Governance",
}

SIGNUP_BOX = (
    '\n\n      <div class="signup-box">\n'
    "        <strong>Free: the Board-Ready AI Governance Starter Packet.</strong> "
    "Four tools from the companion workbook: board resolution, data governance policy, "
    "90-day sprint, and board briefing template. "
    '<a href="../../starter-packet.html">Get the packet &rarr;</a>\n'
    "      </div>"
)


def meta(content, pattern):
    m = re.search(pattern, content, re.S)
    return html.unescape(m.group(1).strip()) if m else ""


def page_info(path: Path):
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    title = meta(text, r"<title>(.*?)</title>")
    desc = meta(text, r'<meta name="description" content="(.*?)">')
    url = BASE + "/" + ("" if rel == "index.html" else rel)
    is_post = rel.startswith("posts/")
    date = None
    section = None
    if is_post:
        m = re.match(r"posts/([^/]+)/(\d{4}-\d{2}-\d{2})-", rel)
        section, date = m.group(1), m.group(2)
    return rel, text, title, desc, url, is_post, section, date


def jsonld(rel, title, desc, url, is_post, date):
    if is_post:
        h1 = title.split(" | ")[0]
        data = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": h1,
            "description": desc,
            "datePublished": date,
            "dateModified": date,
            "mainEntityOfPage": url,
            "author": AUTHOR,
            "publisher": PUBLISHER,
            "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": BASE + "/"},
        }
    elif rel == "index.html":
        data = {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "WebSite", "name": SITE_NAME, "url": BASE + "/", "description": desc, "publisher": PUBLISHER},
                dict(AUTHOR, **{"@context": None}),
                {
                    "@type": "Book",
                    "name": "Senior Housing: The AI Gap: From Governance Theater to Deployment in 90 Days",
                    "author": {"@type": "Person", "name": "Ken Leatherman"},
                    "url": BOOK_URL,
                },
            ],
        }
        data["@graph"][1].pop("@context")
    else:
        data = {
            "@context": "https://schema.org",
            "@type": "CollectionPage" if rel.endswith("-housing.html") or rel in ("governance.html", "insurance-coverage.html") else "WebPage",
            "name": title,
            "description": desc,
            "url": url,
            "author": AUTHOR,
            "isPartOf": {"@type": "WebSite", "name": SITE_NAME, "url": BASE + "/"},
        }
    return json.dumps(data, indent=2, ensure_ascii=False)


def head_block(rel, title, desc, url, is_post, date):
    e = html.escape
    lines = [
        f'<link rel="canonical" href="{url}">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:type" content="{"article" if is_post else "website"}">',
        f'<meta property="og:title" content="{e(title, quote=True)}">',
        f'<meta property="og:description" content="{e(desc, quote=True)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{IMAGE}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:image" content="{IMAGE}">',
        f'<meta name="twitter:title" content="{e(title, quote=True)}">',
        f'<meta name="twitter:description" content="{e(desc, quote=True)}">',
    ]
    if is_post:
        lines.append(f'<meta property="article:published_time" content="{date}">')
        lines.append('<meta name="author" content="Ken Leatherman">')
    lines.append('<link rel="alternate" type="application/rss+xml" title="AI Implementation" href="%s/feed.xml">' % BASE)
    lines.append('<script type="application/ld+json">\n' + jsonld(rel, title, desc, url, is_post, date) + "\n</script>")
    return "\n".join(lines) + "\n"


PLAUSIBLE = '<script defer data-domain="www.youraigap.com" src="https://plausible.io/js/script.tagged-events.js"></script>\n'


def fix_page(path: Path):
    rel, text, title, desc, url, is_post, section, date = page_info(path)
    changed = False
    if 'rel="canonical"' not in text:
        text = text.replace("</head>", head_block(rel, title, desc, url, is_post, date) + "</head>", 1)
        changed = True
    if is_post and 'class="signup-box"' not in text:
        new = re.sub(r'(<div class="cta-box">.*?</div>)(\s*</article>)', lambda m: m.group(1) + SIGNUP_BOX + m.group(2), text, count=1, flags=re.S)
        if new != text:
            text, changed = new, True
    if "og:image" not in text and 'rel="canonical"' in text:
        text = text.replace('<meta name="twitter:card" content="summary">',
            f'<meta property="og:image" content="{IMAGE}">\n<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:image" content="{IMAGE}">', 1)
        changed = True
    if "plausible.io" not in text:
        text = text.replace("</head>", PLAUSIBLE + "</head>", 1)
        changed = True
    if "Storify Studios" in text:
        text = text.replace("Storify Studios", "Storify Studio")
        changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def all_pages():
    return sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)


def write_sitemap(pages):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for p in pages:
        rel, _, _, _, url, is_post, _, date = page_info(p)
        pri = "1.0" if rel == "index.html" else ("0.6" if is_post else "0.8")
        out.append(f"  <url><loc>{url}</loc><lastmod>{date or today}</lastmod><priority>{pri}</priority></url>")
    out.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(out) + "\n", encoding="utf-8")


def posts_sorted(pages):
    posts = [page_info(p) for p in pages if "/posts/" in p.as_posix()]
    return sorted(posts, key=lambda t: (t[7], t[0]), reverse=True)


def write_feed(posts):
    e = html.escape
    items = []
    for rel, text, title, desc, url, _, section, date in posts[:30]:
        pub = datetime.strptime(date, "%Y-%m-%d").strftime("%a, %d %b %Y 12:00:00 +0000")
        items.append(
            f"    <item><title>{e(title.split(' | ')[0])}</title><link>{url}</link><guid>{url}</guid>"
            f"<pubDate>{pub}</pubDate><category>{SECTION_LABEL[section]}</category><description>{e(desc)}</description></item>"
        )
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>\n'
        f"    <title>{SITE_NAME}: Governance, Coverage, and Deployment</title>\n"
        f"    <link>{BASE}/</link>\n"
        "    <description>Weekly AI governance, insurance coverage, and senior housing analysis from Ken Leatherman.</description>\n"
        "    <language>en-us</language>\n" + "\n".join(items) + "\n</channel></rss>\n"
    )
    (ROOT / "feed.xml").write_text(feed, encoding="utf-8")


def write_llms(posts):
    lines = [
        "# AI Implementation (youraigap.com)",
        "",
        "> Weekly analysis of AI governance, AI insurance coverage, and AI deployment for senior housing operators, "
        "risk managers, and general business leaders. Written by Ken Leatherman, author of Senior Housing: The AI Gap. "
        "Built from his books, the LITT Briefing, and The Second Ledger method.",
        "",
        "## Sections",
        f"- [Senior Housing]({BASE}/senior-housing.html): AI governance committees, accreditation (CARF), prior authorization, resident-safety and staffing issues",
        f"- [Insurance Coverage]({BASE}/insurance-coverage.html): AI exclusion endorsements, silent AI exposure, underwriting, and a coverage self-check",
        f"- [Governance]({BASE}/governance.html): State AI law and board-level governance for general business",
        "",
        "## Free resource",
        f"- [Board-Ready AI Governance Starter Packet]({BASE}/starter-packet.html): board resolution, data governance policy, 90-day sprint, and board briefing templates",
        f"- [General Business AI Governance Starter Packet]({BASE}/general-business-packet.html): board resolution, AI use and data policy, 90-day sprint, and board briefing for any industry",
        "",
        "## Author and book",
        "- [Ken Leatherman](https://kenleatherman.com): author, speaker, creator of the Leadership in Tough Times (LITT) framework",
        f"- [Senior Housing: The AI Gap]({BOOK_URL}): From Governance Theater to Deployment in 90 Days",
        "- [The LITT Briefing](https://kenleatherman.substack.com/): weekly newsletter",
        "",
        "## Recent posts",
    ]
    for rel, _, title, desc, url, _, section, date in posts[:20]:
        lines.append(f"- [{title.split(' | ')[0]}]({url}) ({SECTION_LABEL[section]}, {date}): {desc}")
    lines += ["", f"Full list: {BASE}/sitemap.xml", ""]
    (ROOT / "llms.txt").write_text("\n".join(lines), encoding="utf-8")


def write_robots():
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        "# AI answer engines are welcome\n"
        "User-agent: GPTBot\nAllow: /\n"
        "User-agent: OAI-SearchBot\nAllow: /\n"
        "User-agent: ChatGPT-User\nAllow: /\n"
        "User-agent: ClaudeBot\nAllow: /\n"
        "User-agent: Claude-SearchBot\nAllow: /\n"
        "User-agent: PerplexityBot\nAllow: /\n"
        "User-agent: Google-Extended\nAllow: /\n\n"
        f"Sitemap: {BASE}/sitemap.xml\n",
        encoding="utf-8",
    )


def main():
    pages = all_pages()
    n = sum(fix_page(p) for p in pages)
    pages = all_pages()
    posts = posts_sorted(pages)
    write_sitemap(pages)
    write_feed(posts)
    write_llms(posts)
    write_robots()
    print(f"pages updated: {n} / {len(pages)}; posts: {len(posts)}")


if __name__ == "__main__":
    main()
