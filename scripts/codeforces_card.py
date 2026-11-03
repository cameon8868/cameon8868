import json
import urllib.parse
import urllib.request
from html import escape
from pathlib import Path

HANDLE = "ggca"
OUT = Path("assets/codeforces-card.svg")

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


def api(method, **params):
    url = f"https://codeforces.com/api/{method}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    if data.get("status") != "OK":
        raise RuntimeError(data.get("comment", "Codeforces API error"))
    return data["result"]


user = api("user.info", handles=HANDLE)[0]
subs = api("user.status", handle=HANDLE)

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

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="495" height="150" viewBox="0 0 495 150">
  <rect x="0.5" y="0.5" width="494" height="149" rx="8" fill="#141321" stroke="#e4e2e2" stroke-opacity="0.2"/>
  <text x="25" y="35" font-family="Segoe UI, Ubuntu, sans-serif" font-size="18" font-weight="600" fill="#fe428e">Codeforces: {escape(user["handle"])}</text>
  <text x="25" y="75" font-family="Segoe UI, Ubuntu, sans-serif" font-size="15" fill="{color}" font-weight="600">{escape(rank.title())}</text>
  <text x="25" y="100" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14" fill="#a9fef7">Rating: {rating} (max {max_rating})</text>
  <text x="25" y="122" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14" fill="#a9fef7">Max rank: {escape(max_rank.title())}</text>
  <text x="300" y="100" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14" fill="#a9fef7">Solved: {len(solved)}</text>
  <text x="300" y="122" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14" fill="#a9fef7">Contribution: {user.get("contribution", 0)}</text>
</svg>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(svg, encoding="utf-8")
print("Saved", OUT)
