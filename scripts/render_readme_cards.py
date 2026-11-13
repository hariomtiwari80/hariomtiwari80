"""Render animated SVG cards for the GitHub profile README.
Run: python scripts/render_readme_cards.py        (STATIC=1 shows the final frame, no animation)
"""
import base64, json, os, datetime as dt
from collections import defaultdict
from xml.sax.saxutils import escape as esc

# ---------- edit these ----------
NAME = ("Hariom", "Tiwari")
TAGLINE = "Building intelligent systems, scalable backends & AI-powered products."
SUBLINE = "Backend engineer · B.Tech CS, GLA University (2023–2027)"
PROFILE = "https://github.com/HariomTiwari01"
TILES = [  # label, number, suffix, caption, colour, text colour
    ("BUILD", 3, "", "flagship projects", "#2f5bea", "#ffffff"),
    ("COMPETE", 1551, "", "Codeforces rating · Specialist", "#e5484d", "#ffffff"),
    ("LEARN", 600, "+", "LeetCode problems solved", "#f5c518", "#141414"),
]
PROJECTS = [  # name, description, stack
    ("PRLens", "AI engineering intelligence platform with GitHub analytics and AI insights.", "GitHub OAuth · Groq"),
    ("CodeArc", "AI Codeforces coach: contest analytics, weak-topic detection, roadmaps.", "Analytics · AI"),
    ("SelfSevya", "Doctor appointment booking with user, doctor and admin portals.", "MERN · JWT · RBAC"),
]
CODING = "Now coding: LangGraph agents · RAG pipelines · Node.js backends"
# --------------------------------
PAPER, INK, MUTED, BLUE = "#f7f5f0", "#141414", "#6b6b66", "#2f5bea"
STATIC = os.environ.get("STATIC") == "1"
W = 900
os.makedirs("cards", exist_ok=True)

def font_css():
    out = ""
    for fam, f in (("Instrument Serif", "fonts/serif-400.woff"), ("Geist", "fonts/sans-400.woff")):
        if os.path.exists(f):
            b = base64.b64encode(open(f, "rb").read()).decode()
            out += f"@font-face{{font-family:'{fam}';src:url(data:font/woff;base64,{b})}}"
    return out
SERIF = "'Instrument Serif',Georgia,'Times New Roman',serif"
SANS = "Geist,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,Menlo,Consolas,monospace"

CSS = font_css() + f"""
text{{font-family:{SANS};fill:{INK}}}
@keyframes rise{{from{{opacity:0;transform:translateY(24px)}}to{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes pop{{0%{{opacity:0;transform:scale(0)}}70%{{transform:scale(1.25)}}100%{{opacity:1;transform:scale(1)}}}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
@keyframes tile{{0%{{opacity:0;transform:translateY(60px) rotate(-5deg)}}60%{{opacity:1;transform:translateY(-8px) rotate(1deg)}}100%{{opacity:1;transform:none}}}}
@keyframes ring{{from{{opacity:.7;transform:scale(.4)}}to{{opacity:0;transform:scale(2.6)}}}}
@keyframes nudge{{0%,100%{{transform:translateX(0)}}50%{{transform:translateX(5px)}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
.o{{transform-box:fill-box}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;opacity:1!important}}}}
"""

def A(name, delay, dur=0.7, extra=""):
    """style attribute running keyframe `name` after `delay` seconds (empty in STATIC mode)."""
    if STATIC: return ""
    return f' style="animation:{name} {dur}s {delay:.2f}s both;{extra}"'

def svg(w, h, body, defs="", title=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
            f'<style>{CSS}</style><defs>{defs}</defs>{body}</svg>')

def save(name, s):
    open(f"cards/{name}.svg", "w", encoding="utf-8").write(s)

# ---------- data ----------
try:
    days = [(dt.date.fromisoformat(d["date"]), d["count"]) for d in json.load(open("data/contributions.json"))["days"]]
except FileNotFoundError:
    days = []
days.sort()
end = days[-1][0] if days else dt.date.today()
total = sum(c for _, c in days)
by_date = dict(days)
active = sum(1 for _, c in days if c)
busiest = max(days, key=lambda x: x[1]) if days else (end, 0)
cur = lng = run = 0
for _, c in days:
    run = run + 1 if c else 0
    lng = max(lng, run)
for dd, c in reversed(days):
    if c: cur += 1
    elif dd != end: break

