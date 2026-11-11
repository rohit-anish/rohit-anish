"""Render every README card as an animated SVG (paper-card theme).
STATIC=1 -> final frame only. Base styles ARE the final state, so reduced-motion also shows the final frame."""
import base64, json, math, os, textwrap, datetime as dt
from xml.sax.saxutils import escape as esc

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "cards"); os.makedirs(OUT, exist_ok=True)
STATIC = os.environ.get("STATIC") == "1"
cfg = json.load(open(f"{ROOT}/config.json", encoding="utf-8"))
cal = json.load(open(f"{ROOT}/data/contributions.json"))
prof = json.load(open(f"{ROOT}/data/profile.json"))

PAPER, WHITE, EDGE = "#f4f2ec", "#fffefb", "#e2dfd5"
INK, MUTE = "#14141a", "#6f6d66"
VIOLET, CORAL, SUN = "#5b2cf0", "#f0443a", "#ffc61a"
RAMP = ["#e9e6f4", "#cdbfff", "#a58bff", "#7a52f5", "#4a1fd6"]

FONTFILES = {"serif": ("serif-500", "RA Serif", 500, "normal"), "serifi": ("serif-i-500", "RA Serif", 500, "italic"),
             "sans": ("sans-400", "RA Sans", 400, "normal"), "sansb": ("sans-700", "RA Sans", 700, "normal"),
             "mono": ("mono-400", "RA Mono", 400, "normal"), "monob": ("mono-700", "RA Mono", 700, "normal")}
def fonts(keys):
    out = ""
    for k in keys:
        f, fam, w, st = FONTFILES[k]
        b64 = base64.b64encode(open(f"{ROOT}/fonts/{f}.woff", "rb").read()).decode()
        out += f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:{st};src:url(data:font/woff;base64,{b64}) format('woff')}}"
    return out

CSS = """
.serif{font-family:'RA Serif','Lora',Georgia,serif;font-weight:500}
.serifi{font-family:'RA Serif','Lora',Georgia,serif;font-weight:500;font-style:italic}
.sans{font-family:'RA Sans','Inter',Arial,sans-serif;font-weight:400}
.sansb{font-family:'RA Sans','Inter',Arial,sans-serif;font-weight:700}
.mono{font-family:'RA Mono','DejaVu Sans Mono',Consolas,monospace}
.monob{font-family:'RA Mono','DejaVu Sans Mono',Consolas,monospace;font-weight:700}
.rise{animation:rise .9s cubic-bezier(.2,.8,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(26px)}}
.pop{transform-box:fill-box;transform-origin:center;animation:pop .45s cubic-bezier(.3,1.6,.5,1) both}
@keyframes pop{from{opacity:0;transform:scale(.15)}}
.grow{transform-box:fill-box;transform-origin:bottom;animation:grow .8s cubic-bezier(.2,.9,.3,1.1) both}
@keyframes grow{from{transform:scaleY(0)}}
.fade{animation:fade .6s ease both}
@keyframes fade{from{opacity:0}}
.draw{stroke-dasharray:1;animation:draw 2.4s cubic-bezier(.3,.7,.3,1) both}
@keyframes draw{from{stroke-dashoffset:1}}
.pulse{opacity:0;transform-box:fill-box;transform-origin:center;animation:pulse 2.4s ease-out infinite}
@keyframes pulse{0%{transform:scale(1);opacity:.7}100%{transform:scale(3.2);opacity:0}}
.nudge{animation:nudge 2.2s ease-in-out infinite}
@keyframes nudge{0%,100%{transform:translate(0,0)}50%{transform:translate(4px,-4px)}}
.shine{animation:shine 6s ease-in-out infinite}
@keyframes shine{0%{transform:translateX(0)}35%,100%{transform:translateX(1500px)}}
.tile{animation:tile 1.1s cubic-bezier(.2,.8,.2,1) both;transform-origin:0 230px}
@keyframes tile{0%{opacity:0;transform:translateY(46px) rotate(-6deg)}55%{opacity:1;transform:translateY(-10px) rotate(1.6deg)}78%{transform:translateY(3px) rotate(-.6deg)}}
.cn{opacity:0;animation:cn .001s linear}
@keyframes cn{0%,100%{opacity:1}}
.cn-last{animation:cnl .001s linear both}
@keyframes cnl{from{opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
""" + ("*{animation:none!important}" if STATIC else "")

