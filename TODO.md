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
- [ ] **Chronoscape sleeps on Streamlit Community Cloud** (found 06/08/2026). The app had
      idled out - visitors clicking the card get Streamlit's "Zzzz - this app has gone to
      sleep... Would you like to wake it back up?" screen, not the app. It wakes on a click,
      but that is a poor landing from a portfolio page. NOTE: my earlier link check passed it
      because it returned HTTP 303, which I read as a normal redirect - status codes do not
      prove a page is healthy, only fetching the body does.
      Options: (a) accept it, (b) a weekly GitHub Actions cron in the `chronoscape` repo that
      curls the URL to keep it warm - that repo is PUBLIC so Actions minutes are free, (c)
      move it off Streamlit Community Cloud. Charlie's call - (b) is a standing automation.
- [ ] **Bump Chronoscape pill** from "In progress" to "Live" once it covers more than
      Iceland + Taiwan.
- [x] ~~**Favicon**~~ - done: "aperture" mark (slate broken ring + centre dot), inline SVG.
- [ ] **Refresh screenshots** in `assets/` as the linked sites change. Shoot at 16:10 (the
      card ratio) so nothing crops. Use headless Edge, NOT chrome-devtools `take_screenshot`
      (see the 05/08/2026 correction; the devtools route produced a duplicated top bar, a
      wrong-aspect viewport capture, then hung).
      DONE 06/08/2026 for crowdwise, dcf-studio, one-story, the-aftertimes and lexicon -
      all now exactly 1280x800. Command used:
      `msedge.exe --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1
      --virtual-time-budget=12000 --screenshot=<out> --window-size=1280,800 <url>`
      **`--virtual-time-budget` matters** - without it Crowdwise captured before its charts
      rendered and the lower third came out empty.
      STILL 1.465/1.488 and therefore cropped: `thinkerings.png`, `chronoscape.png`. Both
      re-shot and both rejected on inspection - Substack threw its subscribe modal over the
      page, and Chronoscape was asleep (see below). Re-shoot when those two are shootable.
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
- [x] ~~**Optional:** a dedicated OG social-share image~~ - DONE, already shipped in
      commits #1 and #2 (`assets/og-card.png`, rendered natively at 2x). Verified
      05/08/2026: the file exists and `index.html` points `og:image` at it. The item was
      just never ticked, and its parenthetical "currently reuses the One Story screenshot"
      had been wrong for two commits.
- [x] ~~**Beyond Small Talk**~~ - DONE 05/08/2026, commits 0ddb96c + 3654d4a. A
      random-question page at `/beyond-small-talk`, genuinely hosted here like `/lexicon`,
      with a card in Projects. 56 questions over a shuffle bag. Named by Charlie after
      "Fathom" was rejected; see the README for the two layout gotchas and the re-shoot
      command.

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
      INTEGRATE WITH LIGHTHOUSE rather than building a second store. Lighthouse already
      holds the theses, the falsifiers and the outcomes in its journal, so the ledger
      should be a published VIEW of that, not a parallel one - a thesis gets written once,
      in Lighthouse, and the page renders whatever is flagged public. Anything else means
      double entry, and double entry means the public copy quietly drifts from the real
      one, which destroys the whole point of a scorecard.
      Decide when building: (a) what marks an entry public - a column in the journal, or
      an explicit export step; (b) how it publishes, given the journal is a gitignored
      SQLite DB and this site is static, so it needs an export to JSON committed here
      rather than a live DB read; (c) what stays private - position sizes and P&L almost
      certainly, since the hit-rate and the calibration curve are the point, not the book.

- [ ] **Promote Lighthouse and Parallax out of the text-only block.** Structural, and
      arguably higher return than any new project above. The five most substantial things
      built are currently the only ones a visitor cannot see. A read-only demo on
      synthetic or lagged data would do it; a static walkthrough page with real
      screenshots would do it more cheaply.
- [ ] **Lexicon** source is now public in this repo (`/lexicon`). If it ever gains an API
      call, key, or a personal default deck, rework how it's hosted before pushing.

## Non-finance project ideas (added 05/08/2026)

The site is a personal site, not a finance portfolio. These fit the quiet single-purpose
register of Lexicon / Beyond Small Talk / One Story rather than the markets work.

- [ ] **Loop** - give it a start point and a distance, and it generates a running or
      walking route that is a genuine LOOP of that length, not an out-and-back.
      Real gap: most route tools make you draw the route yourself, and the ones that
      auto-generate tend to produce a there-and-back-again.
      - Input: a dropped pin (or geolocation) plus a target distance
      - Output: a closed circuit within a tolerance of that distance, drawn on a map
      - Nice-to-haves once v1 works: prefer parks and paths over arterial roads, avoid
        repeating the same street, an elevation profile, and a GPX export
      Data is OpenStreetMap. The interesting part is the routing problem - finding a
      closed circuit of a target length is not a shortest-path problem, so expect to
      generate candidate loops and score them rather than solve it directly.

- [ ] **Telephone** - paste a passage, watch it degrade as it is translated through a
      chain of languages and back to English, with the text shown at every hop so the
      drift is visible as it happens.
      A toy, and deliberately so. Should be an afternoon, not a project.
      - Show each intermediate language and its output, not just the final mangled text
      - Let the user set the number of hops
      - Some measure of how far it has drifted from the original would make it land
      Decide the translation source before starting - this is the only real dependency,
      and a free/keyless one keeps it hostable alongside everything else.

- [ ] **Oldest Near You** - drop a pin, get everything around you ranked by age. The
      oldest building, wall, tree, road, pub. Natural sibling to Chronoscape.
      Checked 05/08/2026: per-city building-age maps exist and OSM's `start_date` powers
      them, but no "rank what is near me by age" tool turned up. The idea survives.
      DO THIS FIRST, before any code: probe how much `start_date` / `building:age` data
      OSM actually holds for Sydney. Coverage is known to be thin outside a handful of
      well-mapped cities (the Netherlands, Lviv). If Sydney is sparse, the project dies
      there and that is fine - better to find out in an Overpass query than after a
      week's work.
      Shape once the data checks out:
      - Overpass query in a radius around the pin, filtered to anything carrying a date
      - Ranked list, oldest first, each entry with what it is and how it is dated
      - Show the dating confidence - "1857" and "19th century" are not the same claim
      - Map alongside the list, since the spatial pattern is half the interest
