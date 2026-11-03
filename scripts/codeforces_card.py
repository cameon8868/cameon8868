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
  <text x="300" y="122" font-family="{FONT}" font-size="14"
