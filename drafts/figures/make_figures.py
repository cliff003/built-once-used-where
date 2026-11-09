"""Figures 2-3 of the paper (Figures 1-2 until 2026-11-09, when the draw.io overview became Figure 1), as static SVG.

Inputs: level_annotation/levels.csv (labels, score weights) and the frozen R-06
output results/r06_v1cfg_v1/analyze_reuse.json (uptake by label and position).
Position bins follow analyze_reuse.py: level <= 3 is "levels 2-3", else level >= n-1
is "last two", else "middle". Run from paper-track/: python3 -I drafts/figures/make_figures.py
"""
import csv, json, os
from collections import defaultdict
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LEVELS = os.path.join(ROOT, "level_annotation", "levels.csv")
R06 = os.path.join(ROOT, "results", "r06_v1cfg_v1", "analyze_reuse.json")

COL = {"S": "#2a78d6", "V": "#eb6834", "N": "#1baf7a"}
GRAY, INK, INK2, GRID, AXIS, SURF = "#8a8984", "#1f1e1c", "#5c5b56", "#e4e3df", "#b5b4ae", "#ffffff"
BINS = [("levels 2-3", "Levels 2–3"), ("middle", "Middle"), ("last two", "Last two")]
FONT = 'font-family="Helvetica Neue, Helvetica, Arial, sans-serif"'


def weight_shares():
    rows = list(csv.DictReader(open(LEVELS, encoding="utf-8")))
    games = sorted({r["game"] for r in rows})
    acc, first = defaultdict(float), 0.0
    for g in games:
        rs = [r for r in rows if r["game"] == g]
        tot = sum(float(r["score_weight"]) for r in rs)
        for r in rs:
            lv, n, w = int(r["level"]), int(r["n_levels"]), float(r["score_weight"]) / tot
            if lv == 1:
                first += w
                continue
            b = "levels 2-3" if lv <= 3 else ("last two" if lv >= n - 1 else "middle")
            acc[(b, r["label"])] += 100 * w
    return {k: v / len(games) for k, v in acc.items()}, 100 * first / len(games), len(games)


def r06():
    a = json.load(open(R06, encoding="utf-8"))
    d = a["descriptive"]
    lab = {"S": (a["U2"]["uptake_S"], a["U2"]["S_levels"]), "N": (a["U2"]["uptake_N"], a["U2"]["N_levels"])}
    pos = {k: (v[0], v[1]) for k, v in d["uptake_by_position"].items()}
    return a, lab, pos, d


