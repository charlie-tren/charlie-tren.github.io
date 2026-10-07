# charlietrenorden.com, open items

Site-level work on the hub itself. Anything about a project belongs in that
project's own repo, since most directories here are deploy targets.

- [ ] **Link the podcast from the homepage.** Thinkerings went live on Spotify
  on 23/09/2026 and nothing here points at the show. Two places it could go and
  they are not the same decision:
  - The **Elsewhere** row already has a Spotify link, at
    `https://open.spotify.com/playlist/7h4WfWsQspkJsEsSHD47ya`, which is a
    playlist rather than the podcast. Either repoint it at the show or add a
    second entry, and note that the row is already six items wide.
  - The **Thinkerings card** links to `https://thinkerings.substack.com/`. The
    blog and the podcast share a name, so a card with two destinations needs a
    decision about which one the card is for.

- [ ] **Point the Position Record trigger alert at an inbox that is read.**
  **Charlie-only.** `position-record/alert.py` opens a GitHub issue assigned to
  `charlie-tren` when a watched pair crosses its trigger, and GitHub emails the
  assignee. That account's notification address is charlie.rochfordgroup@gmail.com,
  so a trigger fires into an inbox he does not read. charlie.tren@gmail.com cannot
  be added: GitHub answers "email is already in use", because the dormant
  `charlietren` account holds it. The fix is about two minutes, all on his side:
  sign into `charlietren` (GitHub's account switcher keeps `charlie-tren` signed
  in), remove the address there, add and verify it on `charlie-tren`, and set it
  as the default under Settings, Notifications. A session can then re-fire the
  test with `gh workflow run "Refresh position record" -f alert_test=true` and
  confirm the mail lands. Left mid-flow 23/09/2026; nothing has fired since.
