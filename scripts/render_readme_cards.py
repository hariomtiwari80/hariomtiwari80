#!/usr/bin/env python3
"""Render the animated SVG cards for the GitHub profile README.

Reads   config.json, data/contributions.json, data/repos.json, assets/portrait.txt
Writes  cards/*.svg and README.md (filled in from README.template.md)

GitHub strips scripts and stylesheets from README HTML but shows SVG files
placed in <img> tags, and an SVG carries its own CSS keyframes, SMIL
animation and embedded fonts. So every block of the profile is one SVG.

    python scripts/render_readme_cards.py            # normal, animated
    STATIC=1 python scripts/render_readme_cards.py   # final frame, for screenshots
"""
import base64
import datetime as dt
import html
import json
import math
import os
import subprocess
import sys
from pathlib import Path

try:  # only used to measure text; without it widths are estimated
    from fontTools.ttLib import TTFont
except ImportError:  # pragma: no cover
    TTFont = None

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "cards"
STATIC = os.environ.get("STATIC") == "1"

# ------------------------------------------------------------------ palette
PAPER = "#F6F1E6"
CARD = "#FBF8F1"
INK = "#17150F"
MUTED = "#6E685B"
LINE = "#DDD5C3"
BLUE = "#2457E6"
RED = "#E4493B"
YELLOW = "#F1B530"
GRAPH = ["#E7E1D2", "#C3D3FB", "#88A9F6", "#4B7BEF", BLUE]  # contribution levels 0..4
BAR = "#CBC3B0"
LANG_COLORS = {
    "Java": "#B07219", "JavaScript": "#F1E05A", "TypeScript": "#3178C6", "Python": "#3572A5",
    "HTML": "#E34C26", "CSS": "#563D7C", "C++": "#F34B7D", "C": "#555555",
    "Jupyter Notebook": "#DA5B0B", "Shell": "#89E051", "Go": "#00ADD8", "Kotlin": "#A97BFF",
}


# --------------------------------------------------------------------- data
def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


CFG = load_json(ROOT / "config.json", {})
CONTRIB = load_json(ROOT / "data" / "contributions.json")
if CONTRIB is None:  # first run, nothing fetched yet: draw placeholder data
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_sample_data.py")], check=True)
    CONTRIB = load_json(ROOT / "data" / "contributions.json")
REPOS = load_json(ROOT / "data" / "repos.json", {"repos": [], "sample": False})
SAMPLE = bool(CONTRIB.get("sample"))

DAYS = [(dt.date.fromisoformat(d), int(c), int(l)) for d, c, l in CONTRIB["days"]]
GITHUB_USER = (
    CFG.get("github_user")
    or os.environ.get("GITHUB_REPOSITORY_OWNER")
    or (CONTRIB.get("user") if CONTRIB.get("user") not in (None, "", "sample") else "")
    or "YOUR_GITHUB_USERNAME"
)


# -------------------------------------------------------------------- fonts
FONT_SPECS = {
    "serif": ("fonts/serif-600.woff", "HT Serif", 600),
    "sans": ("fonts/sans-400.woff", "HT Sans", 400),
    "sansb": ("fonts/sans-600.woff", "HT Sans", 600),
}


class Fonts:
    """Embeds the subset fonts as data URIs and measures text with them."""

    def __init__(self):
        self.css = ""
        self.metrics = {}
        for key, (rel, family, weight) in FONT_SPECS.items():
            path = ROOT / rel
            if not path.exists():
                continue
            b64 = base64.b64encode(path.read_bytes()).decode()
            self.css += (
                f"@font-face{{font-family:'{family}';font-weight:{weight};"
                f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
            )
            if TTFont:
                f = TTFont(str(path))
                self.metrics[key] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)

    def measure(self, kind, text, size, spacing=0.0):
        m = self.metrics.get(kind)
        if not m:
            return len(text) * (size * 0.56 + spacing)
        cmap, hmtx, upm = m
        total = 0
        for ch in text:
            g = cmap.get(ord(ch))
            total += hmtx[g][0] if g in hmtx else upm * 0.55
        return total / upm * size + spacing * len(text)