class Svg:
    def __init__(self, w, h, title, desc):
        self.w, self.h = w, h
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" role="img" {FONT}>',
                      f"<title>{escape(title)}</title><desc>{escape(desc)}</desc>",
                      f'<rect x="0" y="0" width="{w}" height="{h}" fill="{SURF}"/>']

    def text(self, x, y, s, size=11, fill=INK2, anchor="middle", weight="400"):
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{escape(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke=GRID, width=1):
        self.parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"/>')

    def bar(self, x, y, w, h, fill, tip, round_top=True):
        # 4 px rounded data end at the top, square at the baseline
        r = min(4, h / 2, w / 2) if round_top else 0
        p = (f"M{x:.1f},{y + h:.1f} L{x:.1f},{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
             f"L{x + w - r:.1f},{y:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} L{x + w:.1f},{y + h:.1f} Z")
        self.parts.append(f'<path d="{p}" fill="{fill}"><title>{escape(tip)}</title></path>')

    def axis(self, x0, x1, base, top, vmax, step, fmt="{:.0f}%"):
        v = 0
        while v <= vmax + 1e-9:
            y = base - (base - top) * v / vmax
            self.line(x0, y, x1, y, GRID if v else AXIS, 1)
            self.text(x0 - 6, y + 3.5, fmt.format(v), size=9.5, anchor="end")
            v += step

    def save(self, path):
        open(path, "w", encoding="utf-8").write("\n".join(self.parts + ["</svg>"]) + "\n")


def figure1(lab, pos, uptake_v, n_v, path):
    s = Svg(680, 250, "Figure 2. Uptake on opportunity levels in R-06",
            "Bar charts. A, by novelty label: S {:.1%} of {} levels, V {:.1%} of {}, N {:.1%} of {}. "
            "B, by level position: levels 2-3 {:.1%} of {}, middle {:.1%} of {}, last two {:.1%} of {}.".format(
                lab["S"][0], lab["S"][1], uptake_v, n_v, lab["N"][0], lab["N"][1],
                *[x for k, _ in BINS for x in pos[k]]))
    base, top = 196, 46
    panels = [(58, "A. By novelty label", [("S", "S", lab["S"][0], lab["S"][1], COL["S"]),
                                             ("V", "V", uptake_v, n_v, COL["V"]),
                                             ("N", "N", lab["N"][0], lab["N"][1], COL["N"])]),
              (400, "B. By level position", [(k, name, pos[k][0], pos[k][1], GRAY) for k, name in BINS])]
    for x0, title, bars in panels:
        x1 = x0 + 250
        s.text(x0 - 40, 22, title, size=12, fill=INK, anchor="start", weight="600")
        s.axis(x0, x1, base, top, 100, 25)
        for i, (_, name, v, n, c) in enumerate(bars):
            cx = x0 + 42 + i * 83
            h = (base - top) * v
            s.bar(cx - 22, base - h, 44, h, c, f"{name}: uptake {v:.1%} on {n} opportunity levels")
            s.text(cx, base - h - 6, f"{100 * v:.1f}%", size=10.5, fill=INK, weight="600")
            s.text(cx, base + 16, name, size=11, fill=INK)
            s.text(cx, base + 30, f"{n} levels", size=9.5)
    s.text(18, 243, "Share of opportunity levels with at least one carried call. Descriptive; the frozen test of S against N is U2.",
           size=9, anchor="start")
    s.save(path)


def figure2(ws, first, n_games, pos, path):
    tot = {k: sum(ws[(k, l)] for l in "SVN") for k, _ in BINS}
    calls = {k: round(pos[k][0] * pos[k][1]) for k, _ in BINS}
    n_calls = sum(calls.values())
    s = Svg(680, 262, "Figure 3. Where the score weight is, and where carried calls happened in R-06",
            "A: mean share of a game's score weight by position, stacked S, V, N: " +
            "; ".join(f"{name} {tot[k]:.1f}% (S {ws[(k, 'S')]:.1f}, V {ws[(k, 'V')]:.1f}, N {ws[(k, 'N')]:.1f})" for k, name in BINS) +
            f"; level 1 holds {first:.1f}%. B: share of the {n_calls} opportunity levels with a carried call: " +
            "; ".join(f"{name} {100 * calls[k] / n_calls:.1f}% ({calls[k]})" for k, name in BINS) + ".")
    base, top, vmax = 206, 62, 50
    # legend for panel A, one row under its title, kept left of panel B's axis
    lx = 18
    for lab, name in (("S", "S: known elements"), ("V", "V: new configuration"), ("N", "N: new element")):
        s.parts.append(f'<rect x="{lx}" y="35" width="10" height="10" rx="2" fill="{COL[lab]}"/>')
        s.text(lx + 14, 44, name, size=9.5, fill=INK, anchor="start")
        lx += 14 + 5.3 * len(name) + 15
    for x0, title in ((58, "A. Share of a game's score weight"), (400, f"B. Share of the {n_calls} levels with a carried call")):
        s.text(x0 - 40, 20, title, size=12, fill=INK, anchor="start", weight="600")
        s.axis(x0, x0 + 250, base, top, vmax, 10)
    for i, (k, name) in enumerate(BINS):
        cx = 58 + 42 + i * 83
        y = base
        for lab in "SVN":
            v = ws[(k, lab)]
            h = (base - top) * v / vmax
            gap = 2 if lab != "S" else 0
            s.bar(cx - 22, y - h + gap, 44, h - gap, COL[lab],
                  f"{name}, {lab}: {v:.1f}% of a game's score weight", round_top=(lab == "N"))
            if h >= 16:
                s.text(cx, y - h / 2 + 4, f"{v:.1f}", size=9, fill=SURF, weight="600")
            y -= h
        s.text(cx, y - 6, f"{tot[k]:.1f}%", size=10.5, fill=INK, weight="600")
        s.text(cx, base + 16, name, size=11, fill=INK)
        cx2 = 400 + 42 + i * 83
        v2 = 100 * calls[k] / n_calls
        h2 = (base - top) * v2 / vmax
        s.bar(cx2 - 22, base - h2, 44, h2, GRAY, f"{name}: {calls[k]} of {n_calls} levels with a carried call ({v2:.1f}%)")
        s.text(cx2, base - h2 - 6, f"{v2:.1f}%", size=10.5, fill=INK, weight="600")
        s.text(cx2, base + 16, name, size=11, fill=INK)
        s.text(cx2, base + 30, f"{calls[k]} levels", size=9.5)
    s.text(18, 254, f"A: mean over the {n_games} public games; level 1 holds the remaining {first:.1f}%. "
                    "B: R-06, both passes. Same scale in both panels.", size=9, anchor="start")
    s.save(path)


if __name__ == "__main__":
    a, lab, pos, d = r06()
    ws, first, n_games = weight_shares()
    # V opportunity levels = all opportunity levels (the position bins cover them once each) minus S and N
    n_v = sum(n for _, n in pos.values()) - lab["S"][1] - lab["N"][1]
    figure1(lab, pos, d["uptake_V"], n_v, os.path.join(HERE, "figure1_uptake.svg"))
    figure2(ws, first, n_games, pos, os.path.join(HERE, "figure2_weight_vs_calls.svg"))
    print("ok", {k: round(v, 2) for k, v in ws.items()}, round(first, 2))
