#!/usr/bin/env python3
"""Write placeholder data/contributions.json and data/repos.json.

Used only so the cards can be previewed before the GitHub Action has run.
Both files carry "sample": true, which makes the cards show a small
SAMPLE DATA badge. fetch_contributions.py overwrites them with real data.
"""
import datetime as dt
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def level_for(count: int) -> int:
    if count == 0:
        return 0
    if count < 3:
        return 1
    if count < 6:
        return 2
    if count < 10:
        return 3
    return 4


def main() -> None:
    DATA.mkdir(exist_ok=True)
    rng = random.Random(2027)
    today = dt.date.today()
    start = today - dt.timedelta(days=364)

    days = []
    burst_until = None
    for i in range(365):
        d = start + dt.timedelta(days=i)
        weekday_boost = 0.75 if d.weekday() < 5 else 0.5
        if burst_until and d <= burst_until:
            p, hi = 0.92, 14
        else:
            p, hi = weekday_boost * 0.7, 7
            if rng.random() < 0.012:
                burst_until = d + dt.timedelta(days=rng.randint(6, 16))
        count = rng.randint(1, hi) if rng.random() < p else 0
        days.append([d.isoformat(), count, level_for(count)])

    (DATA / "contributions.json").write_text(
        json.dumps(
            {
                "user": "sample",
                "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "sample": True,
                "total": sum(c for _, c, _ in days),
                "days": days,
            },
            separators=(",", ":"),
        )
    )

    repos = [
        {"name": "mern-app", "description": "Full-stack MERN project with auth, REST API and a React front end.", "language": "JavaScript", "stars": 0, "url": "https://github.com/"},
        {"name": "langgraph-agent", "description": "Multi-step LLM agent built with LangGraph and tool calling.", "language": "Python", "stars": 0, "url": "https://github.com/"},
        {"name": "rag-chatbot", "description": "Retrieval-augmented chatbot over your own documents with LangChain.", "language": "Python", "stars": 0, "url": "https://github.com/"},
        {"name": "dsa-in-java", "description": "Data structures and algorithms practice, solved in Java.", "language": "Java", "stars": 0, "url": "https://github.com/"},
    ]
    (DATA / "repos.json").write_text(json.dumps({"user": "sample", "sample": True, "repos": repos}, indent=2))
    print("wrote sample data to", DATA)


if __name__ == "__main__":
    main()
