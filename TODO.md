# charlietrenorden.com, open items

Site-level work on the hub itself. Anything about a project belongs in that
project's own repo, since most directories here are deploy targets.

- [ ] **Point the Position Record trigger alert at an inbox that is read.**
  **07/10/2026: nothing to alert on for now.** Brent/WTI and Mastercard/Visa came
  off Watching after failing their re-tests, and the one row left (WTI/Diesel) is
  event-triggered, which `alert.py` skips (line 58). This only matters again when
  a priced watch goes back on the page.
  **Charlie-only.** `position-record/alert.py` opens a GitHub issue assigned to
  `charlie-tren` when a watched pair crosses its trigger, and GitHub emails the
  assignee. That account's notification address is [second Gmail account],
  so a trigger fires into an inbox he does not read. charlie.tren@gmail.com cannot
  be added: GitHub answers "email is already in use", because the dormant
  `charlietren` account holds it. The fix is about two minutes, all on his side:
  sign into `charlietren` (GitHub's account switcher keeps `charlie-tren` signed
  in), remove the address there, add and verify it on `charlie-tren`, and set it
  as the default under Settings, Notifications. A session can then re-fire the
  test with `gh workflow run "Refresh position record" -f alert_test=true` and
  confirm the mail lands. Left mid-flow 23/09/2026; nothing has fired since.

- [ ] **Finish removing the old email addresses from GitHub.** **Charlie-only**, about
  ten minutes. On 06/11/2026 history was rewritten on 9 public repos (this one,
  chronoscape, consensus-drift, photocopy, woop-woop, vantage-releases, the profile
  repo, and the One Story and Aftertimes sites) so no commit carries the work address
  or the second Gmail account, and no file carries three subscribers' emails. Two
  steps only the account owner can take:
  1. GitHub Support, "Remove cached views": ask them to purge the dereferenced commits
     in those 9 repos. Until they do, an old commit is still served by its exact ID
     (checked: `commits/49949ae` in this repo still returned the work address).
  2. Settings, Emails: tick "Block command line pushes that expose my email", so a
     machine set to a real address is refused rather than published.

## Shipped

- ~~Link the podcast from the homepage~~ - the Elsewhere row links the Thinkerings
  show on Spotify and the Substack beside it (`index.html`, "Thinkerings, the
  podcast"). Row closed 06/11/2026.
