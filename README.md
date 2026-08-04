# charlie-tren.github.io

Personal hub - a single landing page linking to my projects, built to attach to LinkedIn.

- Static one-pager, no build step. Just `index.html` + `assets/`.
- Dark editorial theme (slate accent), follows the viewer's OS light/dark preference with a manual toggle.
- Hosted on GitHub Pages at https://charlietrenorden.com/ (custom domain, registered 04/08/2026;
  the old https://charlie-tren.github.io/ still redirects there).

## Projects linked

| Project | Status | Link |
|---|---|---|
| One Story | Live | https://the-one-story.github.io/ |
| Crowdwise | Live | https://crowdwise-live.vercel.app |
| Lexicon | Live | https://charlietrenorden.com/lexicon/ (self-hosted in this repo, `/lexicon`) |
| Chronoscape | In progress | https://chronoscape.streamlit.app/ |

## Short URLs

Every project has a shareable path on the hub domain. All but `/lexicon` are static
redirect pages (`<slug>/index.html`: canonical + meta-refresh + `location.replace`) -
GitHub Pages can only host one repo, so a real subpath isn't possible for the others.

| Path | Goes to |
|---|---|
| `/crowdwise` | https://crowdwise-live.vercel.app/ |
| `/dcf-studio` | https://dcf-studio.vercel.app/ |
| `/one-story` | https://the-one-story.github.io/ |
| `/the-aftertimes` | https://the-aftertimes.github.io/ |
| `/thinkerings` | https://thinkerings.substack.com/ |
| `/chronoscape` | https://chronoscape.streamlit.app/ |
| `/lexicon` | served here for real, not a redirect |

If a target's URL changes, edit the slug's `index.html` - the URL appears three times
in it (canonical, meta-refresh, script).

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
