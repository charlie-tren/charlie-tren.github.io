# charlietrenorden.com

The live site. **Pushing to `main` PUBLISHES immediately** - there is no staging
step and no build, so anything committed here is what the world sees within a
minute or two.

## Skills that apply here

**`personal-site-style` covers every directory in this repo**, by path rather
than by name: if it is a folder here, the skill applies to it, including
whatever is added next. Invoke it before building, restyling, writing copy for,
or deploying anything, and again when Charlie gives feedback on any of it so the
rule gets written into the skill rather than re-learned next time.

Also **`design-decisions`** before any round of marks, palettes, layouts or
names, and again when he chooses.

## Most directories here are DEPLOY TARGETS, not sources

Several projects are built in their own repo and copied in. Pendulum is the
clearest case: `pendulum/`, `inequality/` and `polarisation/` are all built from
`charlie-tren/pendulum` under `site/`, and `style.css` is one source copied into
all three. Editing a deploy target directly means the next deploy silently
reverts it.

Check for a source repo before editing a directory here. If one exists, make the
change there and deploy.

## Other sessions push to this repo constantly

Fetch before reading anything you intend to quote, and rebase rather than force
when a push is rejected.
