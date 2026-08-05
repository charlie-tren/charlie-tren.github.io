# Hub - TODO

Deferred work for the personal hub (charlie-tren.github.io). None blocking - the site is live.

- [x] ~~**Custom domain**~~ - DONE 04/08/2026. **charlietrenorden.com**, registered at
      Cloudflare Registrar (US$10.46/yr, at-cost, renews at the same price). Live and
      verified: apex + `www` + HTTPS enforced, cert issued, `/lexicon` serving.
      GOTCHA for next time: the `CNAME` file alone did NOT take - GitHub never built that
      commit and Pages sat with `cname: null` and no certificate. Fixed with
      `gh api -X PUT repos/<owner>/<repo>/pages -f cname=<domain>`, then a second PUT with
      `-F https_enforced=true`. Cloudflare DNS records must stay **grey cloud / DNS only**;
      proxying them breaks GitHub's certificate, and the dashboard nags to enable it.
      Also updated: `og:url`/`og:image`, Lexicon's toolbar link + its test, README, and the
      hub links inside dcf-studio (commit 1fff26b there).
- [x] ~~**Short URLs for every project**~~ - DONE 04/08/2026, commit afa63ed.
      `charlietrenorden.com/<slug>` resolves for crowdwise, dcf-studio, one-story,
      the-aftertimes, thinkerings, chronoscape; `/lexicon` was already genuinely hosted.
      All but Lexicon are static redirect pages, because GitHub Pages serves only this
      repo at the apex - a real subpath would need a Cloudflare proxy, which breaks the
      cert. NOT done deliberately: the cards in `index.html` still link straight to each
      destination rather than via `/<slug>`, to avoid an extra hop on the primary
      navigation. Flip them if you'd rather every click go through the hub domain.
- [x] ~~**Subdomains for every project**~~ - DONE 04/08/2026. `crowdwise.` and `dcf.`
      (Vercel), `one-story.` and `aftertimes.` (GitHub Pages) all live with certs, and the
      hub cards + short-URL redirects now route through them. Chronoscape and Thinkerings
      stay redirect-only: Streamlit Community Cloud has no documented custom-domain
      support and Substack charges US$50.
      GOTCHAS: (1) Vercel's CLI recommends `A 76.76.21.21` for a subdomain but their docs
      say subdomains want a CNAME - the A record routes traffic fine, yet the certificate
      never provisioned on its own. `vercel certs issue <host>` fixed it in seconds; don't
      wait it out. (2) The Vercel dashboard is unreachable behind a 2FA setup interstitial,
      so the per-project CNAME value can't be read - use the CLI. (3) Setting a custom
      domain on a Pages repo makes the old `.github.io` redirect IMMEDIATELY, so DNS must
      exist first or a live site goes dark.
- [ ] **Regenerate One Story's `index.html`** - `render.py` now emits the new og:url /
      og:image, but the committed `index.html` keeps the old ones until the daily 20:00 UTC
      cron rebuilds. Self-resolving; just don't be surprised by the diff.
- [x] ~~**Lexicon lives in two places**~~ - CLOSED 04/08/2026, already resolved. The
      private `charlie-tren/lexicon` repo was ALREADY archived before this was raised;
      `gh repo archive` reported it as a no-op. The hub copy at `/lexicon` is canonical
      and is the one being served (and is ahead: index.html 83,884 vs 83,748, test.js
      7,479 vs 6,894). Nothing to do.
      Why it was raised at all: the `gh repo list` I audited with silently fell back to a
      query WITHOUT `isArchived`, so archived repos looked live. Ask for the field.
- [ ] **Bump Chronoscape pill** from "In progress" to "Live" once it covers more than
      Iceland + Taiwan.
