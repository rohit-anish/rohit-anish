"""Render every README card as an animated SVG (paper-card theme).
STATIC=1 -> final frame only. Base styles ARE the final state, so reduced-motion also shows the final frame."""
import base64, json, math, os, textwrap, datetime as dt
from xml.sax.saxutils import escape as esc

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "cards"); os.makedirs(OUT, exist_ok=True)
STATIC = os.environ.get("STATIC") == "1"
cfg = json.load(open(f"{ROOT}/config.json"))
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
def save(name, s):
    open(f"{OUT}/{name}.svg", "w").write(s); print(f"{name:10s}{len(s)/1024:7.1f} KB")
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
months = []
for i in range(11, -1, -1):
    mm, yy = today.month - i, today.year
    while mm <= 0: mm += 12; yy -= 1
    months.append((yy, mm))
mtot = [sum(c for d, c in days if (d.year, d.month) == k) for k in months]

# ---------- HERO ----------
def hero():
    W, H = 900, 336
    first, rest = (cfg["name"].split(" ", 1) + [""])[:2]
    # sensor waveform panel (voltage + current), drawn in on load
    px, py, pw, ph = 574, 48, 278, 240; cy = py + ph / 2 + 6
    def wave(amp, ph0, yo=0):
        pts = [(px + 18 + i * 2, cy + yo - amp * math.sin((i * 2) / 38 + ph0)) for i in range(int((pw - 36) / 2) + 1)]
        return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    grid = "".join(f'<line x1="{px+14}" x2="{px+pw-14}" y1="{y}" y2="{y}" stroke="{EDGE}" stroke-dasharray="2 5"/>' for y in (cy - 70, cy, cy + 70))
    panel = f'<g class="fade" style="{D(.6)}"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="16" fill="{WHITE}" stroke="{EDGE}"/>{grid}' \
            f'<path class="draw" pathLength="1" style="{D(.9)}" d="{wave(54, 0)}" fill="none" stroke="{VIOLET}" stroke-width="3" stroke-linecap="round"/>' \
            f'<path class="draw" pathLength="1" style="{D(1.3)}" d="{wave(30, 1.1)}" fill="none" stroke="{CORAL}" stroke-width="3" stroke-linecap="round"/>' \
            f'<circle cx="{px+24}" cy="{py+26}" r="4" fill="{VIOLET}"/><circle class="pulse" cx="{px+24}" cy="{py+26}" r="4" fill="none" stroke="{VIOLET}" stroke-width="2"/>' \
            f'<text x="{px+38}" y="{py+30}" font-size="11" class="mono" fill="{MUTE}" letter-spacing="1.5">SIGNAL</text>' \
            f'<circle cx="{px+pw-88}" cy="{py+ph-24}" r="4" fill="{VIOLET}"/><text x="{px+pw-78}" y="{py+ph-20}" font-size="11" class="mono" fill="{MUTE}">V</text>' \
            f'<circle cx="{px+pw-52}" cy="{py+ph-24}" r="4" fill="{CORAL}"/><text x="{px+pw-42}" y="{py+ph-20}" font-size="11" class="mono" fill="{MUTE}">I</text></g>'
    body = card(W, H) + \
        f'<g class="rise" style="{D(.1)}"><rect x="48" y="50" width="9" height="9" rx="2" fill="{VIOLET}"/><text x="68" y="59" font-size="12" class="mono" fill="{MUTE}" letter-spacing="2">{esc(cfg["role"].upper())}</text></g>' \
        f'<g class="rise" style="{D(.25)}"><text x="46" y="146" font-size="88" class="serif" fill="{INK}">{esc(first)}</text></g>' \
        f'<g class="rise" style="{D(.45)}"><text x="46" y="228" font-size="88" class="serifi" fill="{VIOLET}">{esc(rest)}</text></g>' \
        f'<g class="rise" style="{D(.75)}"><text x="48" y="272" font-size="19" class="sans" fill="{INK}" fill-opacity=".85">{esc(cfg["tagline"])}</text>' \
        f'<text x="48" y="304" font-size="13" class="mono" fill="{INK}">{esc(cfg["link_text"])}</text>{ARROW(48+len(cfg["link_text"])*7.8+8, 294, 9, VIOLET)}</g>{panel}'
    save("hero", svg(W, H, body, f"{cfg['name']} - GitHub profile", f"{cfg['name']}. {cfg['tagline']} {cfg['role']}.", ("serif", "serifi", "sans", "mono")))

