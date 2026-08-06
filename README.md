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
| Thinkerings | Live | https://thinkerings.substack.com/ |
| Lexicon | Live | https://charlietrenorden.com/lexicon/ (self-hosted in this repo, `/lexicon`) |
| Chronoscape | In progress | https://chronoscape.streamlit.app/ |
| Beyond Small Talk | Live | https://charlietrenorden.com/beyond-small-talk/ (self-hosted in this repo, `/beyond-small-talk`) |

`Beyond Small Talk` is a single-file random-question page - one question at a time, click or
tap for another. It draws from a shuffle bag over 56 questions, so every question shows once
before any repeats, and a fresh bag never opens on the question just shown. Add or remove
entries in the `QUESTIONS` array in `beyond-small-talk/index.html`; nothing else needs
touching. A few questions come from Aron et al. (1997), credited and linked in the footer.

Four gotchas if you edit it.

1. The question sits inside a `<button>`, which inherits neither `font` nor `color` from
   `body`. Both are set explicitly on `.stage` - don't drop them, or the question renders
   in the browser's default button font.
2. `.qwrap` has a fixed `min-height` (225px desktop, 175px mobile) so the eyebrow and the
   hint don't shift when question length changes. If you add a question longer than the
   current longest, re-check it still fits - the tightest margin is 18px at 900px wide.
3. Font size steps by question length via the `len-s`/`len-m`/`len-l`/`len-xl` classes,
   assigned in `bucket()`. The thresholds and the CSS must stay in sync.
4. To re-shoot `assets/beyond-small-talk.png`: copy `index.html` to a temp `_shot.html`,
   inject a style pinning `html/body` to exactly 1280x800 plus a script forcing dark theme
   and one fixed question, then run headless Edge and delete the temp file:

   ```
   msedge.exe --headless=new --disable-gpu --hide-scrollbars \
     --force-device-scale-factor=1.5 --screenshot="assets/beyond-small-talk.png" \
     --window-size=860,538 "http://127.0.0.1:8899/beyond-small-talk/_shot.html"
   ```

   Pinning the box is necessary because the browser window won't give a viewport taller
   than 667. Do it this way rather than via devtools screenshots - those produced a frame
   with the top bar duplicated and the footer missing, then hung outright.

   Shoot at 860x538, NOT at 1280x800. The page is mostly deliberate empty space, so a
   wide shot shrinks to an empty rectangle in a 320px card. The narrower frame keeps the
   16:10 ratio while making the type fill it. Use a question that wraps to three lines
   for the same reason - a one-liner leaves a hole where `.qwrap` reserves its height.

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
| `/thinkerings` | https://thinkerings.substack.com/ |
| `/chronoscape` | https://chronoscape.streamlit.app/ |
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