- [x] ~~**Favicon**~~ - done: "aperture" mark (slate broken ring + centre dot), inline SVG.
- [ ] **Refresh screenshots** in `assets/` as the linked sites change (Crowdwise,
      Chronoscape, Lexicon, One Story). Re-shoot via chrome-devtools `take_screenshot`
      at ~1280 wide (aspect <1.6 so the 16:10 card crops from the top), filePath into the
      workspace root, then move.
- [ ] **Essays & books section** (asked 30/07/2026, scope settled 04/08/2026). A section
      where Charlie writes short reviews of what he's reading at the moment - essays and
      books by other people, with his own take on each. This resolves the earlier open
      question: it's a curated reading list with commentary, NOT a pick of his own
      Thinkerings posts.
      Shape: title + author + source link + Charlie's review. Sits below Projects,
      text-only like the also-built entries so it doesn't compete with the screenshot
      cards. Decide before building: (a) does it show a "currently reading" state as well
      as finished items, and (b) is the copy hand-edited in `index.html` or split into a
      small data file / separate page once it grows past ~10 entries? Start inline in
      `index.html`; only split it out when the list gets long.
- [x] ~~**T8**~~ - CLOSED 30/07/2026, out of scope. Earlier note said "not found on disk";
      that was wrong - it exists, but it's internal Rochford client work rather than a
      personal project, so it isn't hub material. No further action.
- [ ] **Optional:** a dedicated OG social-share image (currently `og:image` reuses the
      One Story screenshot).

## New project ideas (added 05/08/2026)

Three new builds for the hub, all aimed at the same gap: every project that demonstrates
long/short equity judgement currently sits in the text-only "personal project" block, so
it is unclickable and unverifiable to a visitor. These are the clickable versions.
Priority order as listed.

- [ ] **Short Book** - the missing half of the public work. Everything on the site today
      is constructive; nothing shows the other side of the trade. A page surfacing names
      that screen for deteriorating quality:
      - Accruals diverging from cash flow
      - Receivables / inventory growing faster than revenue
      - Rising share count against falling ROIC
      - Capitalised-cost creep
      - Margin peak coinciding with multiple peak

      Each name gets a card stating the specific flag that fired, plus a chart, framed
      explicitly as "this is a flag, not a thesis". Novel because near enough every
      retail-facing screener is long-only. Reuses Parallax's screener plumbing and
      Lighthouse's kill-chain framing. Highest-signal artefact on this list for a
      multi-manager pod interview.

- [ ] **Consensus Drift** - track sell-side estimate movement over time and plot the
      REVISION PATH, not the level. Revisions trend; the interesting picture is where
      price has moved and estimates have not, or the reverse. Core visual is a scatter of
      3-month price change against 3-month FY2 EPS revision with the four quadrants
      labelled, refreshed weekly.
      BLOCKER TO SOLVE FIRST: data. Bloomberg is work-licensed and cannot feed a public
      site. Either find a free estimates source or hand-maintain a narrow universe of
      ~40 names. Decide this before writing any code - it determines whether the project
      is viable at all.

- [ ] **Thesis Ledger** - a public, timestamped decision journal. Post a thesis with the
      falsifier stated UP FRONT ("wrong if gross margin has not recovered above X by
      Q3"), then the page marks each one resolved / broken / pending against price and
      the stated trigger, and shows a running hit-rate and calibration curve.
      Genuinely novel: plenty of people publish calls, nobody publishes their own
      scorecard with the invalidation written before the outcome. It is Lighthouse's
      journal made public and stripped back to one table.
      Note the real cost: this publishes the misses too. That is the point, and it is
      also the reason to be sure before starting.

- [ ] **Promote Lighthouse and Parallax out of the text-only block.** Structural, and
      arguably higher return than any new project above. The five most substantial things
      built are currently the only ones a visitor cannot see. A read-only demo on
      synthetic or lagged data would do it; a static walkthrough page with real
      screenshots would do it more cheaply.
- [ ] **Lexicon** source is now public in this repo (`/lexicon`). If it ever gains an API
      call, key, or a personal default deck, rework how it's hosted before pushing.
