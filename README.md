# charlie-tren.github.io

Personal hub - a single landing page linking to my projects, built to attach to LinkedIn.

- Static one-pager, no build step. Just `index.html` + `assets/`.
- Dark editorial theme (slate accent), follows the viewer's OS light/dark preference with a manual toggle.
- Hosted on GitHub Pages at https://charlietrenorden.com/ (custom domain, registered 04/08/2026;
  the old https://charlie-tren.github.io/ still redirects there).

## Projects linked

| Project | Status | Link |
|---|---|---|
| One Story | Live | https://one-story.charlietrenorden.com/ |
| Crowdwise | Live | https://crowdwise.charlietrenorden.com/ |
| Lexicon | Live | https://charlietrenorden.com/lexicon/ (self-hosted in this repo, `/lexicon`) |
| Chronoscape | In progress | https://chronoscape.streamlit.app/ |

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