def svg(w, h, body, title, desc="", f=("sans", "mono")):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc or title)}</desc><style>{fonts(f)}{CSS}</style>{body}</svg>')
GAP = {"hero": 18, "graph": 18, "activity": 18, "tile": 18, "repo": 18, "stack": 22}  # space below cards so they don't touch
def save(name, s):
    g = GAP.get(name.rstrip("0123456789"), 0)
    if g:
        import re as _re
        m = _re.match(r'<svg[^>]*? height="(\d+)" viewBox="0 0 (\d+) (\d+)"', s)
        s = s.replace(m[0], m[0].replace(f' height="{m[1]}"', f' height="{int(m[1])+g}"').replace(f'0 0 {m[2]} {m[3]}"', f'0 0 {m[2]} {int(m[3])+g}"'), 1)
    open(f"{OUT}/{name}.svg", "w", encoding="utf-8").write(s); print(f"{name:10s}{len(s)/1024:7.1f} KB")
def D(x): return f"animation-delay:{x:.2f}s"
def card(w, h, fill=PAPER, stroke=EDGE):
    return f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="18" fill="{fill}" stroke="{stroke}"/>'
def fmt(n): return f"{n:,}"
def wrap(t, n, maxl):
    ls = textwrap.wrap(t, n)
    if len(ls) > maxl: ls = ls[:maxl]; ls[-1] = ls[-1][: n - 3].rstrip() + "..."
    return ls
ARROW = lambda x, y, s, col: f'<path d="M{x} {y+s} L{x+s} {y} M{x+2} {y} H{x+s} V{y+s-2}" fill="none" stroke="{col}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'

# ---------- data ----------
days = [(dt.date.fromisoformat(x["date"]), x["count"]) for x in cal["days"]]
today = dt.date.today(); counts = dict(days); total = cal["total"]
def streaks():
    best = run = 0
    for d, c in days:
        run = run + 1 if c > 0 else 0; best = max(best, run)
    d = max(x for x, _ in days if x <= today)
    if counts.get(d, 0) == 0: d -= dt.timedelta(days=1)
    cur = 0
    while counts.get(d, 0) > 0: cur += 1; d -= dt.timedelta(days=1)
    return cur, best
cur_streak, best_streak = streaks()
active = sum(1 for _, c in days if c > 0)
busy_d, busy_c = max(days, key=lambda x: x[1])
YEAR = cal.get("year")
PERIOD = f"in {YEAR}" if YEAR else "in the last year"
elapsed = sum(1 for d, _ in days if d <= today)
months = [(YEAR, m) for m in range(1, 13)] if YEAR else []
for i in (range(11, -1, -1) if not YEAR else ()):
    mm, yy = today.month - i, today.year
    while mm <= 0: mm += 12; yy -= 1
    months.append((yy, mm))
mtot = [sum(c for d, c in days if (d.year, d.month) == k) for k in months]

