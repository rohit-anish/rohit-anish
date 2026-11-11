"""Fetch real profile data -> data/contributions.json + data/profile.json.
No token required. Contributions are read from the public contribution calendar
(the same one shown on your profile, including private contributions if you enabled
that setting). Repo/follower stats come from the REST API; GITHUB_TOKEN is optional
and only raises the rate limit. If anything fails, the previous JSON files are kept."""
import datetime, json, os, re, sys, urllib.request
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
cfg = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
USER = cfg["username"]
TOK = os.environ.get("GITHUB_TOKEN")

def get(url, api=True):
    h = {"User-Agent": "profile-cards"}
    if api:
        h["Accept"] = "application/vnd.github+json"
        if TOK: h["Authorization"] = f"Bearer {TOK}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
        body = r.read().decode()
    return json.loads(body) if api else body

def contributions():
    # "contribution_year": "current" (default) -> Jan-Dec of this year, like GitHub's year tab; "rolling" -> last 12 months
    mode = str(cfg.get("contribution_year", "current"))
    year = None if mode == "rolling" else (datetime.date.today().year if mode == "current" else int(mode))
    q = f"?from={year}-01-01&to={year}-12-31" if year else ""
    html = get(f"https://github.com/users/{USER}/contributions{q}", api=False)
    dates = dict(re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?id="([^"]+)"', html))
    dates = {cid: d for d, cid in dates.items()}
    counts = {}
    for cid, text in re.findall(r'<tool-tip[^>]*?for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        if cid in dates:
            m = re.match(r"(\d[\d,]*) contribution", text)
            counts[dates[cid]] = int(m.group(1).replace(",", "")) if m else 0
    if len(counts) < 300: raise RuntimeError(f"calendar parse failed ({len(counts)} days)")
    days = [{"date": d, "count": counts[d]} for d in sorted(counts)]
    return {"sample": False, "year": year, "total": sum(x["count"] for x in days), "days": days}

def card(r):
    lang = r.get("language") or ""
    return {"name": r["name"], "description": r.get("description") or "", "stars": r["stargazers_count"],
            "forks": r["forks_count"], "url": r["html_url"], "language": lang, "color": COLORS.get(lang, "#8b95b3")}

COLORS = {"Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Go": "#00ADD8", "C++": "#f34b7d",
          "C": "#555555", "C#": "#178600", "Java": "#b07219", "HTML": "#e34c26", "CSS": "#663399", "Rust": "#dea584",
          "Jupyter Notebook": "#DA5B0B", "Shell": "#89e051", "Kotlin": "#A97BFF", "Dart": "#00B4AB", "ShaderLab": "#222c37"}

def profile():
    u = get(f"https://api.github.com/users/{USER}")
    repos = get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    own = [r for r in repos if not r["fork"]]
    by_name = {r["name"].lower(): r for r in repos}
    feat = [by_name[n.lower()] for n in cfg.get("featured_repos", []) if n.lower() in by_name]
    rest = sorted((r for r in own if r not in feat and r["name"].lower() != USER.lower()),
                  key=lambda r: (r["stargazers_count"], r["pushed_at"] or ""), reverse=True)
    return {"sample": False, "followers": u["followers"], "repos": cfg.get("repo_count") or len(own),
            "stars": sum(r["stargazers_count"] for r in own), "featured": [card(r) for r in (feat + rest)[:3]]}

def main():
    ok = False
    for name, fn in (("contributions", contributions), ("profile", profile)):
        try:
            data = fn()
            json.dump(data, open(os.path.join(ROOT, f"data/{name}.json"), "w"), indent=None if name == "contributions" else 1)
            print(f"{name}: refreshed"); ok = True
        except Exception as e:
            print(f"{name}: kept previous data ({e})")
    if not ok: sys.exit(1)

main()
