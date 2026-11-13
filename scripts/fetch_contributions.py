"""Fetch the last year of contributions into data/contributions.json (uses GITHUB_TOKEN)."""
import json, os, urllib.request
USER = os.environ.get("GH_USER", "HariomTiwari01")
Q = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": Q, "variables": {"u": USER}}).encode(),
    headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
)
weeks = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
days = [{"date": d["date"], "count": d["contributionCount"]} for w in weeks for d in w["contributionDays"]]
os.makedirs("data", exist_ok=True)
json.dump({"user": USER, "days": days}, open("data/contributions.json", "w"))
print(f"saved {len(days)} days")