FONTS = Fonts()


def fit(kind, text, size, maxw, spacing=0.0):
    while size > 10 and FONTS.measure(kind, text, size, spacing) > maxw:
        size -= 1
    return size


def _greedy(text, kind, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and FONTS.measure(kind, trial, size) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def wrap(text, kind, size, maxw, max_lines=None, balance=False):
    lines = _greedy(text, kind, size, maxw)
    if balance and len(lines) > 1:  # narrow the box until just before it needs another line
        w = maxw
        while w > maxw / 2 and len(_greedy(text, kind, size, w - 6)) == len(lines):
            w -= 6
        lines = _greedy(text, kind, size, w)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while len(last) > 1 and FONTS.measure(kind, last + "…", size) > maxw:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


# ---------------------------------------------------------------------- css
COMMON_CSS = """
text{font-family:'HT Sans',system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;font-weight:400}
.b{font-weight:600}
.serif{font-family:'HT Serif',Georgia,'Times New Roman',serif;font-weight:600}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace}
.cu-s{display:none}
.tb{transform-box:fill-box;transform-origin:center}
.gb{transform-box:fill-box;transform-origin:50% 100%}
.vb{transform-box:view-box;transform-origin:50% 100%}
.a{animation-fill-mode:backwards;animation-duration:.8s;animation-timing-function:cubic-bezier(.2,.8,.2,1)}
.rise{animation-name:rise}
.fade{animation-name:fade;animation-duration:.5s}
.pop{animation-name:pop;animation-duration:.45s;animation-timing-function:cubic-bezier(.3,1.5,.5,1)}
.grow{animation-name:grow;animation-duration:.9s}
.swing{animation-name:swing;animation-duration:1.15s;animation-timing-function:ease-out}
.ring{animation:ring 2.6s ease-out infinite}
.nudge{animation:nudge 1.8s ease-in-out infinite}
.dotp{animation:dotp 2s ease-in-out infinite}
""" + "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(GRAPH))

KEYFRAMES = """
@keyframes rise{from{opacity:0;transform:translateY(22px)}}
@keyframes fade{from{opacity:0}}
@keyframes pop{0%{opacity:0;transform:scale(0)}70%{transform:scale(1.25)}}
@keyframes grow{from{transform:scaleY(0)}}
@keyframes swing{0%{opacity:0;transform:translateY(70px) rotate(-7deg)}55%{opacity:1;transform:translateY(-10px) rotate(1.8deg)}78%{transform:translateY(3px) rotate(-.5deg)}100%{transform:none}}
@keyframes ring{0%{opacity:.6;transform:scale(.4)}100%{opacity:0;transform:scale(2.6)}}
@keyframes nudge{0%,100%{transform:translate(0,0)}50%{transform:translate(4px,-4px)}}
@keyframes dotp{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(1.7)}}
"""

REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}.cu{display:none}.cu-s{display:inline}.shine{display:none}}"
STATIC_CSS = "*{animation:none!important}.cu-s{display:inline}"


# ------------------------------------------------------------------ helpers
def esc(s):
    return html.escape(str(s), quote=True)


def dl(delay, dur=None):
    """Inline style that sets an animation delay (and optionally duration)."""
    d = f";animation-duration:{dur:.2f}s" if dur else ""
    return f' style="animation-delay:{delay:.2f}s{d}"'


def T(x, y, s, size=14, fill=INK, cls="", anchor=None, spacing=None, extra=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    c = f' class="{cls}"' if cls else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}"{c}{a}{ls}{extra}>{esc(s)}</text>'