# ---------- hero ----------
portrait = open("fonts/portrait.txt").read().splitlines() if os.path.exists("fonts/portrait.txt") else []
body = f'<rect width="{W}" height="320" rx="14" fill="{PAPER}" stroke="#e2dfd6"/>'
grad = (f'<linearGradient id="sh" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="220" y2="0">'
        f'<stop offset="0" stop-color="{INK}"/><stop offset=".5" stop-color="{BLUE}"/><stop offset="1" stop-color="{INK}"/>'
        + ('' if STATIC else '<animateTransform attributeName="gradientTransform" type="translate" from="-300 0" to="700 0" dur="3.5s" begin="2s;+4s" repeatCount="indefinite"/>')
        + '</linearGradient>')
body += f'<g{A("rise",0.1)}><text x="48" y="150" font-family="{SERIF}" font-size="96" style="fill:{INK}">{NAME[0]}</text></g>'
body += f'<g{A("rise",0.35)}><text x="48" y="238" font-family="{SERIF}" font-size="96" style="fill:url(#sh)">{NAME[1]}</text></g>'
body += f'<text x="52" y="272" font-size="16"{A("fade",0.9)}>{esc(TAGLINE)}</text>'
body += f'<text x="52" y="296" font-size="13" style="fill:{MUTED}">{esc(SUBLINE)}</text>'
body += f'<circle cx="40" cy="46" r="4" fill="{BLUE}"' + ('/>' if STATIC else ' style="animation:pulse 2s infinite"/>')
body += f'<text x="52" y="51" font-size="13" style="fill:{MUTED}">Software engineer</text>'
n = max(len(portrait), 1)
for i, row in enumerate(portrait[:96]):
    body += f'<text xml:space="preserve" x="560" y="{14 + i * 292 / n:.1f}" font-family="{MONO}" font-size="{292 / n * 0.95:.1f}"{A("fade",0.4 + i * 0.018, 0.3)}>{esc(row)}</text>'
save("hero", svg(W, 320, body, grad, "Hariom Tiwari"))

# ---------- contribution graph (blue) ----------
G_H = 190
cs, gap = 12, 4
dow = (end.weekday() + 1) % 7
start = end - dt.timedelta(days=dow + 52 * 7)
mx = max([c for _, c in days] or [1]) or 1
pal = ["#e6e9f2", "#c7d4fb", "#8fa9f6", "#4f77ee", "#1f45c8"]
body = f'<rect width="{W}" height="{G_H}" rx="14" fill="#fff" stroke="#e2dfd6"/>'
body += f'<text x="32" y="38" font-family="{SERIF}" font-size="26">{total:,} contributions in the last year</text>'
d = start
while d <= end:
    col, row = (d - start).days // 7, (d.weekday() + 1) % 7
    c = by_date.get(d, 0)
    lvl = 0 if c == 0 else min(4, 1 + int(3.999 * c / mx))
    x, y = 32 + col * (cs + gap), 58 + row * (cs + gap)
    body += f'<rect class="o" x="{x}" y="{y}" width="{cs}" height="{cs}" rx="2.5" fill="{pal[lvl]}"' + \
            (f'/>' if STATIC else f' style="transform-origin:center;animation:pop .4s {1.4 + col * 0.03:.2f}s both"/>')
    d += dt.timedelta(days=1)
save("graph", svg(W, G_H, body, title="Contribution graph"))

# ---------- monthly chart + stats ----------
months = defaultdict(int)
for dd, c in days: months[(dd.year, dd.month)] += c
keys = sorted(months)[-12:]
vals = [months[k] for k in keys]
best = max(range(len(vals)), key=vals.__getitem__) if vals else 0
H = 330
body = f'<rect width="{W}" height="{H}" rx="14" fill="{PAPER}" stroke="#e2dfd6"/>'
body += f'<text x="32" y="40" font-family="{SERIF}" font-size="26">Contributions by month</text>'
base, bh, bw = 250, 160, 44
vmax = max(vals or [1]) or 1
for i, (k, v) in enumerate(zip(keys, vals)):
    h = max(3, bh * v / vmax); x = 40 + i * 68; y = base - h
    col = BLUE if i == best else "#c9c6bb"
    body += f'<rect class="o" x="{x}" y="{y:.1f}" width="{bw}" height="{h:.1f}" rx="4" fill="{col}"' + \
            ('/>' if STATIC else f' style="transform-origin:bottom;animation:grow .8s {2.0 + i * 0.07:.2f}s both"/>')
    body += f'<text x="{x + bw / 2}" y="{base + 20}" font-size="12" text-anchor="middle" style="fill:{MUTED}">{dt.date(k[0], k[1], 1):%b}</text>'
    if i == best:
        body += f'<text class="o" x="{x + bw / 2}" y="{y - 8:.1f}" font-size="14" font-weight="700" text-anchor="middle" style="fill:{BLUE}' + \
                ('">' if STATIC else f';transform-origin:center;animation:pop .4s 3.2s both">') + f'{v}</text>'
