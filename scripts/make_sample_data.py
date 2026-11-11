"""Creates SAMPLE data so the cards can be previewed offline. Real data comes from fetch_data.py."""
import json, os, random, datetime as dt
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
random.seed(7)
end = dt.date.today(); start = end - dt.timedelta(days=364)
start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # align to Sunday
days, d = [], start
while d <= end:
    wk = d.weekday() < 5
    n = random.choice([0,0,1,2,3,5,8,12]) if wk and random.random() < .7 else (random.choice([0,0,0,1,2]) if random.random() < .3 else 0)
    days.append({"date": d.isoformat(), "count": n}); d += dt.timedelta(days=1)
json.dump({"sample": True, "total": sum(x["count"] for x in days), "days": days}, open(f"{ROOT}/data/contributions.json", "w"))
json.dump({"sample": True, "followers": 42, "repos": 18, "stars": 130, "featured": [
  {"name":"onboardAI","description":"AI-powered developer onboarding for unfamiliar codebases (sample text, replaced by live data).","stars":64,"forks":9,"url":"https://github.com/rohit-anish/onboardAI","language":"TypeScript","color":"#3178c6"},
  {"name":"Pragati","description":"AI textbook tutor for Tamil and Tanglish learners (sample text, replaced by live data).","stars":41,"forks":5,"url":"https://github.com/rohit-anish/Pragati","language":"TypeScript","color":"#3572A5"},
  {"name":"your-third-repo","description":"Pin a third repo on GitHub and it appears here.","stars":25,"forks":2,"url":"https://github.com/rohit-anish","language":"Go","color":"#00ADD8"}]},
  open(f"{ROOT}/data/profile.json", "w"), indent=1)