# ---------- CONTRIBUTION GRAPH ----------
def graph(t0=1.8):
    W, H = 900, 262; x0, y0, cs, pitch = 42, 108, 12, 15.4
    first = days[0][0]; mx = max(c for _, c in days) or 1
    def lvl(c):
        if c == 0: return 0
        q = c / mx; return 1 if q <= .25 else 2 if q <= .5 else 3 if q <= .75 else 4
    cells, labels, last_m = [], [], None
    for d, c in days:
        col = (d - first).days // 7; row = (d.weekday() + 1) % 7
        cells.append(f'<rect class="pop" style="{D(t0 + .1 + col * .022)}" x="{x0 + col*pitch:.1f}" y="{y0 + row*pitch:.1f}" width="{cs}" height="{cs}" rx="3" fill="{RAMP[lvl(c)]}"><title>{d}: {c}</title></rect>')
        if row == 0 and d.month != last_m and d.day <= 7:
            labels.append(f'<text x="{x0 + col*pitch:.1f}" y="{y0-10}" font-size="10" class="mono" fill="{MUTE}">{d.strftime("%b")}</text>'); last_m = d.month
    lx = 858 - 5 * 17
    leg = "".join(f'<rect x="{lx + i*17}" y="{H-36}" width="12" height="12" rx="3" fill="{c}"/>' for i, c in enumerate(RAMP))
    body = card(W, H) + \
        f'<g class="rise" style="{D(t0)}"><text x="42" y="62" font-size="32" class="serif" fill="{INK}">Every day, <tspan class="serifi" fill="{VIOLET}">in purple</tspan></text>' \
        f'<text x="858" y="56" text-anchor="end" font-size="11" class="mono" fill="{MUTE}" letter-spacing="1.5">REFRESHED DAILY</text></g>' \
        f'<g class="fade" style="{D(t0+.3)}">{"".join(labels)}</g>{"".join(cells)}' \
        f'<g class="fade" style="{D(t0+1.4)}"><text x="{lx-8}" y="{H-26}" text-anchor="end" font-size="10" class="mono" fill="{MUTE}">less</text>{leg}<text x="{lx+5*17+4}" y="{H-26}" font-size="10" class="mono" fill="{MUTE}">more</text></g>'
    save("graph", svg(W, H, body, "Contribution graph", f"{fmt(total)} contributions in the last year.", ("serif", "serifi", "mono")))

# ---------- ACTIVITY ----------
def activity(t0=3.0):
    W, H = 900, 292; base, maxh, bw, pitch, x0 = 252, 96, 28, 38, 42
    peak = max(mtot) or 1; bi = mtot.index(max(mtot)); bars = ""
    for i, ((yy, mm), v) in enumerate(zip(months, mtot)):
        h = max(4, v / peak * maxh); x = x0 + i * pitch; best = i == bi
        bars += f'<rect class="grow" style="{D(t0 + .2 + i*.06)}" x="{x}" y="{base-h:.1f}" width="{bw}" height="{h:.1f}" rx="5" fill="{VIOLET if best else INK}"><title>{dt.date(yy,mm,1):%B %Y}: {v}</title></rect>' \
                f'<text x="{x+bw/2}" y="{base+20}" text-anchor="middle" font-size="10" class="mono" fill="{MUTE}">{dt.date(yy,mm,1):%b}</text>'
        if best: bars += f'<text class="pop mono" style="{D(t0+1.2)}" x="{x+bw/2}" y="{base-h-9:.1f}" text-anchor="middle" font-size="11" fill="{VIOLET}">{fmt(v)}</text>'
    rows = [(f"{cur_streak}", f" / {best_streak}", "days: current streak, and the longest"),
            (f"{active}", f" / {len(days)}", "days with a commit"),
            (f"{busy_c}", "", f"contributions on the busiest day, {busy_d:%b} {busy_d.day}")]
    st = ""
    for i, (a, b, cap) in enumerate(rows):
        y = 100 + i * 78
        st += f'<g class="rise" style="{D(t0 + .5 + i*.18)}"><text x="590" y="{y}" font-size="40" class="serifi" fill="{INK}">{a}<tspan fill="{MUTE}" fill-opacity=".7">{b}</tspan></text>' \
              f'<text x="590" y="{y+22}" font-size="12.5" class="sans" fill="{MUTE}">{esc(cap)}</text>' + \
              (f'<line x1="590" x2="858" y1="{y+40}" y2="{y+40}" stroke="{EDGE}"/>' if i < 2 else "") + '</g>'
    body = card(W, H) + \
        f'<g class="rise" style="{D(t0)}"><text x="42" y="54" font-size="11" class="mono" fill="{MUTE}" letter-spacing="1.5">THE LAST 12 MONTHS ON GITHUB</text>' \
        f'<text x="42" y="104" font-size="48" class="serif" fill="{INK}">{fmt(total)} <tspan class="serifi">contributions</tspan></text></g>{bars}{st}'
    save("activity", svg(W, H, body, "Monthly contributions", f"{fmt(total)} contributions. Best month {dt.date(*months[bi],1):%B %Y}. Current streak {cur_streak} days.", ("serif", "serifi", "sans", "mono")))

