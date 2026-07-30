# Hub - TODO

Deferred work for the personal hub (charlie-tren.github.io). None blocking - the site is live.

- [ ] **Custom domain** (the main one). Buy it, add a `CNAME` file with the bare domain,
      point DNS at GitHub Pages, then update `og:url` + `og:image` host in `index.html`
      from `charlie-tren.github.io` to the new domain.
- [ ] **Bump Chronoscape pill** from "In progress" to "Live" once it covers more than
      Iceland + Taiwan.
- [x] ~~**Favicon**~~ - done: "aperture" mark (slate broken ring + centre dot), inline SVG.
- [ ] **Refresh screenshots** in `assets/` as the linked sites change (Crowdwise,
      Chronoscape, Lexicon, One Story). Re-shoot via chrome-devtools `take_screenshot`
      at ~1280 wide (aspect <1.6 so the 16:10 card crops from the top), filePath into the
      workspace root, then move.
- [ ] **Favourite essays section** (asked for 30/07/2026). Add a section to the hub
      showing Charlie's favourite essays. OPEN QUESTION to settle first: is this a
      curated reading list of essays by OTHER people (a "things worth reading" list), or
      a pick of his own best Thinkerings posts? The wording ("my favourite essays") reads
      more like the former. Either way it wants title + author + source link + a one-line
      note on why, and should sit below Projects; keep it text-only like the also-built
      entries so it doesn't compete with the screenshot cards.
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
