# Hub - TODO

Deferred work for the personal hub (charlie-tren.github.io). None blocking - the site is live.

- [ ] **Custom domain** - decided 04/08/2026: **charlietrenorden.com**, bought at
      Cloudflare Registrar (at-cost, ~US$10.44/yr, no renewal markup). Verified available
      via Verisign RDAP on 04/08/2026. Once registered: add a `CNAME` file containing the
      bare domain, point DNS at GitHub Pages (four A records for the apex + a `www`
      CNAME), enable Enforce HTTPS in the repo's Pages settings, then update `og:url` +
      `og:image` host in `index.html` from `charlie-tren.github.io` to the new domain.
      Later, optionally give the Vercel projects subdomains (`dcf.`, `crowdwise.`).
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
- [ ] **Optional:** a dedicated OG social-share image (currently `og:image` reuses the
      One Story screenshot).
- [ ] **Lexicon** source is now public in this repo (`/lexicon`). If it ever gains an API
      call, key, or a personal default deck, rework how it's hosted before pushing.