# ---------- TILES ----------
def tiles(t0=4.2):
    W, H = 290, 230
    for i, t in enumerate(cfg["tiles"]):
        val = int(prof[t["metric"]]); bgc, fg = t["bg"], t["fg"]; d0 = t0 + i * .22
        N, dtf = 18, .045
        mk = lambda k, cls, anim: f'<text class="{cls}" style="{anim}" x="24" y="122" font-size="64" fill="{fg}">'
        frames = "".join(f'<text class="cn serif" style="animation-delay:{d0+.5+k*dtf:.3f}s;animation-duration:{dtf}s" x="24" y="122" font-size="64" fill="{fg}">{fmt(round(val*(1-(1-(k+1)/N)**3)))}</text>' for k in range(N - 1))
        final = f'<text class="cn-last serif" style="animation-delay:{d0+.5+(N-1)*dtf:.3f}s" x="24" y="122" font-size="64" fill="{fg}">{fmt(val)}</text>'
        desc = "".join(f'<text x="24" y="{176 + j*19}" font-size="13.5" class="sans" fill="{fg}" fill-opacity=".92">{esc(l)}</text>' for j, l in enumerate(wrap(t["text"], 34, 2)))
        body = f'<defs><clipPath id="c{i}"><rect width="{W}" height="{H}" rx="18"/></clipPath><linearGradient id="s{i}" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".28"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>' \
               f'<g class="tile" style="{D(d0)}"><g clip-path="url(#c{i})"><rect width="{W}" height="{H}" fill="{bgc}"/>' \
               f'<circle cx="{W-30}" cy="30" r="150" fill="{fg}" fill-opacity=".06"/>' \
               f'<rect class="shine" x="-340" y="0" width="120" height="{H}" fill="url(#s{i})" transform="skewX(-18)" style="animation-delay:{d0+2.5+i*.8:.1f}s"/></g>' \
               f'<text x="24" y="42" font-size="12" class="monob" fill="{fg}" fill-opacity=".9" letter-spacing="2">{esc(t["label"])}</text>' \
               f'<circle class="pulse" cx="{W-30}" cy="37" r="7" fill="none" stroke="{fg}" stroke-width="2" style="animation-delay:{d0+1}s"/>' \
               f'<g class="nudge" style="animation-delay:{d0}s">{ARROW(W-38, 30, 15, fg)}</g>' \
               f'{frames}{final}<text x="24" y="152" font-size="26" class="serifi" fill="{fg}" fill-opacity=".95">{esc(t["unit"])}</text>{desc}</g>'
        save(f"tile{i+1}", svg(W, H, body, f'{t["label"]}: {val} {t["unit"]}', t["text"], ("serif", "serifi", "sans", "mono", "monob")))

# ---------- HEADING + REPOS ----------
def heading(t0=5.4):
    W, H = 900, 76
    body = card(W, H) + f'<g class="rise" style="{D(t0)}"><text x="42" y="50" font-size="34" class="serif" fill="{INK}">What I\'m <tspan class="serifi" fill="{VIOLET}">building</tspan></text>' \
        f'<text x="858" y="45" text-anchor="end" font-size="11" class="mono" fill="{MUTE}" letter-spacing="1.5">FEATURED PROJECTS</text></g>'
    save("heading", svg(W, H, body, "What I'm building", f=("serif", "serifi", "mono")))