# ---------- HERO ----------
def hero():
    W, H = 900, 320; cx = W / 2
    first, rest = (cfg["name"].split(" ", 1) + [""])[:2]
    link = cfg["link_text"]; lw = len(link) * 7.8 + 8 + 9; lx = cx - lw / 2
    body = card(W, H) +         f'<g class="rise" style="{D(.1)}"><text x="{cx}" y="64" text-anchor="middle" font-size="12" class="mono" fill="{MUTE}" letter-spacing="2.5">{esc(cfg["role"].upper())}</text></g>'         f'<g class="rise" style="{D(.3)}"><text x="{cx}" y="156" text-anchor="middle" font-size="80" class="serif" fill="{INK}">{esc(first)} <tspan class="serifi" fill="{VIOLET}">{esc(rest)}</tspan></text></g>'         f'<g class="fade" style="{D(.6)}"><rect x="{cx-24}" y="184" width="48" height="3" rx="1.5" fill="{VIOLET}"/></g>'         f'<g class="rise" style="{D(.75)}"><text x="{cx}" y="232" text-anchor="middle" font-size="19" class="sans" fill="{INK}" fill-opacity=".85">{esc(cfg["tagline"])}</text>'         f'<text x="{lx}" y="270" font-size="13" class="mono" fill="{INK}">{esc(link)}</text>{ARROW(lx + len(link)*7.8 + 8, 260, 9, VIOLET)}</g>'
    save("hero", svg(W, H, body, f"{cfg['name']} - GitHub profile", f"{cfg['name']}. {cfg['tagline']} {cfg['role']}.", ("serif", "serifi", "sans", "mono")))

# ---------- CONTRIBUTION GRAPH ----------
def graph(t0=1.8):
    W, H = 900, 250; x0, y0, cs, pitch = 42, 112, 12, 15.4
    first = days[0][0]; mx = max(c for _, c in days) or 1
    def lvl(c):
        if c == 0: return 0
        q = c / mx; return 1 if q <= .25 else 2 if q <= .5 else 3 if q <= .75 else 4
    cells, labels, last_m = [], [], None
    for d, c in days:
        col = (d - first).days // 7; row = (d.weekday() + 1) % 7
        cells.append(f'<rect class="pop" style="{D(t0 + .1 + col * .022)}" x="{x0 + col*pitch:.1f}" y="{y0 + row*pitch:.1f}" width="{cs}" height="{cs}" rx="3" fill="{RAMP[lvl(c)]}"><title>{d}: {c}</title></rect>')
        if row == 0 and d.month != last_m and d.day <= 7:
            labels.append(f'<text x="{x0 + col*pitch:.1f}" y="{y0-12}" font-size="10" class="mono" fill="{MUTE}">{d.strftime("%b")}</text>'); last_m = d.month
    body = card(W, H) + \
        f'<g class="rise" style="{D(t0)}"><text x="42" y="62" font-size="30" class="serif" fill="{INK}">Every day, <tspan class="serifi" fill="{VIOLET}">in purple</tspan></text></g>' \
        f'<g class="fade" style="{D(t0+.3)}">{"".join(labels)}</g>{"".join(cells)}'
    save("graph", svg(W, H, body, "Contribution graph", f"{fmt(total)} contributions {PERIOD}.", ("serif", "serifi", "mono")))

# ---------- ACTIVITY ----------
def activity(t0=3.0):
    W, H = 900, 276; base, maxh, bw, pitch, x0 = 226, 86, 36, 69, 50
    peak = max(mtot) or 1; bi = mtot.index(max(mtot)); bars = ""
    for i, ((yy, mm), v) in enumerate(zip(months, mtot)):
        h = max(3, v / peak * maxh); x = x0 + i * pitch; best = i == bi
        bars += f'<rect class="grow" style="{D(t0 + .2 + i*.06)}" x="{x}" y="{base-h:.1f}" width="{bw}" height="{h:.1f}" rx="5" fill="{VIOLET if best else INK}" fill-opacity="{1 if best else .85}"><title>{dt.date(yy,mm,1):%B %Y}: {v}</title></rect>' \
                f'<text x="{x+bw/2}" y="{base+22}" text-anchor="middle" font-size="10" class="mono" fill="{MUTE}">{dt.date(yy,mm,1):%b}</text>'
    side = f"{active} ACTIVE DAYS  ·  LONGEST STREAK {best_streak}"
    head = f"{YEAR} ON GITHUB" if YEAR else "THE LAST 12 MONTHS ON GITHUB"
    body = card(W, H) + \
        f'<g class="rise" style="{D(t0)}"><text x="42" y="52" font-size="11" class="mono" fill="{MUTE}" letter-spacing="1.5">{head}</text>' \
        f'<text x="42" y="98" font-size="44" class="serif" fill="{INK}">{fmt(total)} <tspan class="serifi">contributions</tspan></text>' \
        f'<text x="858" y="94" text-anchor="end" font-size="11" class="mono" fill="{MUTE}" letter-spacing="1">{side}</text></g>{bars}'
    save("activity", svg(W, H, body, "Monthly contributions", f"{fmt(total)} contributions {PERIOD}. {active} active days, longest streak {best_streak}.", ("serif", "serifi", "mono")))

