# Lexicon - TODO

Deferred / open items. Lexicon is a single self-contained file: `lexicon/index.html`
in the `charlie-tren.github.io` repo, served live at https://charlie-tren.github.io/lexicon/.
Tests: `node lexicon/test.js` (loads the real script headless; 33 checks incl. a scheduler fuzz).

**Single source of truth:** this repo only. The old private `charlie-tren/lexicon` repo was
archived on consolidation (2026-06-03) after it drifted 46 words behind the live site - do
not resurrect it as a second copy.

| # | Item | Input | Notes |
|---|------|-------|-------|
| 1 | **Persistence: move progress off localStorage (Supabase)** | Charlie | The one real architectural gap. See "Persistence plan" below - design is settled, just needs a free account + ~1h build. |
| 2 | Real-browser verification of the review flow | Charlie | Node tests pass (33/0) but the in-app browser preview timed out every attempt - the bidirectional typed review, inferred Got it/Missed grading, learning-step previews and daily auto-backup have **not** been driven in a live browser. Do one real run. |
| 3 | Decide on `asset` | Charlie | Held back from a word batch as a probable mis-transcription (oddly common vs the rest). Add it (and in which sense) or drop. |
| 4 | Pre-commit hook running the test suite | Auto | Optional: block a commit if `node lexicon/test.js` fails. Low effort. |
| 5 | Auto-push after each word-add | Charlie | Push is currently on explicit request. Could push automatically after each add (outward action - left to Charlie's standing call). |

## Where progress lives today (and how it can be lost)

The **word list** is safe - it lives in `index.html`, so git + GitHub + OneDrive all cover it.

**Review progress is not in the file.** It lives in the browser's `localStorage` for the
`charlie-tren.github.io` origin. That means:

- Survives: reloads, closing the tab, quitting the browser, rebooting, and site updates.
- Lost on: clearing browsing data / "cookies and other site data"; Chrome set to clear on
  exit; clearing data for that site; incognito windows closing; browser reinstall or
  profile reset; a different browser, profile or device.
- Per-device: each device keeps a **separate deck**, because localStorage does not travel.

Mitigations already in place:
- `navigator.storage.persist()` is requested on load, asking the browser to keep the deck
  out of its storage-eviction pool (Chrome grants silently; guarded no-op elsewhere).
- Settings -> **Automatic backup** downloads `lexicon-backup-YYYY-MM-DD.json` (deck +
  progress) once a day on the first review, plus a **Back up now** button.

Why that is still only a floor: it fires only on days you review, is up to 24h stale, lands
in **Downloads** (so it is only as offsite as that folder is synced), and does nothing for
cross-device use.

## Persistence plan (item #1) - design settled

Chosen approach: **Supabase**, because it collapses backup + cross-device + staleness into
one solution. Continuous, offsite, no files to manage, one deck on every device.

Design decisions:
- **Auth: Supabase Auth magic-link email**, with row-level security tying the deck to the
  user id. Required because the site is **public** and therefore cannot hold a secret - an
  open anon key would let anyone read or write the deck.
- **Keep localStorage as the offline cache/fallback** so the app still works with no
  connection (the zero-dependency, works-offline property is a house constraint).
- **Keep Export/Import intact** - they remain the migration and belt-and-braces path.
- Strictly additive: no change to FSRS scheduling, the card schema, or the review flow.

Alternatives considered and rejected:
- **File System Access API** (silent auto-save into a synced OneDrive folder): solves backup
  but is Chrome-only, needs frequent permission re-grants, and gives no cross-device sync.
- **Committing progress to git from the browser**: needs a write token embedded in a public
  page. Non-starter.
- **Chrome profile sync**: does not cover `localStorage`.
