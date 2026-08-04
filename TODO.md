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
- [ ] **LinkedIn caption for the site** - Charlie asked 30/07/2026 what to put on the
      LinkedIn media item. His draft ("Equity Research & Markets Tooling ... Lighthouse,
      Parallax and Vantage") only names the three markets tools, but the site LEADS with
      Crowdwise / One Story / Thinkerings / Lexicon / Chronoscape, so the caption
      undersells the breadth a visitor actually lands on. Two drafts were offered (a
      breadth-matching one and a markets-tilted one); he hasn't picked. Decide, then keep
      the caption and the hero in sync if either changes.
      URL to use is now **https://charlietrenorden.com** (updated 04/08/2026).
- [ ] **Optional:** a dedicated OG social-share image (currently `og:image` reuses the
      One Story screenshot).
- [ ] **Lexicon** source is now public in this repo (`/lexicon`). If it ever gains an API
      call, key, or a personal default deck, rework how it's hosted before pushing.
