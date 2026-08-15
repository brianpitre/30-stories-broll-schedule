# 30 Stories B-Roll — Shoot Schedule

Mobile shoot schedule for the *30 Stories* B-roll pickups at The Life Church
(Houston Levee, Austin Peay, Highland), August 16 – September 6, 2026.

**Live page:** https://brianpitre.github.io/30-stories-broll-schedule/

## Editing the schedule

`index.html` is **generated — do not hand-edit it.** Change the schedule in
`data/schedule.json`, then:

```
python3 build.py          # rewrites index.html
python3 build.py --check  # exits 1 if index.html is stale
```

Every count on the page (sessions, shoot days, per-day, per-campus, the location
chips, "numbers on file") is derived from the slot data at build time, so those
can't drift. `template.html` holds the shell — styles, fonts, and scripts — with
`{{STATS}}`, `{{JUMP}}`, `{{CHIPS}}`, `{{DAYS}}` and `{{SYNCED}}` filled in.

### Deliberate deviations from the sources

`data/schedule.json` has an `overrides` block recording where the page
intentionally disagrees with the *30 Stories B-Roll* sheet — people kept off the
page, and people on the page who aren't in the sheet. The sync reads it so it
doesn't undo those decisions. Add a `reason` whenever you add an entry.

## Notes

- Single self-contained `index.html` — fonts are embedded as base64, so the page
  works with no signal in the building.
- Tap a date to jump, tap a number to call, tap **Text** to SMS. Location chips
  filter the list; **Print** produces a paper call sheet.
- The page marks days as *Wrapped* / *Today* / *Next up* automatically from the
  device clock.

## Privacy

This page contains personal phone numbers and email addresses for the people
being filmed. It is set to `noindex` (meta tag + `robots.txt`) so it will not
appear in search results, but the URL itself is publicly reachable. **Share the
link only with the shoot crew.**

To take it down: delete this repo, or turn off GitHub Pages in
Settings → Pages.