# ---------- TILES ----------
def tiles(t0=4.2):
    W, H = 290, 200
    for i, t in enumerate(cfg["tiles"]):
        bgc, fg = t["bg"], t["fg"]; d0 = t0 + i * .22
        if "value" in t:
            val = t["value"]; shown = esc(val)
        else:
            val = int(prof[t["metric"]]); shown = fmt(val)
        body = f'<g class="rise" style="{D(d0)}"><rect width="{W}" height="{H}" rx="18" fill="{bgc}"/>' \
               f'<text x="26" y="44" font-size="11" class="monob" fill="{fg}" fill-opacity=".8" letter-spacing="2">{esc(t["label"])}</text>' \
               f'{ARROW(W-40, 32, 12, fg)}' \
               f'<text x="26" y="118" font-size="{t.get("size", 56)}" class="serif" fill="{fg}">{shown}</text>' \
               f'<text x="26" y="146" font-size="22" class="serifi" fill="{fg}" fill-opacity=".95">{esc(t["unit"])}</text>' \
               f'<text x="26" y="176" font-size="13" class="sans" fill="{fg}" fill-opacity=".8">{esc(t["text"])}</text></g>'
        save(f"tile{i+1}", svg(W, H, body, f'{t["label"]}: {val} {t["unit"]}', t["text"], ("serif", "serifi", "sans", "monob")))

# ---------- REPOS ----------
def repos(t0=5.4):
    for i, r in enumerate(prof["featured"][:3]):
        W, H = 290, 168; d0 = t0 + i * .2; col = r.get("color") or VIOLET
        desc = "".join(f'<text x="26" y="{82 + j*19}" font-size="13" class="sans" fill="{MUTE}">{esc(l)}</text>' for j, l in enumerate(wrap(r["description"], 36, 3)))
        lang = r["language"]
        foot = f'<circle cx="31" cy="140" r="5" fill="{col}"/><text x="44" y="144" font-size="12" class="mono" fill="{MUTE}">{esc(lang)}</text>' if lang else ""
        body = card(W, H, WHITE) + f'<g class="rise" style="{D(d0)}">' \
            f'<text x="26" y="50" font-size="17" class="sansb" fill="{INK}">{esc(r["name"][:24])}</text>{ARROW(W-40, 36, 11, VIOLET)}{desc}{foot}</g>'
        save(f"repo{i+1}", svg(W, H, body, r["name"], f'{r["name"]}: {r["description"]}', ("sans", "sansb", "mono")))

# ---------- FOCUS ----------
def pills(items, y, t0, col, tint):
    out, x = "", 42
    for i, t in enumerate(items):
        w = int(len(t) * 8.0 + 32)
        out += f'<g class="pop" style="{D(t0 + i*.12)}"><rect x="{x}" y="{y}" width="{w}" height="34" rx="17" fill="{tint}" stroke="{col}" stroke-opacity=".35"/><text x="{x+w/2}" y="{y+22}" text-anchor="middle" font-size="13" class="mono" fill="{INK}">{esc(t)}</text></g>'
        x += w + 12
    return out