def svg(w, h, body, title, desc, defs=""):
    css = FONTS.css + COMMON_CSS + (STATIC_CSS if STATIC else KEYFRAMES + REDUCED)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="{esc(title)}"><title>{esc(title)}</title><desc>{esc(desc)}</desc>'
        f"<defs>{defs}<style>{css}</style></defs>{body}</svg>"
    )


def card_bg(w, h, fill=CARD, stroke=LINE, rx=20):
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'


def sample_badge(x, y):
    if not SAMPLE:
        return ""
    return (
        f'<rect x="{x:.1f}" y="{y}" width="96" height="20" rx="10" fill="{YELLOW}"/>'
        + T(x + 48, y + 14, "SAMPLE DATA", 10, INK, "b", "middle", 1.2)
    )


def smil(markup):
    return "" if STATIC else markup


def fmt_date(d):
    return f"{d:%b} {d.day}"


def countup(x, y, value, suffix, size, fill, begin):
    """A number that counts up from 0. CSS cannot change text, so it is a stack of
    text elements shown one after another with SMIL <set>. Reduced-motion and STATIC
    show only the final number."""
    final = f"{value:,}{suffix}"
    base = f'x="{x}" y="{y}" font-size="{size}" fill="{fill}"'
    if STATIC:
        return f'<text {base} class="serif">{esc(final)}</text>'
    frames, step = 18, 0.04
    out = [f'<text {base} class="serif cu-s">{esc(final)}</text>']
    for i in range(frames):
        t = i / (frames - 1)
        v = round(value * (1 - (1 - t) ** 3))
        last = i == frames - 1
        dur = "" if last else f' dur="{step:.2f}s"'
        out.append(
            f'<text {base} class="serif cu" visibility="hidden">{esc(f"{v:,}{suffix}")}'
            f'<set attributeName="visibility" to="visible" begin="{begin + i * step:.2f}s"{dur}/></text>'
        )
    return "".join(out)


# -------------------------------------------------------------------- stats
def calc_stats(days):
    total = sum(c for _, c, _ in days)
    active = sum(1 for _, c, _ in days if c > 0)
    best_len, best_start, best_end, run, start = 0, None, None, 0, None
    for d, c, _ in days:
        if c > 0:
            if run == 0:
                start = d
            run += 1
            if run > best_len:
                best_len, best_start, best_end = run, start, d
        else:
            run = 0
    i = len(days) - 1
    if days[i][1] == 0:  # today may simply not have a contribution yet
        i -= 1
    current = 0
    while i >= 0 and days[i][1] > 0:
        current += 1
        i -= 1
    busiest = max(days, key=lambda t: t[1])
    return dict(total=total, active=active, longest=best_len, longest_start=best_start,
                longest_end=best_end, current=current, busiest=busiest)


def monthly(days):
    y, m = days[-1][0].year, days[-1][0].month
    keys = []
    for _ in range(12):
        keys.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    keys.reverse()
    sums = dict.fromkeys(keys, 0)
    for d, c, _ in days:
        if (d.year, d.month) in sums:
            sums[(d.year, d.month)] += c
    return [(k, sums[k]) for k in keys]


STATS = calc_stats(DAYS)


