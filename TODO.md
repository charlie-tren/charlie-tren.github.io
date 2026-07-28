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
- [ ] **T8** - Charlie mentioned a "T8 analysis" to potentially feature but never said what
      it is; not found on disk. Awaiting his clarification before it can be added.
- [ ] **Optional:** a dedicated OG social-share image (currently `og:image` reuses the
      One Story screenshot).
- [ ] **Lexicon** source is now public in this repo (`/lexicon`). If it ever gains an API
      call, key, or a personal default deck, rework how it's hosted before pushing.
