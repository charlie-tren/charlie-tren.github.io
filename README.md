# charlie-tren.github.io

Personal hub - a single landing page linking to my projects, built to attach to LinkedIn.

- Static one-pager, no build step. Just `index.html` + `assets/`.
- Dark editorial theme (slate accent), follows the viewer's OS light/dark preference with a manual toggle.
- Hosted on GitHub Pages at https://charlietrenorden.com/ (custom domain, registered 04/08/2026;
  the old https://charlie-tren.github.io/ still redirects there).

## Projects linked

| Project | Status | Link |
|---|---|---|
| Crowdwise | Live | https://crowdwise.charlietrenorden.com/ |
| DCF Studio | Live | https://dcf.charlietrenorden.com/ |
| One Story | Live | https://one-story.charlietrenorden.com/ |
| The Aftertimes | Live | https://aftertimes.charlietrenorden.com/ |
| Photocopy | Live | https://charlietrenorden.com/photocopy/ (project Pages under this account, genuinely served at this path - do NOT add a `/photocopy` redirect folder here or it collides) |
| Thinkerings | Live | https://thinkerings.substack.com/ |
| Lexicon | Live | https://charlietrenorden.com/lexicon/ (self-hosted in this repo, `/lexicon`) |
| Chronoscape | In progress | https://chronoscape.charlietrenorden.com/ |
| Beyond Small Talk | Live | https://charlietrenorden.com/beyond-small-talk/ (self-hosted in this repo, `/beyond-small-talk`) |

| Split the Room | Live | https://charlietrenorden.com/split-the-room/ (self-hosted in this repo, `/split-the-room`) |

### Beyond Small Talk and Split the Room

**Two pages, one shell.** Both show one line at a time and swap it on click or tap:
`/beyond-small-talk` is questions, `/split-the-room` is agree-or-disagree statements. Each
draws from its own shuffle bag, so every line shows once before any repeats and a fresh bag
never opens on the line just shown. A few of the questions come from Aron et al. (1997),
credited and linked in that page's footer; the statements are Charlie's.

They are **deliberately two real pages rather than one page with tabs**, so each mode has
its own URL, its own title and its own link preview, and the back button works. The tabs are
plain `<a>` links between them. Because the URL is the state, there is no stored "last tab" -
that would be actively wrong, since the hub card points at `/beyond-small-talk/` and should
always open questions.

The shared shell lives in `assets/room.css` and `assets/room.js`; each page supplies only its
own content via `window.ROOM = { items: [...] }` before loading the script. **Add or remove
lines in that array - nothing else needs touching.** The shell was extracted rather than
copied precisely because two near-identical inline copies would drift the first time one was
edited.

Five gotchas if you edit them.

1. The line sits inside a `<button>`, which inherits neither `font` nor `color` from
   `body`. Both are set explicitly on `.stage` - don't drop them, or it renders in the
   browser's default button font.
2. `.qwrap` has a fixed `min-height` (225px desktop, 175px mobile) so the tabs and the
   hint don't shift when line length changes. If you add a line longer than the current
   longest, re-check it still fits - the tightest margin is 18px at 900px wide.
3. Font size steps by length via the `len-s`/`len-m`/`len-l`/`len-xl` classes, assigned in
   `bucket()` in `room.js`. The thresholds there and the CSS must stay in sync.
4. **The tabs must stay outside `.stage`.** `.stage` is a `<button>`; a link inside a button
   is invalid HTML, and clicking a tab would also fire the next-line handler.
5. Card thumbnails are now produced by `tools/shoot_thumbnails.py`, which pins the question
   via `#q` and `.q.len-s` (see its `PREPARE` map) so the card never draws a random line.
   Keep that id and those classes. **Use the script - do not re-shoot by hand.** This
   section used to give a `msedge --headless=new --screenshot` command; that no longer
   works. Retested 08/08/2026: Edge writes no file at all and reports no error, which is
   the worst possible failure because a stale PNG stays in place and the shot looks done.
   The devtools screenshot tool is not a fallback either - it produced a frame with the
   top bar duplicated and the footer missing, then hung.

   Two framing rules the script encodes, worth keeping if it is ever rewritten. **Shoot at
   860x538, not 1280x800.** Same 16:10 ratio, but the page is mostly deliberate empty
   space, so a wide shot shrinks to an empty rectangle in a 320px card. And **pin a
   question that wraps to three lines** - a one-liner leaves a visible hole where
   `.qwrap` reserves its fixed height.

## Notes and roadmap

Open items and project ideas live in the **private** repo `charlie-tren/hub-notes`,
not here - this repo is public, and a roadmap in a public repo is a published roadmap.
Moved 06/08/2026.

## Short URLs

Every project has a shareable path on the hub domain. All but `/lexicon` are static
redirect pages (`<slug>/index.html`: canonical + meta-refresh + `location.replace`) -
GitHub Pages can only host one repo, so a real subpath isn't possible for the others.

| Path | Goes to |
|---|---|
| `/crowdwise` | https://crowdwise.charlietrenorden.com/ |
| `/dcf-studio` | https://dcf.charlietrenorden.com/ |
| `/one-story` | https://one-story.charlietrenorden.com/ |
| `/the-aftertimes` | https://aftertimes.charlietrenorden.com/ |
| `/photocopy` | not a redirect - GitHub serves the `charlie-tren/photocopy` repo at this path |
| `/thinkerings` | https://thinkerings.substack.com/ |
| `/chronoscape` | https://chronoscape.charlietrenorden.com/ |
| `/lexicon` | served here for real, not a redirect |

If a target's URL changes, edit the slug's `index.html` - the URL appears three times
in it four times (canonical, meta-refresh, the visible link, and the script).

Subdomains (added 04/08/2026): crowdwise / dcf -> Vercel via `A 76.76.21.21`;
one-story / aftertimes -> GitHub Pages via CNAME. Vercel needed
`vercel certs issue <host>` - the cert did not provision on its own.

## "Also built" (overview only, no links)

Compact, non-clickable entries - internal tools and personal projects that aren't public.
Copy is deliberately capability-only: no client names, exposures, numbers, or internal
methodology. The three internal ones (Vantage, Overlay & hedging ops, Signal pipelines)
have Rochford sign-off for this wording; keep any future edits to that same generic level.

| Entry | Tag |
|---|---|
| Parallax | Personal project |
| All-Weather | Personal project |
| Vantage | Internal tool |
| Overlay & hedging ops | Internal tool |
| Signal pipelines | Internal tool |

## Updating

Edit `index.html`, commit, push. Project card thumbnails live in `assets/` - swap the PNGs to refresh a screenshot.

## Custom domain (later)

Add a `CNAME` file containing the bare domain, point the domain's DNS at GitHub Pages, and set it under Settings → Pages.