def stack(t0=6.2):
    W, H = 900, 120
    body = card(W, H) + f'<g class="rise" style="{D(t0)}"><text x="42" y="46" font-size="11" class="mono" fill="{MUTE}" letter-spacing="1.5">FOCUS</text></g>' \
        + pills(cfg["focus"], 60, t0 + .2, INK, WHITE)
    save("stack", svg(W, H, body, "Focus areas", "Focus: " + ", ".join(cfg["focus"]), ("mono",)))

# ---------- CHIPS + FOOTER ----------
def chips():
    for i, l in enumerate(cfg["links"]):
        w = int(60 + len(l["label"]) * 8.4); H = 42
        body = f'<rect x=".5" y=".5" width="{w-1}" height="{H-1}" rx="21" fill="{PAPER}" stroke="{EDGE}"/>' \
               f'<text x="22" y="26" font-size="13" class="monob" fill="{INK}">{esc(l["label"])}</text>{ARROW(w-32, 14, 11, VIOLET)}'
        save(f"chip{i+1}", svg(w, H, body, l["label"], f=("monob",)))
def footer():
    note = "preview with sample data" if prof.get("sample") or cal.get("sample") else "rendered from live GitHub data"
    body = f'<text x="450" y="22" text-anchor="middle" font-size="12" class="mono" fill="#8a8a85">refreshed {dt.date.today():%d %b %Y} - {note}</text>'
    save("footer", svg(900, 36, body, "Last refreshed", f=("mono",)))

# ---------- README ----------
def readme():
    u = cfg["username"]; L = []
    a = lambda href, img, alt, attr: f'<a href="{href}"><img src="./cards/{img}.svg" alt="{esc(alt)}" {attr}></a>'
    L.append('<div align="center">\n')
    L.append(a(f"https://github.com/{u}", "hero", f'{cfg["name"]}. {cfg["tagline"]} {cfg["role"]}.', 'width="100%"'))
    L.append('<img src="./cards/graph.svg" alt="Contribution graph for the last year" width="100%">')
    L.append('<img src="./cards/activity.svg" alt="Contributions per month, with current and longest streak" width="100%">')
    for i, t in enumerate(cfg["tiles"]): L.append(a(t["url"], f"tile{i+1}", f'{t["label"]}: {t.get("value", "")} {t["unit"]}. {t["text"]}', 'width="32.5%"'))
    for i, r in enumerate(prof["featured"][:3]): L.append(a(r["url"], f"repo{i+1}", f'Repository {r["name"]}: {r["description"]}', 'width="32.5%"'))
    L.append('<img src="./cards/stack.svg" alt="Focus areas" width="100%">')
    L.append("\n" + "\n".join(a(l["url"], f"chip{i+1}", l["label"], 'height="40"') for i, l in enumerate(cfg["links"])) + "\n")
    L.append('<img src="./cards/footer.svg" alt="Cards refreshed daily by a GitHub Action" width="100%">\n\n</div>\n')
    repos_txt = "\n".join(f'- [{r["name"]}]({r["url"]}): {r["description"]}' for r in prof["featured"][:3])
    L.append(f'<details>\n<summary>Text version</summary>\n\n**{cfg["name"]}**: {cfg["role"]}. {cfg["tagline"]}\n\nFocus: {", ".join(cfg["focus"])}. Learning now: {", ".join(cfg["learning"])}.\n\n{repos_txt}\n\n</details>\n')
    # cache-bust: version each card URL by its content hash so GitHub's image cache refreshes when a card changes
    import hashlib, re
    ver = lambda m: f'./cards/{m[1]}.svg?v={hashlib.sha1(open(f"{ROOT}/cards/{m[1]}.svg", "rb").read()).hexdigest()[:8]}'
    open(f"{ROOT}/README.md", "w", encoding="utf-8").write(re.sub(r"\./cards/([\w-]+)\.svg", ver, "\n".join(L)))

if __name__ == "__main__":
    hero(); graph(); activity(); tiles(); repos(); stack(); chips(); footer(); readme()
