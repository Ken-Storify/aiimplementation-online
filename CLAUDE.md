# CLAUDE.md — aiimplementation.online

Zero-build static site (plain HTML/CSS/JS, no bundler). Deployed on Vercel,
auto-deploys on every push to `main`. Direct-to-`main` is this repo's normal
workflow — no PR required for routine post publishing.

## Weekly publish: keep the homepage in sync (IMPORTANT)

Each week's posts are published by updating the section pages **and** the
homepage. The homepage is easy to forget because older instructions only
covered the section pages — don't. A publish is not complete until all three
levels below are updated for every section that got a new post that week:

1. **New post file** — `posts/<section>/YYYY-MM-DD-slug.html`
   (`<section>` is one of `senior-housing`, `insurance-coverage`, `governance`).
   Copy an existing post as the template; relative paths are `../../`.

2. **Section page** (`senior-housing.html` / `insurance-coverage.html` /
   `governance.html`): update the **Latest** teaser block to the new post, and
   add a new newest-first `<li>` to the **Archive** list. Last week's Latest
   moves down into Archive.

3. **Homepage** (`index.html`): each of the three `.card` blocks has a
   `.card-latest` element:

   ```html
   <div class="card-latest">
     <span class="card-latest-label">Latest &middot; MONTH D, YYYY</span>
     <a href="posts/<section>/YYYY-MM-DD-slug.html">Exact Post Title</a>
   </div>
   ```

   Update the date, title, and href to match that section's new Latest post.
   These are **hardcoded** (deliberately, for SEO — there is no script that
   fills them in). If the homepage isn't updated, the section pages will show
   the new post but the front page will still show last week's — that's the
   bug this checklist exists to prevent.

   Then, below the cards, `index.html` has a **`.home-archive`** section with
   one `.archive-col` per section (the smaller "The archive" tiles). Move the
   post that was in that section's card *last* week to the **top** of its
   `.archive-col` list (newest first), same `<li>` shape as the section-page
   Archive:

   ```html
   <li><a href="posts/<section>/YYYY-MM-DD-slug.html">Prior Post Title</a><span class="archive-date">MONTH D, YYYY</span></li>
   ```

   So each week the card's outgoing Latest lands in the homepage archive tile,
   mirroring how it moves into the section page's Archive list.

4. **Run the SEO script** — `python3 scripts/seo.py` from the repo root, before
   committing. It adds canonical/Open Graph/JSON-LD tags and the Starter Packet
   signup box to any new post, and regenerates `sitemap.xml`, `feed.xml`, and
   `llms.txt`. It is idempotent, so running it every week is safe. Commit the
   regenerated files with the post.

When applying a pre-built weekly patch that only touches the section pages and
post files, update `index.html` yourself in the same commit — both the three
`.card-latest` blocks and the `.home-archive` tiles — so the homepage doesn't
fall behind.

## Verifying a homepage change

`python3 -m http.server 8000`, open `index.html`, confirm one row of three
cards, each showing the correct latest date/title linking to the right post.

## Scope discipline

Routine publishing touches only the files above. Don't edit unrelated content,
`governance.html`'s non-Latest sections, Substack, or LinkedIn unless asked.