STAR = "M6 .6l1.7 3.6 3.9.5-2.9 2.7.8 3.9L6 9.3 2.5 11.3l.8-3.9L.4 4.7l3.9-.5z"
def repos(t0=5.7):
    for i, r in enumerate(prof["featured"][:3]):
        W, H = 290, 214; d0 = t0 + i * .2; col = r.get("color") or VIOLET
        desc = "".join(f'<text x="24" y="{84 + j*20}" font-size="13.5" class="sans" fill="{MUTE}">{esc(l)}</text>' for j, l in enumerate(wrap(r["description"], 34, 4)))
        lang = r["language"] or "n/a"; sx = 24 + len(lang) * 7.3 + 14
        body = card(W, H, WHITE) + f'<g class="rise" style="{D(d0)}"><circle cx="30" cy="42" r="5" fill="{col}"/>' \
            f'<text x="44" y="48" font-size="18" class="sansb" fill="{INK}">{esc(r["name"][:22])}</text>{desc}' \
            f'<text x="24" y="190" font-size="12" class="mono" fill="{MUTE}">{esc(lang)}</text>' \
            f'<g transform="translate({sx:.1f} 180)"><path d="{STAR}" fill="{SUN}"/></g><text x="{sx+17:.1f}" y="190" font-size="12" class="mono" fill="{MUTE}">{fmt(r["stars"])}</text></g>'
        save(f"repo{i+1}", svg(W, H, body, r["name"], f'{r["name"]}: {r["description"]}. {r["stars"]} stars.', ("sans", "sansb", "mono")))

# ---------- FOCUS / LEARNING ----------
def pills(items, y, t0, col, tint):
    out, x = "", 42
    for i, t in enumerate(items):
        w = int(len(t) * 8.0 + 32)
        out += f'<g class="pop" style="{D(t0 + i*.12)}"><rect x="{x}" y="{y}" width="{w}" height="34" rx="17" fill="{tint}" stroke="{col}" stroke-opacity=".55"/><text x="{x+w/2}" y="{y+22}" text-anchor="middle" font-size="13" class="mono" fill="{INK}">{esc(t)}</text></g>'
        x += w + 10
    return out
def stack(t0=6.6):
    W, H = 900, 212
    body = card(W, H) + f'<g class="rise" style="{D(t0)}"><text x="42" y="44" font-size="11" class="mono" fill="{MUTE}" letter-spacing="1.5">FOCUS</text></g>' \
        + pills(cfg["focus"], 56, t0 + .2, INK, WHITE) \
        + f'<g class="rise" style="{D(t0+.8)}"><text x="42" y="124" font-size="11" class="mono" fill="{MUTE}" letter-spacing="1.5">CURRENTLY LEARNING</text></g>' \
        + pills(cfg["learning"], 136, t0 + 1.0, VIOLET, "#ece6ff")
    save("stack", svg(W, H, body, "Focus areas and currently learning", "Focus: " + ", ".join(cfg["focus"]) + ". Learning: " + ", ".join(cfg["learning"]), ("mono",)))

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
    for i, t in enumerate(cfg["tiles"]): L.append(a(t["url"], f"tile{i+1}", f'{t["label"]}: {t["unit"]}. {t["text"]}', 'width="32.5%"'))
    L.append('<img src="./cards/heading.svg" alt="What I am building" width="100%">')
    for i, r in enumerate(prof["featured"][:3]): L.append(a(r["url"], f"repo{i+1}", f'Repository {r["name"]}: {r["description"]}', 'width="32.5%"'))
    L.append('<img src="./cards/stack.svg" alt="Focus areas and what I am learning now" width="100%">')
    L.append("\n" + "\n".join(a(l["url"], f"chip{i+1}", l["label"], 'height="40"') for i, l in enumerate(cfg["links"])) + "\n")
    L.append('<img src="./cards/footer.svg" alt="Cards refreshed daily by a GitHub Action" width="100%">\n\n</div>\n')
    repos_txt = "\n".join(f'- [{r["name"]}]({r["url"]}): {r["description"]}' for r in prof["featured"][:3])
    L.append(f'<details>\n<summary>Text version</summary>\n\n**{cfg["name"]}**: {cfg["role"]}. {cfg["tagline"]}\n\nFocus: {", ".join(cfg["focus"])}. Learning now: {", ".join(cfg["learning"])}.\n\n{repos_txt}\n\n</details>\n')
    # cache-bust: version each card URL by its content hash so GitHub's image cache refreshes when a card changes
    import hashlib, re
    ver = lambda m: f'./cards/{m[1]}.svg?v={hashlib.sha1(open(f"{ROOT}/cards/{m[1]}.svg", "rb").read()).hexdigest()[:8]}'
    open(f"{ROOT}/README.md", "w").write(re.sub(r"\./cards/([\w-]+)\.svg", ver, "\n".join(L)))

if __name__ == "__main__":
    hero(); graph(); activity(); tiles(); heading(); repos(); stack(); chips(); footer(); readme()