# --------------------------------------------------------------------- hero
def hero():
    W, LM, TEXT_W = 900, 40, 556
    first, last = CFG["first_name"], CFG["last_name"]
    nsize = fit("serif", f"{first} {last}", 80, TEXT_W)
    name_y = 70 + nsize * 0.78
    tag_lines = wrap(CFG["tagline"], "sans", 18, TEXT_W, balance=True)
    tag_y = name_y + 38
    chips_y = tag_y + 26 * (len(tag_lines) - 1) + 26
    # chips, wrapped onto rows if needed
    chips, cx, cy = [], LM, chips_y
    for i, tag in enumerate(CFG["tags"]):
        w = FONTS.measure("sansb", tag, 12.5) + 26
        if cx + w > LM + TEXT_W:
            cx, cy = LM, cy + 36
        chips.append((cx, cy, w, tag, i))
        cx += w + 8
    H = int(cy + 28 + 36)

    body = [card_bg(W, H)]
    # eyebrow
    body.append(f'<circle cx="{LM + 5}" cy="45" r="4.5" fill="{BLUE}" class="dotp tb"/>')
    body.append(T(LM + 18, 50, CFG["eyebrow"].upper(), 12, MUTED, "b a fade", spacing=1.8, extra=dl(0.1)))

    # name: the last name carries a blue shine that sweeps across it every few seconds
    first_w = FONTS.measure("serif", first + " ", nsize)
    last_w = FONTS.measure("serif", last, nsize)
    gx = LM + first_w
    sweep = smil(
        f'<animateTransform attributeName="gradientTransform" type="translate" '
        f'values="{gx - 170:.0f} 0;{gx - 170:.0f} 0;{gx + last_w + 20:.0f} 0;{gx + last_w + 20:.0f} 0" '
        f'keyTimes="0;0.4;0.72;1" dur="6s" begin="2.2s" repeatCount="indefinite"/>'
    )
    defs = (
        f'<linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="150" y2="0" '
        f'gradientTransform="translate({gx - 170:.0f} 0)">'
        f'<stop offset="0" stop-color="{INK}"/><stop offset=".38" stop-color="{INK}"/>'
        f'<stop offset=".5" stop-color="{BLUE}"/><stop offset=".62" stop-color="{INK}"/>'
        f'<stop offset="1" stop-color="{INK}"/>{sweep}</linearGradient>'
    )
    body.append(
        f'<text x="{LM}" y="{name_y:.1f}" font-size="{nsize}" class="serif a rise"{dl(0.25)}>'
        f'<tspan fill="{INK}">{esc(first)} </tspan><tspan fill="url(#shine)">{esc(last)}</tspan></text>'
    )
    for i, line in enumerate(tag_lines):
        body.append(T(LM, tag_y + 26 * i, line, 18, MUTED, "a rise", extra=dl(0.5 + i * 0.12)))

    for x, y, w, tag, i in chips:
        body.append(
            f'<g class="a pop tb"{dl(0.95 + i * 0.07)}>'
            f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="28" rx="14" fill="{PAPER}" stroke="{LINE}"/>'
            + T(x + w / 2, y + 18.5, tag, 12.5, INK, "b", "middle")
            + "</g>"
        )

    # ASCII monogram that prints in row by row, like a slow terminal.
    # Swap assets/portrait.txt for any ASCII portrait of your own.
    art_path = ROOT / "assets" / "portrait.txt"
    if art_path.exists():
        rows = [r.rstrip("\n") for r in art_path.read_text().splitlines()]
        cols = max(len(r) for r in rows)
        art_w = 244
        cell_w = art_w / cols
        pitch = cell_w * 2
        top = (H - pitch * len(rows)) / 2
        ax = W - 36 - art_w
        for i, row in enumerate(rows):
            txt = row.ljust(cols).replace(" ", " ")
            body.append(
                f'<text x="{ax:.1f}" y="{top + pitch * (i + 0.8):.1f}" font-size="{cell_w / 0.6:.2f}" '
                f'textLength="{art_w}" lengthAdjust="spacing" fill="{INK}" fill-opacity=".94" '
                f'class="mono a fade"{dl(0.7 + i * 0.07)}>{txt}</text>'
            )
    alt = f'{CFG["name"]}. {CFG["eyebrow"]}. {CFG["tagline"]}'
    return svg(W, H, "".join(body), CFG["name"], alt, defs), W, H


