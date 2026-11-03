import json
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

HANDLE = "ggca"
OUT_DIR = Path("assets")

RANK_COLORS = {
    "newbie": "#808080",
    "pupil": "#008000",
    "specialist": "#03a89e",
    "expert": "#4d7cfe",
    "candidate master": "#aa00aa",
    "master": "#ff8c00",
    "international master": "#ff8c00",
    "grandmaster": "#ff3030",
    "international grandmaster": "#ff3030",
    "legendary grandmaster": "#ff3030",
}

FONT = "Segoe UI, Ubuntu, sans-serif"


def api(method, **params):
    url = f"https://codeforces.com/api/{method}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    if data.get("status") != "OK":
        raise RuntimeError(data.get("comment", "Codeforces API error"))
    return data["result"]


def build_card(user, subs):
    solved = {
        (s["problem"].get("contestId"), s["problem"]["index"])
        for s in subs
        if s.get("verdict") == "OK"
    }
    rank = user.get("rank", "unrated")
    max_rank = user.get("maxRank", "unrated")
    rating = user.get("rating", "—")
    max_rating = user.get("maxRating", "—")
    color = RANK_COLORS.get(rank, "#9aa4b2")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="495" height="150" viewBox="0 0 495 150">
  <rect x="0.5" y="0.5" width="494" height="149" rx="8" fill="#141321" stroke="#e4e2e2" stroke-opacity="0.2"/>
  <text x="25" y="35" font-family="{FONT}" font-size="18" font-weight="600" fill="#fe428e">Codeforces: {escape(user["handle"])}</text>
  <text x="25" y="75" font-family="{FONT}" font-size="15" fill="{color}" font-weight="600">{escape(rank.title())}</text>
  <text x="25" y="100" font-family="{FONT}" font-size="14" fill="#a9fef7">Rating: {rating} (max {max_rating})</text>
  <text x="25" y="122" font-family="{FONT}" font-size="14" fill="#a9fef7">Max rank: {escape(max_rank.title())}</text>
  <text x="300" y="100" font-family="{FONT}" font-size="14" fill="#a9fef7">Solved: {len(solved)}</text>
  <text x="300" y="122" font-family="{FONT}" font-size="14" fill="#a9fef7">Contribution: {user.get("contribution", 0)}</text>
</svg>
"""


def level_color(n):
    if n == 0:
        return "#2a2a3e"
    if n == 1:
        return "#0e4429"
    if n <= 3:
        return "#006d32"
    if n <= 6:
        return "#26a641"
    return "#39d353"


def build_heatmap(subs):
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(weeks=52)
    start -= timedelta(days=start.weekday())  # начало недели (понедельник)

    per_day = Counter(
        datetime.fromtimestamp(s["creationTimeSeconds"], timezone.utc).date()
        for s in subs
    )

    step, size = 13, 10
    left, top = 25, 68
    weeks = (today - start).days // 7 + 1
    width = left + weeks * step + 25
    height = 200

    total = 0
    cells, months = [], []
    last_month = None
    for col in range(weeks):
        week_start = start + timedelta(weeks=col)
        if week_start.month != last_month:
            months.append(
                f'<text x="{left + col * step}" y="58" font-family="{FONT}" '
                f'font-size="11" fill="#a9fef7">{week_start.strftime("%b")}</text>'
            )
            last_month = week_start.month
        for row in range(7):
            d = week_start + timedelta(days=row)
            if d > today:
                continue
            n = per_day.get(d, 0)
            total += n
            cells.append(
                f'<rect x="{left + col * step}" y="{top + row * step}" '
                f'width="{size}" height="{size}" rx="2" fill="{level_color(n)}">'
                f"<title>{d.isoformat()}: {n} submissions</title></rect>"
            )

    legend_x = width - 25 - 5 * step - 60
    legend = [
        f'<text x="{legend_x}" y="185" font-family="{FONT}" font-size="11" fill="#a9fef7">Less</text>'
    ]
    for i, n in enumerate([0, 1, 2, 4, 7]):
        legend.append(
            f'<rect x="{legend_x + 30 + i * step}" y="176" width="{size}" height="{size}" '
            f'rx="2" fill="{level_color(n)}"/>'
        )
    legend.append(
        f'<text x="{legend_x + 30 + 5 * step + 3}" y="185" font-family="{FONT}" '
        f'font-size="11" fill="#a9fef7">More</text>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="#141321" stroke="#e4e2e2" stroke-opacity="0.2"/>
  <text x="25" y="30" font-family="{FONT}" font-size="16" font-weight="600" fill="#fe428e">{total} submissions in the last year</text>
  {"".join(months)}
  {"".join(cells)}
  {"".join(legend)}
</svg>
"""


user = api("user.info", handles=HANDLE)[0]
subs = api("user.status", handle=HANDLE)

OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "codeforces-card.svg").write_text(build_card(user, subs), encoding="utf-8")
(OUT_DIR / "codeforces-activity.svg").write_text(build_heatmap(subs), encoding="utf-8")
print("Saved card and activity")