stats = [("current streak", f"{cur}d"), ("longest streak", f"{lng}d"), ("active days", str(active)), ("busiest day", f"{busiest[1]} · {busiest[0]:%b %d}")]
for i, (lab, val) in enumerate(stats):
    x = 32 + i * 215
    body += f'<text x="{x}" y="296" font-family="{SERIF}" font-size="28">{esc(val)}</text><text x="{x}" y="316" font-size="12" style="fill:{MUTED}">{lab}</text>'
save("months", svg(W, H, body, title="Monthly contributions"))

# ---------- tiles ----------
TW, TH = 292, 210
for idx, (label, num, suf, cap, bg, fg) in enumerate(TILES):
    t0 = 3.4 + idx * 0.25
    defs = (f'<clipPath id="c{idx}"><rect width="{TW}" height="{TH}" rx="16"/></clipPath>'
            f'<linearGradient id="g{idx}"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    inner = f'<rect width="{TW}" height="{TH}" rx="16" fill="{bg}"/>'
    inner += f'<text x="24" y="40" font-size="13" font-weight="700" letter-spacing="2" style="fill:{fg}">{label}</text>'
    if STATIC:
        inner += f'<text x="24" y="128" font-family="{SERIF}" font-size="84" style="fill:{fg}">{num:,}{suf}</text>'
    else:  # count-up: one text per value, shown briefly via SMIL <set>
        n = 18
        for i in range(n):
            v = round(num * (i + 1) / n); b = t0 + 0.4 + i * 0.05; last = i == n - 1
            inner += (f'<text x="24" y="128" font-family="{SERIF}" font-size="84" visibility="hidden" style="fill:{fg}">{v:,}{suf if last else ""}'
                      f'<set attributeName="visibility" to="visible" begin="{b:.2f}s"' + ('' if last else ' dur="0.05s"') + '/></text>')
    inner += f'<text x="24" y="168" font-size="14" style="fill:{fg}">{esc(cap)}</text>'
    inner += f'<text class="o" x="{TW - 44}" y="{TH - 24}" font-size="22" style="fill:{fg}' + ('">' if STATIC else ';animation:nudge 1.6s ease-in-out infinite">') + '→</text>'
    if not STATIC:
        inner += f'<circle class="o" cx="{TW - 36}" cy="36" r="14" fill="none" stroke="{fg}" stroke-width="2" style="transform-origin:center;animation:ring 2.4s {t0 + 1.2:.2f}s infinite both"/>'
        inner += (f'<rect x="-120" y="0" width="90" height="{TH}" fill="url(#g{idx})" transform="skewX(-18)">'
                  f'<animate attributeName="x" from="-120" to="{TW + 80}" dur="1.2s" begin="{t0 + 2:.2f}s;+5s" repeatCount="indefinite"/></rect>')
    body = f'<g class="o" clip-path="url(#c{idx})"{A("tile", t0, 1.1, "transform-origin:50% 100%")}>{inner}</g>'
    save(["build", "compete", "learn"][idx], svg(TW, TH, body, defs, label))

# ---------- projects ----------
PH = 64 + len(PROJECTS) * 84
body = f'<rect width="{W}" height="{PH}" rx="14" fill="#fff" stroke="#e2dfd6"/>'
body += f'<text x="32" y="40" font-family="{SERIF}" font-size="26">Featured projects</text>'
for i, (nm, desc, stack) in enumerate(PROJECTS):
    y = 64 + i * 84
    body += (f'<g class="o"{A("rise", 4.4 + i * 0.2)}><rect x="24" y="{y}" width="{W - 48}" height="72" rx="10" fill="{PAPER}"/>'
             f'<text x="44" y="{y + 30}" font-family="{SERIF}" font-size="28">{esc(nm)}</text>'
             f'<text x="44" y="{y + 54}" font-size="13" style="fill:{MUTED}">{esc(desc)}</text>'
             f'<text x="{W - 44}" y="{y + 30}" font-size="12" text-anchor="end" style="fill:{BLUE}">{esc(stack)}</text></g>')
save("projects", svg(W, PH, body, title="Featured projects"))

# ---------- now coding ----------
body = f'<rect width="{W}" height="64" rx="14" fill="{INK}"/><circle cx="32" cy="32" r="5" fill="#5be584"' + ('/>' if STATIC else ' style="animation:pulse 1.8s infinite"/>')
body += f'<text x="52" y="37" font-size="15" style="fill:#f7f5f0">{esc(CODING)}</text>'
save("coding", svg(W, 64, body, title="Now coding"))
print("rendered", len(os.listdir("cards")), "cards; total contributions:", total)
