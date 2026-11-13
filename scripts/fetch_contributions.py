#!/usr/bin/env python3
"""Refresh data/contributions.json and data/repos.json (standard library only).

Usage:  python scripts/fetch_contributions.py [github_username]

The username comes from, in order: the argument, config.json "github_user",
the GITHUB_REPOSITORY_OWNER variable that GitHub Actions sets.

Contributions are read from the public calendar GitHub already serves at
https://github.com/users/<user>/contributions, so no token is needed (this
counts public contributions only). Repos come from the REST API; a token in
GITHUB_TOKEN is used when present to avoid rate limits.

If a request fails, the existing JSON is left untouched and the script exits 0
so a bad day never breaks the workflow.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UA = {"User-Agent": "profile-readme-cards (+https://github.com)"}


def http_get(url: str, headers: dict | None = None) -> str:
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def warn(msg: str) -> None:
    print(f"::warning::{msg}")


def load_config() -> dict:
    try:
        return json.loads((ROOT / "config.json").read_text())
    except (OSError, ValueError):
        return {}


# ---------------------------------------------------------------- contributions

ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
FALLBACK_COUNT = {0: 0, 1: 1, 2: 3, 3: 6, 4: 10}  # only used if tooltips are missing


def parse_calendar(html: str) -> list[list]:
    """Return [[date, count, level], ...] sorted by date."""
    tips = {}
    for m in re.finditer(r"<tool-tip\b([^>]*)>(.*?)</tool-tip>", html, re.S):
        attrs = dict(ATTR.findall(m.group(1)))
        target = attrs.get("for")
        if not target:
            continue
        text = unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        n = re.match(r"(\d[\d,]*)\s+contribution", text)
        if n:
            tips[target] = int(n.group(1).replace(",", ""))
        elif text.lower().startswith("no contributions"):
            tips[target] = 0

    today = dt.date.today().isoformat()
    days = {}
    for m in re.finditer(r"<td\b([^>]*)>", html):
        attrs = dict(ATTR.findall(m.group(1)))
        date = attrs.get("data-date")
        if not date or date > today:
            continue
        level = int(attrs.get("data-level", "0") or 0)
        count = tips.get(attrs.get("id", ""), FALLBACK_COUNT.get(level, 0))
        days[date] = [date, count, level]
    return [days[k] for k in sorted(days)]


def fetch_contributions(user: str) -> None:
    html = http_get(f"https://github.com/users/{user}/contributions")
    days = parse_calendar(html)
    if len(days) < 300:
        raise RuntimeError(f"calendar looked wrong ({len(days)} days parsed)")
    payload = {
        "user": user,
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sample": False,
        "total": sum(d[1] for d in days),
        "days": days,
    }
    (DATA / "contributions.json").write_text(json.dumps(payload, separators=(",", ":")))
    print(f"contributions: {len(days)} days, {payload['total']} total for {user}")


# ------------------------------------------------------------------------ repos

def fetch_repos(user: str, cfg: dict) -> None:
    want = int(cfg.get("repos", {}).get("count", 4))
    pinned = cfg.get("repos", {}).get("featured", []) or []
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    raw = json.loads(http_get(f"https://api.github.com/users/{user}/repos?per_page=100&type=owner&sort=pushed", headers))

    by_name = {r["name"].lower(): r for r in raw}
    chosen = []
    for name in pinned:  # pinned repos first, in the order given
        r = by_name.get(str(name).lower())
        if r:
            chosen.append(r)
    if len(chosen) < want:
        rest = [
            r for r in raw
            if not r["fork"] and not r["archived"] and r["name"].lower() != user.lower() and r not in chosen
        ]
        rest.sort(key=lambda r: (r["stargazers_count"], r["pushed_at"]), reverse=True)
        chosen += rest[: want - len(chosen)]

    repos = [
        {
            "name": r["name"],
            "description": (r.get("description") or "").strip(),
            "language": r.get("language") or "",
            "stars": r.get("stargazers_count", 0),
            "url": r["html_url"],
        }
        for r in chosen[:want]
    ]
    (DATA / "repos.json").write_text(json.dumps({"user": user, "sample": False, "repos": repos}, indent=2))
    print(f"repos: {', '.join(r['name'] for r in repos) or 'none'}")


def main() -> int:
    cfg = load_config()
    user = (
        (sys.argv[1] if len(sys.argv) > 1 else "")
        or cfg.get("github_user", "")
        or os.environ.get("GITHUB_REPOSITORY_OWNER", "")
    )
    if not user:
        warn("no GitHub username: pass one, set github_user in config.json, or run inside GitHub Actions")
        return 0
    DATA.mkdir(exist_ok=True)
    for label, fn in (("contributions", lambda: fetch_contributions(user)), ("repos", lambda: fetch_repos(user, cfg))):
        try:
            fn()
        except (urllib.error.URLError, RuntimeError, ValueError, KeyError) as e:
            warn(f"{label} not refreshed, keeping the previous file: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
