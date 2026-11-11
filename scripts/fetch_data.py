"""Fetch real profile data via GitHub GraphQL -> data/contributions.json + data/profile.json.
Needs GITHUB_TOKEN. If anything fails, the previous JSON files are kept."""
import json, os, sys, urllib.request
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
cfg = json.load(open(os.path.join(ROOT, "config.json")))
Q = """query($login:String!){ user(login:$login){
  followers{totalCount}
  repositories(privacy:PUBLIC, ownerAffiliations:OWNER, isFork:false, first:100){totalCount nodes{stargazerCount}}
  pinnedItems(first:3, types:REPOSITORY){nodes{... on Repository{name description stargazerCount forkCount url primaryLanguage{name color}}}}
  top: repositories(privacy:PUBLIC, ownerAffiliations:OWNER, isFork:false, first:3, orderBy:{field:STARGAZERS,direction:DESC}){nodes{name description stargazerCount forkCount url primaryLanguage{name color}}}
  contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}
}}"""
FIELDS = "name description stargazerCount forkCount url primaryLanguage{name color}"
def main():
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok: sys.exit("no GITHUB_TOKEN; keeping existing data")
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": Q, "variables": {"login": cfg["username"]}}).encode(),
        headers={"Authorization": f"bearer {tok}", "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    if "errors" in d or not d.get("data", {}).get("user"): sys.exit(f"API error: {d.get('errors')}")
    u = d["data"]["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [{"date": x["date"], "count": x["contributionCount"]} for w in cal["weeks"] for x in w["contributionDays"]]
    json.dump({"sample": False, "total": cal["totalContributions"], "days": days},
              open(os.path.join(ROOT, "data/contributions.json"), "w"))
    named = []
    for n in cfg.get("featured_repos", []):
        q2 = 'query($o:String!,$n:String!){repository(owner:$o,name:$n){%s}}' % FIELDS
        r2 = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": q2, "variables": {"o": cfg["username"], "n": n}}).encode(),
            headers={"Authorization": f"bearer {tok}", "Content-Type": "application/json"})
        try:
            rp = json.load(urllib.request.urlopen(r2, timeout=30))["data"]["repository"]
            if rp: named.append(rp)
        except Exception as e: print("skip", n, e)
    seen = {r["name"] for r in named}
    rest = [r for r in (u["pinnedItems"]["nodes"] + u["top"]["nodes"]) if r["name"] not in seen]
    feat = (named + rest)[:3]
    json.dump({"sample": False, "followers": u["followers"]["totalCount"],
               "repos": u["repositories"]["totalCount"],
               "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
               "featured": [{"name": r["name"], "description": r["description"] or "", "stars": r["stargazerCount"],
                             "forks": r["forkCount"], "url": r["url"],
                             "language": (r["primaryLanguage"] or {}).get("name", ""),
                             "color": (r["primaryLanguage"] or {}).get("color") or "#8b95b3"} for r in feat]},
              open(os.path.join(ROOT, "data/profile.json"), "w"), indent=1)
    print("data refreshed")
main()
