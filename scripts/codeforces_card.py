import json
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

HANDLE = "ggca"
OUT = Path("assets/codeforces-stats.svg")

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


def first_solves(subs):
    """Задача -> дата первого успешного решения (UTC)."""
    first = {}
    for s in sorted(subs, key=lambda s: s["creationTimeSeconds"]):
        if s.get("verdict") != "OK":
            continue
        p = s["problem"]
        key = (p.get("contestId"), p["index"])
        if key not in first:
            first[key] = datetime.fromtimestamp(
                s["creationTimeSeconds"], timezone.utc
            ).date()
    return first


def max_streak(days):
    best = cur = 0
    prev = None
    for d in sorted(days):
        cur = cur + 1 if prev and (d - prev).days == 1 else 1
        best = max(best, cur)
        prev = d
    return best


def compute_stats(first):
    today = datetime.now(timezone.utc).date()
    year_ago = today - timedelta(days=365)
    month_ago = today - timedelta(days=30)
    dates = list(first.values())
    year = {d for d in dates if d >= year_ago}
    month = {d for d in dates if d >= month_ago}
    return [
        (len(dates), "solved, all time"),
        (len(year), "solved, year"),
        (len(month), "solved, month"),
        (f"{max_streak(set(dates))} d", "streak, all time"),
        (f"{max_streak(year)} d", "streak, year"),
        (f"{max_streak(month)} d", "streak, month"),
    ]


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


def build_svg(user, first):
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(weeks=52)
    start -= timedelta(days=start.weekday())  # понедельник

    per_day = Counter(first.values())
    step, size = 13, 10
    left = 25
    weeks = (today - start).days // 7 + 1
    width = left + weeks * step + 25
    height = 330
    inner = width - 2 * left

    rank = user.get("rank", "unrated")
    rating = user.get("rating", "—")
    max_rating = user.get("maxRating", "—")
    color = RANK_COLORS.get(rank, "#9aa4b2")

    # --- шесть значений ---
    col_w = inner / 6
    stats = []
    for i, (value, label) in enumerate(compute_stats(first)):
        x = left + i * col_w
        stats.append(
            f'<text x="{x:.0f}" y="118" font-family="{FONT}" font-size="22" '
            f'font-weight="600" fill="#a9fef7">{value}</text>'
            f'<text x="{x:.0f}" y="136" font-family="{FONT}" font-size="11" '
            f'fill="#9aa4b2">{label}</text>'
        )

    # --- сетка активности ---
    top = 204
    total = 0
    cells, months = [], []
    last_month = None
    for col in range(weeks):
        week_start = start + timedelta(weeks=col)
        if week_start.month != last_month:
            months.append(
                f'<text x="{left + col * step}" y="196" font-family="{FONT}" '
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
                f"<title>{d.isoformat()}: {n} solved</title></rect>"
            )

    legend_x = width - left - 5 * step - 60
    legend = [
        f'<text x="{legend_x}" y="313" font-family="{FONT}" font-size="11" fill="#a9fef7">Less</text>'
    ]
    for i, n in enumerate([0, 1, 2, 4, 7]):
        legend.append(
            f'<rect x="{legend_x + 30 + i * step}" y="304" width="{size}" height="{size}" '
            f'rx="2" fill="{level_color(n)}"/>'
        )
    legend.append(
        f'<text x="{legend_x + 30 + 5 * step + 3}" y="313" font-family="{FONT}" '
        f'font-size="11" fill="#a9fef7">More</text>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="#141321" stroke="#e4e2e2" stroke-opacity="0.2"/>
  <text x="{left}" y="45" font-family="{FONT}" font-size="24" font-weight="600" fill="#fe428e">Codeforces: {escape(user["handle"])}</text>
  <text x="{width - left}" y="35" text-anchor="end" font-family="{FONT}" font-size="16" font-weight="600" fill="{color}">{escape(rank.title())}</text>
  <text x="{width - left}" y="56" text-anchor="end" font-family="{FONT}" font-size="13" fill="#a9fef7">Rating {rating} (max {max_rating})</text>
  <line x1="{left}" y1="78" x2="{width - left}" y2="78" stroke="#e4e2e2" stroke-opacity="0.15"/>
  {"".join(stats)}
  <line x1="{left}" y1="154" x2="{width - left}" y2="154" stroke="#e4e2e2" stroke-opacity="0.15"/>
  <text x="{left}" y="177" font-family="{FONT}" font-size="14" font-weight="600" fill="#fe428e">{total} solved in the last year</text>
  {"".join(months)}
  {"".join(cells)}
  {"".join(legend)}
</svg>
"""


user = api("user.info", handles=HANDLE)[0]
subs = api("user.status", handle=HANDLE)
first = first_solves(subs)

print("Solved problems:", sorted((str(k), str(v)) for k, v in first.items()))

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(build_svg(user, first), encoding="utf-8")
print("Saved", OUT)
