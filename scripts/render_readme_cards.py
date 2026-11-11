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
ACCENT = "#f26a1b"  # orange; INK is the black
RAMP = ["#e8e3d8", "#f9cfb2", "#f6a06a", "#f26a1b", "#14141a"]

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
GAP = {"hero": 16, "graph": 16, "activity": 16, "tile": 16, "repo": 16, "project": 16, "stack": 16}
# 3-up rows: each image is 300 wide (1/3 of 900); the 284-wide card is shifted so the
# outer edges align with full-width cards and both inner gaps are 16.
COL_W, CARD_W = 300, 284
def third(i, body): return f'<g transform="translate({i * (COL_W - CARD_W) // 2} 0)">{body}</g>'  # space below cards so they don't touch
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
    body = card(W, H) +         f'<g class="rise" style="{D(.1)}"><text x="{cx}" y="64" text-anchor="middle" font-size="12" class="mono" fill="{MUTE}" letter-spacing="2.5">{esc(cfg["role"].upper())}</text></g>'         f'<g class="rise" style="{D(.3)}"><text x="{cx}" y="156" text-anchor="middle" font-size="80" class="serif" fill="{INK}">{esc(first)} <tspan class="serifi" fill="{ACCENT}">{esc(rest)}</tspan></text></g>'         f'<g class="fade" style="{D(.6)}"><rect x="{cx-24}" y="184" width="48" height="3" rx="1.5" fill="{ACCENT}"/></g>'         f'<g class="rise" style="{D(.75)}"><text x="{cx}" y="232" text-anchor="middle" font-size="19" class="sans" fill="{INK}" fill-opacity=".85">{esc(cfg["tagline"])}</text>'         f'<text x="{lx}" y="270" font-size="13" class="mono" fill="{INK}">{esc(link)}</text>{ARROW(lx + len(link)*7.8 + 8, 260, 9, ACCENT)}</g>'
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
        f'<g class="rise" style="{D(t0)}"><text x="42" y="62" font-size="30" class="serif" fill="{INK}">Every day, <tspan class="serifi" fill="{ACCENT}">in orange</tspan></text></g>' \
        f'<g class="fade" style="{D(t0+.3)}">{"".join(labels)}</g>{"".join(cells)}'
    save("graph", svg(W, H, body, "Contribution graph", f"{fmt(total)} contributions {PERIOD}.", ("serif", "serifi", "mono")))

# ---------- ACTIVITY ----------
def activity(t0=3.0):
    W, H = 900, 276; base, maxh, bw, pitch, x0 = 226, 86, 36, 69, 50
    peak = max(mtot) or 1; bi = mtot.index(max(mtot)); bars = ""
    for i, ((yy, mm), v) in enumerate(zip(months, mtot)):
        h = max(3, v / peak * maxh); x = x0 + i * pitch; best = i == bi
        bars += f'<rect class="grow" style="{D(t0 + .2 + i*.06)}" x="{x}" y="{base-h:.1f}" width="{bw}" height="{h:.1f}" rx="5" fill="{ACCENT if best else INK}" fill-opacity="{1 if best else .85}"><title>{dt.date(yy,mm,1):%B %Y}: {v}</title></rect>' \
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
    W, H = CARD_W, 200
    for i, t in enumerate(cfg["tiles"]):
        bgc, fg = t["bg"], t["fg"]; d0 = t0 + i * .22
        if "value" in t:
            val = t["value"]; shown = esc(val)
        else:
            val = int(prof[t["metric"]]); shown = fmt(val)
        body = f'<g class="rise" style="{D(d0)}"><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="{bgc}" stroke="{t.get('stroke', bgc)}"/>' \
               f'<text x="26" y="44" font-size="11" class="monob" fill="{fg}" fill-opacity=".8" letter-spacing="2">{esc(t["label"])}</text>' \
               f'{ARROW(W-40, 32, 12, fg)}' \
               f'<text x="26" y="118" font-size="{t.get("size", 56)}" class="serif" fill="{fg}">{shown}</text>' \
               f'<text x="26" y="146" font-size="22" class="serifi" fill="{fg}" fill-opacity=".95">{esc(t["unit"])}</text>' \
               f'<text x="26" y="176" font-size="13" class="sans" fill="{fg}" fill-opacity=".8">{esc(t["text"])}</text></g>'
        save(f"tile{i+1}", svg(COL_W, H, third(i, body), f'{t["label"]}: {val} {t["unit"]}', t["text"], ("serif", "serifi", "sans", "monob")))

