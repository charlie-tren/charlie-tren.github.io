# Lexicon - TODO

Deferred / open items. Lexicon is a single self-contained file: `lexicon/index.html`
in the `charlie-tren.github.io` repo, served live at https://charlie-tren.github.io/lexicon/.
Tests: `node lexicon/test.js` (loads the real script headless; 29 checks incl. a scheduler fuzz).

**Single source of truth:** this repo only. The old private `charlie-tren/lexicon` repo was
archived on consolidation (2026-06-03) after it drifted 46 words behind the live site - do
not resurrect it as a second copy.

| # | Item | Input | Notes |
|---|------|-------|-------|
| 1 | Real-browser verification of the review flow | Charlie | Node tests pass (29/0) but the in-app browser preview timed out - the bidirectional typed review, inferred Got it/Missed grading, learning-step previews and daily auto-backup have **not** been driven in a live browser. Do one real run. |
| 2 | Decide on `asset` | Charlie | Held back from a batch as a probable mis-transcription (oddly common vs the rest). Add it (and in which sense) or drop. |
| 3 | Supabase cross-device sync | Charlie | The real "automatic, hands-off, multi-device" upgrade (add on phone -> on laptop). localStorage is per-origin AND per-device, so today each device keeps a separate deck. Needs a free Supabase account; scope + propose migration before building. |
| 4 | Pre-commit hook running the test suite | Auto | Optional: block a commit if `node lexicon/test.js` fails. Low effort. |
| 5 | Auto-push after each word-add | Charlie | Push is currently on explicit request. Could push automatically after each add (outward action - left to Charlie's standing call). |

**Backup position.** The *word list* is safe: it lives in this file, so it is covered by
git + GitHub + OneDrive. *Review progress* is NOT in the file - it lives in the browser's
`localStorage` for the `charlie-tren.github.io` origin, so it is per-browser and
per-device. Settings -> Automatic backup downloads a dated JSON snapshot of deck +
progress once a day; keep it somewhere synced, or do #3 to solve it properly.
