#!/usr/bin/env python3
"""Regenerate index.html from data/schedule.json + template.html.

The published page is a single self-contained file, so it is built rather than
hand-edited: edit data/schedule.json, run this script, commit the result.
Counts (sessions, per-day, per-campus, location chips) are all derived here, so
they cannot drift away from the slot data.

    python3 build.py            # write index.html
    python3 build.py --check    # exit 1 if index.html is stale, write nothing
"""

import json
import sys
from datetime import datetime, date

ROOT = __file__.rsplit("/", 1)[0]
ORDER = ["hsl", "asp", "hld"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

PHONE_SVG = ('<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8c1.4 2.8 '
             '3.8 5.2 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.4.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 '
             '1-1 1-9.4 0-17-7.6-17-17 0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.4 0 '
             '.8-.2 1l-2.3 2.2z"/></svg>')
SMS_SVG = ('<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 2H4c-1.1 0-2 .9-2 '
           '2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM7 9h10v2H7V9zm7 5H7v-2h7v2zm3-6H7V6h10v2z"'
           '/></svg>')


def esc(text):
    """Escape only the structural characters. Unicode is left literal --
    the fonts are embedded, so the page renders it fine offline."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pretty_phone(e164):
    """+19014844845 -> (901) 484-4845. Anything unexpected passes through."""
    digits = e164.lstrip("+")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10 or not digits.isdigit():
        return e164
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def minutes(t):
    """'8:30 am' -> 510, for sorting and for the campus time window."""
    clock, meridiem = t.strip().rsplit(" ", 1)
    hour, minute = (int(p) for p in clock.split(":"))
    hour = hour % 12 + (12 if meridiem.lower() == "pm" else 0)
    return hour * 60 + minute


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def render_slot(slot):
    name = esc(slot["name"])
    out = ['          <article class="slot">',
           f'            <div class="slot-time"><span class="t1">{esc(slot["start"])}</span>'
           f'<span class="t2">to {esc(slot["end"])}</span></div>',
           '            <div class="slot-who">',
           f'              <h4 class="slot-name">{name}</h4>']

    if slot.get("phone"):
        tel = slot["phone"]
        out.append(
            f'              <div class="actions"><a class="act act-call" href="tel:{tel}">'
            f'{PHONE_SVG}<span class="act-txt">{pretty_phone(tel)}</span></a>'
            f'<a class="act act-sms" href="sms:{tel}" aria-label="Text {name}">'
            f'{SMS_SVG}<span class="act-lbl">Text</span></a></div>')
    else:
        out.append('              <div class="actions">'
                   '<span class="act act-none">No number on file</span></div>')

    if slot.get("emails"):
        links = ""
        for entry in slot["emails"]:
            address = esc(entry["address"])
            tag = f' <span class="tagx">{esc(entry["tag"])}</span>' if entry.get("tag") else ""
            links += f'<a class="contact" href="mailto:{address}">{address}{tag}</a>'
        out.append(f'              <div class="contacts">{links}</div>')
    out.append("            </div>")

    notes = []
    if slot.get("shot"):
        notes.append(f'<p class="note note-shot"><span class="nlabel">Shot</span>'
                     f'{esc(slot["shot"])}</p>')
    if slot.get("their_note"):
        notes.append(f'<p class="note note-them"><span class="nlabel">Their note</span>'
                     f'{esc(slot["their_note"])}</p>')
    inner = "".join(notes) if notes else '<span class="note-none">&mdash;</span>'
    out.append(f'            <div class="slot-note">{inner}</div>')
    out.append("          </article>")
    return "\n".join(out)


def render_campus(campus, names):
    code = campus["code"]
    slots = sorted(campus["slots"], key=lambda s: minutes(s["start"]))
    window = f'{slots[0]["start"]} &ndash; {max(slots, key=lambda s: minutes(s["end"]))["end"]}'
    out = [f'      <section class="campus campus-{code}" data-campus="{code}">',
           '        <header class="campus-head">',
           f'          <span class="campus-code">{code.upper()}</span>',
           f'          <h3>{esc(names[code])}</h3>',
           f'          <span class="campus-count">{plural(len(slots), "session")}</span>',
           f'          <span class="campus-window">{window}</span>',
           "        </header>",
           '        <div class="slots">',
           '          <div class="slots-head"><span>Time</span><span>Who</span>'
           "<span>Notes</span></div>"]
    out += [render_slot(s) for s in slots]
    out += ["        </div>", "      </section>"]
    return "\n".join(out)


def render_day(day, index, names):
    campuses = sorted((c for c in day["campuses"] if c["slots"]),
                      key=lambda c: ORDER.index(c["code"]))
    total = sum(len(c["slots"]) for c in campuses)
    codes = " &middot; ".join(c["code"].upper() for c in campuses)
    iso = day["date"]
    out = [f'    <section class="day" id="d{iso}" data-day="{iso}">',
           '      <header class="day-head">',
           f'        <span class="daynum">{index:02d}</span>',
           f'        <div class="day-date"><span class="dow">{esc(day["dow"])}</span>'
           f'<span class="dnum">{esc(day["label"])}</span></div>',
           f'        <div class="day-meta"><span class="todaypill"></span>'
           f'<span class="daycount">{plural(total, "session")}</span>'
           f'<span class="daycamps">{codes}</span></div>',
           "      </header>"]
    out += [render_campus(c, names) for c in campuses]
    out.append("    </section>")
    return "\n".join(out)


def build(doc, synced_at):
    names = doc["campuses"]
    days = sorted(doc["days"], key=lambda d: d["date"])
    days = [d for d in days if any(c["slots"] for c in d["campuses"])]

    per_campus = {code: 0 for code in ORDER}
    for day in days:
        for campus in day["campuses"]:
            per_campus[campus["code"]] += len(campus["slots"])
    total = sum(per_campus.values())
    with_number = sum(1 for d in days for c in d["campuses"] for s in c["slots"] if s.get("phone"))

    stats = "\n".join([
        '    <div class="stats">',
        f'      <div class="stat"><div class="n">{total}</div><div class="l">Sessions</div></div>',
        f'      <div class="stat"><div class="n">{len(days)}</div>'
        '<div class="l">Shoot days</div></div>',
        f'      <div class="stat"><div class="n">{len(ORDER)}</div>'
        '<div class="l">Locations</div></div>',
        f'      <div class="stat stat-wide"><div class="n">{doc["window"]["label"]}</div>'
        f'<div class="l">Window &middot; {with_number}/{total} numbers on file</div></div>',
        "    </div>"])

    jump = "".join(
        f'<a class="jbtn" href="#d{d["date"]}" data-day="{d["date"]}">'
        f'<span class="jdow">{d["dow"][:3]}</span>'
        f'<span class="jdate">{MONTHS[int(d["date"][5:7]) - 1][:3]} '
        f'{int(d["date"][8:10])}</span>'
        f'<span class="jn">{sum(len(c["slots"]) for c in d["campuses"])}</span></a>'
        for d in days)

    chips = "    " + "".join(
        f'<button class="chip chip-{code}" data-filter="{code}" type="button">'
        f'{esc(names[code])} <span>{per_campus[code]}</span></button>'
        for code in ORDER)

    body = "\n".join(render_day(d, i, names) for i, d in enumerate(days, 1))

    stamp = (f'<p class="synced">Synced from Calendly and the <em>30 Stories B-Roll</em> sheet '
             f'&middot; {synced_at}</p>')

    html = open(f"{ROOT}/template.html", encoding="utf-8").read()
    for key, value in (("{{STATS}}", stats), ("{{JUMP}}", jump),
                       ("{{CHIPS}}", chips), ("{{DAYS}}", body), ("{{SYNCED}}", stamp)):
        html = html.replace(key, value)
    return html


def main():
    doc = json.load(open(f"{ROOT}/data/schedule.json", encoding="utf-8"))
    check = "--check" in sys.argv

    try:
        current = open(f"{ROOT}/index.html", encoding="utf-8").read()
    except FileNotFoundError:
        current = ""

    # Render with the stored stamp first. If that matches what is on disk, nothing
    # about the schedule actually changed -- leave the file alone rather than
    # bumping the timestamp, so "synced" keeps meaning "last real change".
    previous = doc.get("synced_at")
    if previous and build(doc, previous) == current:
        print("index.html is up to date" if check else "index.html unchanged")
        return 0

    if check:
        print("index.html is STALE - run: python3 build.py")
        return 1

    synced_at = datetime.now().strftime("%b %-d, %Y at %-I:%M %p")
    open(f"{ROOT}/index.html", "w", encoding="utf-8").write(build(doc, synced_at))
    doc["synced_at"] = synced_at
    json.dump(doc, open(f"{ROOT}/data/schedule.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"index.html rebuilt ({synced_at})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