# -------------------------------------------------------------------- graph
def graph():
    W, X0, GAP, T0 = 900, 28, 3, 1.0
    first = DAYS[0][0]
    off = (first.weekday() + 1) % 7  # weeks start on Sunday
    ncols = (len(DAYS) + off + 6) // 7
    cell = (W - 2 * X0 + GAP) / ncols - GAP
    pitch = cell + GAP
    y0 = 96
    H = int(y0 + 7 * pitch + 62)

    body = [card_bg(W, H)]
    title_w = FONTS.measure("serif", "Contributions", 26)
    body.append(T(X0, 48, "Contributions", 26, INK, "serif a rise", extra=dl(T0 - 0.8)))
    body.append(sample_badge(X0 + title_w + 14, 32))
    body.append(T(W - X0, 46, f"{STATS['total']:,} in the last year", 14, MUTED, "a fade", "end", extra=dl(T0)))

    last_label = -9
    for idx, (d, c, lvl) in enumerate(DAYS):
        col, row = (idx + off) // 7, (idx + off) % 7
        if (d.day == 1 or (idx == 0 and d.day <= 10)) and col - last_label >= 3:
            body.append(T(X0 + col * pitch, y0 - 10, f"{d:%b}", 11, MUTED, "a fade", extra=dl(T0)))
            last_label = col
        delay = T0 + col * 0.022 + row * 0.004
        body.append(
            f'<rect x="{X0 + col * pitch:.1f}" y="{y0 + row * pitch:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
            f'rx="3" class="l{lvl} a pop tb"{dl(delay, 0.4)}/>'
        )

    # legend + last-updated stamp
    ly = H - 26
    updated = CONTRIB.get("generated", "")[:10]
    if updated:
        try:
            u = dt.date.fromisoformat(updated)
            body.append(T(X0, ly + 9, f"Updated {fmt_date(u)}, {u.year}", 11, MUTED))
        except ValueError:
            pass
    right = W - X0
    body.append(T(right, ly + 9, "More", 11, MUTED, anchor="end"))
    sx = right - FONTS.measure("sans", "More", 11) - 8 - 5 * 14 + 3
    for i in range(5):
        body.append(f'<rect x="{sx + i * 14:.1f}" y="{ly}" width="11" height="11" rx="3" class="l{i}"/>')
    body.append(T(sx - 8, ly + 9, "Less", 11, MUTED, anchor="end"))
    return svg(W, H, "".join(body), "Contributions",
               f"{STATS['total']:,} contributions in the last year, shown as a calendar graph."), W, H