# ---------- PROJECTS (2 x 2) ----------
HALF_W, HALF_CARD = 450, 442  # two cards + one 16 gap = 900
def half(i, body): return f'<g transform="translate({(i % 2) * (HALF_W - HALF_CARD)} 0)">{body}</g>'
def projects(t0=5.4):
    for i, p in enumerate(cfg["projects"]):
        W, H = HALF_CARD, 184; d0 = t0 + i * .15
        desc = "".join(f'<text x="28" y="{108 + j*20}" font-size="13.5" class="sans" fill="{MUTE}">{esc(l)}</text>' for j, l in enumerate(wrap(p["text"], 56, 2)))
        body = card(W, H, WHITE) + f'<g class="rise" style="{D(d0)}">' \
            f'<text x="28" y="44" font-size="11" class="mono" fill="{ACCENT}" letter-spacing="1.5">{i+1:02d}</text>{ARROW(W-42, 32, 11, ACCENT) if p.get("url") else ""}' \
            f'<text x="28" y="78" font-size="19" class="sansb" fill="{INK}">{esc(p["name"])}</text>{desc}' \
            f'<text x="28" y="{H-26}" font-size="11.5" class="mono" fill="{INK}" fill-opacity=".7">{esc("  ·  ".join(p["tags"]))}</text></g>'
        save(f"project{i+1}", svg(HALF_W, H, half(i, body), p["name"], f'{p["name"]}: {p["text"]} Built with {", ".join(p["tags"])}.', ("sans", "sansb", "mono")))

# ---------- SKILLS: focus / stack / learning ----------
PILL = {"focus": (WHITE, INK, INK, .35), "stack": (INK, "#ffffff", INK, 1), "learning": ("#fde4d3", INK, ACCENT, .6)}
def pill_rows(items, y, t0, kind):
    fill, txt, stroke, so = PILL[kind]
    out, x = "", 42
    for i, t in enumerate(items):
        w = int(len(t) * 7.8 + 30)
        if x + w > 858: x, y = 42, y + 44
        out += f'<g class="pop" style="{D(t0 + i*.06)}"><rect x="{x}" y="{y}" width="{w}" height="32" rx="16" fill="{fill}" stroke="{stroke}" stroke-opacity="{so}"/>' \
               f'<text x="{x+w/2}" y="{y+21}" text-anchor="middle" font-size="12.5" class="mono" fill="{txt}">{esc(t)}</text></g>'
        x += w + 10
    return out, y + 32
def stack(t0=6.0):
    W = 900; body, y = "", 40
    for kind, label in (("focus", "FOCUS"), ("stack", "STACK  ·  PRACTICED"), ("learning", "CURRENTLY LEARNING")):
        body += f'<g class="rise" style="{D(t0)}"><text x="42" y="{y+6}" font-size="11" class="mono" fill="{MUTE}" letter-spacing="1.5">{label}</text></g>'
        rows, y = pill_rows(cfg[kind], y + 20, t0 + .15, kind); body += rows; y += 34; t0 += .4
    H = y + 6
    save("stack", svg(W, H, card(W, H) + body, "Focus, stack and learning",
                      f'Focus: {", ".join(cfg["focus"])}. Stack: {", ".join(cfg["stack"])}. Learning: {", ".join(cfg["learning"])}.', ("mono",)))

# ---------- CHIPS + FOOTER ----------
def chips():
    for i, l in enumerate(cfg["links"]):
        w = int(60 + len(l["label"]) * 8.4); H = 42
        body = f'<rect x=".5" y=".5" width="{w-1}" height="{H-1}" rx="21" fill="{PAPER}" stroke="{EDGE}"/>' \
               f'<text x="22" y="26" font-size="13" class="monob" fill="{INK}">{esc(l["label"])}</text>{ARROW(w-32, 14, 11, ACCENT)}'
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
    L.append("".join(a(t["url"], f"tile{i+1}", f'{t["label"]}: {t.get("value", "")} {t["unit"]}. {t["text"]}', 'width="33.33%"') for i, t in enumerate(cfg["tiles"])))
    P = cfg["projects"]; purl = lambda x: x.get("url") or f"https://github.com/{u}"
    for k in range(0, len(P), 2):
        L.append("".join(a(purl(x), f"project{k+j+1}", f'{x["name"]}: {x["text"]}', 'width="50%"') for j, x in enumerate(P[k:k+2])))
    L.append('<img src="./cards/stack.svg" alt="Focus, stack and what I am learning" width="100%">')
    L.append("\n" + "\n".join(a(l["url"], f"chip{i+1}", l["label"], 'height="40"') for i, l in enumerate(cfg["links"])) + "\n")
    L.append('<img src="./cards/footer.svg" alt="Cards refreshed daily by a GitHub Action" width="100%">\n\n</div>\n')
    about = open(f"{ROOT}/about.md", encoding="utf-8").read().strip()  # long-form profile, edit freely
    L.append(f'<details>\n<summary><b>More about me</b>: what I build, full stack, project details</summary>\n\n{about}\n\n</details>\n')
    # cache-bust: version each card URL by its content hash so GitHub's image cache refreshes when a card changes
    import hashlib, re
    ver = lambda m: f'./cards/{m[1]}.svg?v={hashlib.sha1(open(f"{ROOT}/cards/{m[1]}.svg", "rb").read()).hexdigest()[:8]}'
    open(f"{ROOT}/README.md", "w", encoding="utf-8").write(re.sub(r"\./cards/([\w-]+)\.svg", ver, "\n".join(L)))

if __name__ == "__main__":
    hero(); graph(); activity(); tiles(); projects(); stack(); chips(); footer(); readme()
