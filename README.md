# aiimplementation.online

The hub site for Ken Leatherman's AI Implementation brand: senior housing, general-business
governance, and insurance coverage, one site, three sections, per the brand architecture
strategy doc (Section 4).

This is a zero-build static site. No framework, no bundler, no `npm install` required.
Every page is plain HTML/CSS/JS and works by just opening it in a browser or dropping the
folder on any static host.

## Structure

```
index.html                Hub home — three section cards
senior-housing.html       Senior housing section — Latest teaser + Archive + resource cards
governance.html           Governance section (standing up ahead of The AI Implementation Crisis)
insurance-coverage.html   Insurance coverage section — Latest teaser + Archive + "Is Your AI Covered?" quiz
styles.css                Shared design system (navy #1f2d4e / gold #b8862b, matches every
                           other Storify/Ken Leatherman deliverable)
script.js                 Mobile nav toggle + the insurance-coverage self-check quiz logic
downloads/                The free Board-Ready Starter Packet (PDF + Word), linked directly
                           from senior-housing.html, no email gate
posts/senior-housing/      One permalink page per week's senior-housing post
posts/insurance-coverage/  One permalink page per week's insurance-coverage post
```

## Running it locally

Nothing to install. Either:
- Open `index.html` directly in a browser, or
- From this folder: `python3 -m http.server 8000` and visit `http://localhost:8000`

## The weekly publishing workflow

This is how the site stays current, and it's a small, repeatable checklist, not a rebuild.

1. The LITT Briefing publishes on Substack as it always has, unchanged. That's still the
   primary weekly publication and the place people subscribe.
2. Run the split workflow (see `LITT_Briefing_Split_Workflow.docx`, delivered separately) to
   turn that edition into two posts: one senior-housing angle, one insurance-coverage angle.
3. Save each post as a new file:
   - `posts/senior-housing/YYYY-MM-DD-slug.html`
   - `posts/insurance-coverage/YYYY-MM-DD-slug.html`
   Copy an existing post file as the template, it already has the shared header, footer, and
   styling wired up correctly, relative paths and all (`../../styles.css` from two directories
   deep).
4. On the section page (`senior-housing.html` or `insurance-coverage.html`):
   - Update the **Latest** block to point at the new post (new title, new teaser paragraph,
     new links).
   - Add a new `<li>` to the **Archive** list, newest first, linking to the post you just
     added. The post that was in "Latest" last week doesn't disappear, it just moves down
     into the Archive list, this is what keeps every past edition permanently reachable.
5. Commit and push to `main`. Vercel auto-deploys on every push, live in under a minute.
6. Cross-post to LinkedIn as usual. Worth linking back to the permalink page on the site
   (`aiimplementation.online/posts/...`) rather than only posting the full text natively, so
   LinkedIn traffic actually reaches the site and its CTAs.

There's no CMS and no database here on purpose, the whole site is just files in git. That
keeps hosting free and deployment a single `git push`, at the cost of a few minutes of manual
copy-editing each week. If that stops feeling worth it once there's a real backlog of posts,
the natural upgrade is a lightweight static-site generator (11ty or Astro are the common
choices) that builds the Latest/Archive pattern automatically from the post files instead of
by hand, everything here is structured so that move wouldn't require starting over.

## Deploying with GitHub + Vercel

1. Create a new empty repo on GitHub (no README/license, this folder already has one).
2. From this folder:
   ```
   git remote add origin <your-new-repo-url>
   git branch -M main
   git push -u origin main
   ```
   (A local repo with one commit is already initialized here, so this is the whole step.)
3. In Vercel: **New Project** → **Import Git Repository** → pick this repo.
4. Framework preset: **Other** (this is a static site, no build command, no output
   directory override needed, root directory is fine as-is).
5. Deploy. Vercel will auto-redeploy on every push to `main` from then on.
6. Once you're happy with the preview URL, point `aiimplementation.online`'s DNS at Vercel
   (Vercel's project settings → Domains walks through the exact records; it'll likely be an
   A record or CNAME depending on whether you use the apex domain or a subdomain) and add the
   domain to the Vercel project.

## Known placeholders, fix before going live

- All `mailto:` links point to `ken_leatherman@ajg.com`. Confirm that's the address you want
  public before this ships.
- The governance section has no dedicated lead magnet yet, it's honestly framed as "standing
  up ahead of The AI Implementation Crisis." Revisit once that book has enough material.
- No analytics wired in (no Plausible/GA/etc.). Worth adding before launch if you want to see
  traffic by section.
- The Starter Packet download is ungated (no email capture). That was a deliberate call for
  this pass, true opt-in gating would need an email service connector wired into the download
  button, which isn't set up yet.

## What's next (from the project roadmap)

- Redirect aiseniorhousing.com, thegovernancetheater.com, and ismyaicovered.com into their
  matching sections once the domain is live on Vercel.
- Backfill past LITT Briefing editions using the split workflow documented separately
  (`LITT_Briefing_Split_Workflow.docx`).
- Build out the General Business Starter Packet and wire it into governance.html the same
  way the senior-housing packet works.