# ------------------------------------------------------------------- months
def months():
    W, H, T0 = 900, 304, 2.2
    X0, X1, BASE, MAXH = 36, 584, 238, 138
    data = monthly(DAYS)
    maxv = max(v for _, v in data) or 1
    best = max(range(len(data)), key=lambda i: data[i][1])
    slot = (X1 - X0) / len(data)
    bw = 28

    body = [card_bg(W, H)]
    title_w = FONTS.measure("serif", "Activity by month", 26)
    body.append(T(36, 48, "Activity by month", 26, INK, "serif a rise", extra=dl(T0)))
    body.append(sample_badge(36 + title_w + 14, 32))
    body.append(f'<line x1="{X0}" x2="{X1}" y1="{BASE + .5}" y2="{BASE + .5}" stroke="{LINE}"/>')

    for i, ((y, m), v) in enumerate(data):
        h = max(4, v / maxv * MAXH)
        x = X0 + i * slot + (slot - bw) / 2
        color = BLUE if i == best else BAR
        body.append(
            f'<rect x="{x:.1f}" y="{BASE - h:.1f}" width="{bw}" height="{h:.1f}" rx="6" fill="{color}" '
            f'class="gb a grow"{dl(T0 + 0.2 + i * 0.06)}/>'
        )
        label = dt.date(y, m, 1).strftime("%b")
        body.append(T(x + bw / 2, BASE + 22, label, 12, INK if i == best else MUTED, "b" if i == best else "", "middle"))
        if i == best:
            body.append(T(x + bw / 2, BASE - h - 10, f"{v:,}", 22, BLUE, "serif a pop tb", "middle",
                          extra=dl(T0 + 1.3)))

    body.append(f'<line x1="616" x2="616" y1="84" y2="{H - 38}" stroke="{LINE}"/>')
    s = STATS
    span = ""
    if s["longest_start"]:
        span = f"{fmt_date(s['longest_start'])} – {fmt_date(s['longest_end'])}"
    cells = [
        (f"{s['current']}", "DAY STREAK", "up to today"),
        (f"{s['longest']}", "LONGEST STREAK", span),
        (f"{s['active']}", "ACTIVE DAYS", f"of {len(DAYS)}"),
        (f"{s['busiest'][1]}", "BUSIEST DAY", fmt_date(s["busiest"][0])),
    ]
    for i, (num, cap, hint) in enumerate(cells):
        cx = 646 + (i % 2) * 126
        cy = 124 + (i // 2) * 102
        d = dl(T0 + 0.5 + i * 0.12)
        body.append(T(cx, cy, num, 40, INK, "serif a rise", extra=d))
        body.append(T(cx, cy + 22, cap, 10.5, MUTED, "b a fade", spacing=1.2, extra=d))
        body.append(T(cx, cy + 38, hint, 11.5, MUTED, "a fade", extra=d))
    return svg(W, H, "".join(body), "Activity by month",
               f"Contributions per month over the last year. Best month: "
               f"{dt.date(*data[best][0], 1):%B %Y} with {data[best][1]:,}."), W, H


# -------------------------------------------------------------------- tiles
def tile(key, label, value, suffix, caption, footer, bg, fg, delay, sample=False):
    W, H = 300, 236
    size = fit("serif", f"{value:,}{suffix}", 88, 248)
    shine = smil(
        f'<g class="shine" transform="translate(-140 0)"><animateTransform attributeName="transform" type="translate" '
        f'values="-140 0;-140 0;460 0" keyTimes="0;0.5;1" dur="7s" begin="{delay + 1.8:.2f}s" repeatCount="indefinite"/>'
        f'<rect x="0" y="-10" width="70" height="{H + 20}" fill="url(#sg)" transform="skewX(-20)"/></g>'
    )
    defs = (
        f'<clipPath id="c"><rect width="{W}" height="{H}" rx="22"/></clipPath>'
        f'<linearGradient id="sg" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity=".32"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
        f"</linearGradient>"
    )
    inner = (
        f'<rect width="{W}" height="{H}" rx="22" fill="{bg}"/>'
        f'<g clip-path="url(#c)">{shine}</g>'
        f'<circle cx="264" cy="38" r="16" fill="none" stroke="{fg}" stroke-width="2" class="ring tb"/>'
        + T(26, 44, label, 12.5, fg, "b", spacing=2.6)
        + T(276, 47, "↗", 24, fg, "b nudge tb", "end")
        + countup(26, 146, value, suffix, size, fg, delay + 0.6)
        + T(26, 178, caption, 14.5, fg, extra=' fill-opacity=".92"')
        + f'<line x1="26" x2="274" y1="198" y2="198" stroke="{fg}" stroke-opacity=".35"/>'
        + T(26, 220, footer, 11.5, fg, "b", spacing=1.8)
        + (T(274, 220, "SAMPLE", 10, fg, "b", "end", 1.2) if sample else "")
    )
    body = f'<g class="a swing vb"{dl(delay)}>{inner}</g>'
    return svg(W, H, body, f"{label}: {value:,}{suffix} {caption}", f"{label} tile. {value:,}{suffix} {caption}.", defs)


def tiles():
    lc, cf = CFG["leetcode"], CFG["codeforces"]
    T0 = 3.3
    return {
        "build": tile("build", "BUILD", STATS["total"], "", "contributions in the last year",
                      "MY REPOSITORIES", BLUE, "#FFFFFF", T0, SAMPLE),
        "solve": tile("solve", "SOLVE", lc["rating"], "+", f"LeetCode {lc['title']}",
                      "LEETCODE PROFILE", RED, "#FFFFFF", T0 + 0.15),
        "compete": tile("compete", "COMPETE", cf["rating"], "+", f"Codeforces {cf['title']}",
                        "CODEFORCES PROFILE", YELLOW, INK, T0 + 0.3),
    }


# -------------------------------------------------------------------- repos
def coding_heading(n):
    W, H, T0 = 900, 64, 4.3
    title = "What I’m coding"
    tw = FONTS.measure("serif", title, 26)
    body = card_bg(W, H, rx=16) + T(28, 41, title, 26, INK, "serif a rise", extra=dl(T0))
    body += sample_badge(28 + tw + 14, 22)
    return svg(W, H, body, title, f"{n} featured repositories follow.")


def repo_card(i, r):
    W, H = 440, 128
    delay = 4.5 + i * 0.12
    name = r["name"]
    nsize = fit("serif", name, 22, 340)
    desc_lines = wrap(r.get("description") or "No description yet.", "sans", 13, 396, 2)
    lang = r.get("language") or ""
    parts = [card_bg(W, H, rx=18)]
    parts.append(T(22, 40, name, nsize, INK, "serif"))
    parts.append(T(W - 22, 40, "↗", 20, MUTED, "b", "end"))
    for j, line in enumerate(desc_lines):
        parts.append(T(22, 66 + 18 * j, line, 13, MUTED))
    mx = 22
    if lang:
        parts.append(f'<circle cx="{mx + 5}" cy="{H - 23}" r="5" fill="{LANG_COLORS.get(lang, MUTED)}"/>')
        parts.append(T(mx + 16, H - 19, lang, 12, INK, "b"))
        mx += 16 + FONTS.measure("sansb", lang, 12) + 18
    if r.get("stars"):
        parts.append(T(mx, H - 19, f"★ {r['stars']}", 12, MUTED, "b"))
    body = f'<g class="a rise"{dl(delay)}>{"".join(parts)}</g>'
    return svg(W, H, body, name, f"{name}. {r.get('description', '')}")


# --------------------------------------------------------------------- main
def write(name, content):
    (CARDS / name).write_text(content)
    print(f"  cards/{name:<14} {len(content.encode()) / 1024:6.1f} KB")


def main():
    CARDS.mkdir(exist_ok=True)
    for old in CARDS.glob("repo*.svg"):
        old.unlink()
    print(f"Rendering cards ({'static' if STATIC else 'animated'}) for {GITHUB_USER}" + (" [sample data]" if SAMPLE else ""))

    for name, fn in (("hero", hero), ("graph", graph), ("months", months)):
        write(f"{name}.svg", fn()[0])
    for key, content in tiles().items():
        write(f"{key}.svg", content)

    repos = (REPOS.get("repos") or [])[:4]
    block = ""
    if repos:
        write("coding.svg", coding_heading(len(repos)))
        links = []
        for i, r in enumerate(repos, 1):
            write(f"repo{i}.svg", repo_card(i - 1, r))
            alt = esc(f"{r['name']}: {r.get('description') or 'repository'}")
            links.append(f'<a href="{esc(r["url"])}"><img src="./cards/repo{i}.svg" width="49%" alt="{alt}" /></a>')
        block = (
            '<img src="./cards/coding.svg" width="100%" alt="What I’m coding" />\n\n<p>\n'
            + "\n".join(links)
            + "\n</p>"
        )

    template = ROOT / "README.template.md"
    if template.exists():
        text = template.read_text()
        for token, value in {
            "{{github_user}}": GITHUB_USER,
            "{{leetcode_url}}": CFG["leetcode"]["url"],
            "{{codeforces_url}}": CFG["codeforces"]["url"],
            "{{name}}": esc(CFG["name"]),
            "{{hero_alt}}": esc(f'{CFG["name"]}. {CFG["eyebrow"]}. {CFG["tagline"]}'),
            "{{coding_block}}": block,
        }.items():
            text = text.replace(token, value)
        (ROOT / "README.md").write_text(text)
        print("  README.md")


if __name__ == "__main__":
    main()
