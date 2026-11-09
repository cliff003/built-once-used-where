"""Figure 4 of the paper: U2 (S minus N uptake) with 90% game-bootstrap intervals, as a static SVG (2026-11-09).

Every value is read from a frozen output that the paper already reports; nothing is recomputed:
  results/r06_v1cfg_v1/analyze_reuse_clearing.json      U2 and T2 of the measured configuration (Section 7.1)
  results/s7_franzen_m2_v3/analyze_reuse_clearing.json  U2 and T2 of the parent configuration (Section 7.2)
  results/human_check_20261107/u2_ai_7games.json, u2_A.json, u2_B.json
                                                         U2 on the 7 games of the blind check (Table A2)
Run from the repository root: python3 -I drafts/figures/make_forest.py drafts/figures/figure4_u2_forest.svg
"""
import json
import os
import sys
from xml.sax.saxutils import escape

INK, INK2, GRID, AXIS, MUTED = "#1f1e1c", "#5c5b56", "#e4e3df", "#b5b4ae", "#8a8984"
FONT = 'font-family="Helvetica Neue, Helvetica, Arial, sans-serif"'
W, LEFT, RIGHT = 680, 200, 516          # plot area runs from LEFT to RIGHT pixels
LO, HI = -0.30, 0.35                    # x range


def x(v):
    return LEFT + (v - LO) / (HI - LO) * (RIGHT - LEFT)


def fmt(v):
    return ("−" if v < 0 else "+") + f"{abs(v):.3f}"


def main(out):
    r06 = json.load(open("results/r06_v1cfg_v1/analyze_reuse_clearing.json"))
    s7 = json.load(open("results/s7_franzen_m2_v3/analyze_reuse_clearing.json"))
    hc = {k: json.load(open(f"results/human_check_20261107/u2_{k}.json")) for k in ("ai_7games", "A", "B")}
    groups = [
        ("R-06 and parent configuration", INK, [
            ("R-06, U2", r06["U2"]), ("R-06, T2 (no clearing)", r06["T2"]),
            ("Parent, U2", s7["U2"]), ("Parent, T2", s7["T2"])]),
        ("7 blind-check games (no verdict)", MUTED, [
            ("AI labels", hc["ai_7games"]), ("Annotator A", hc["A"]), ("Annotator B", hc["B"])]),
    ]
    rows, y = [], 52
    for title, colour, items in groups:
        rows.append(("head", title, None, colour, y))
        y += 22
        for name, d in items:
            rows.append(("row", name, d, colour, y))
            y += 24
        y += 8
    H = y + 34
    desc = "; ".join(f"{r[1]}: {fmt(r[2]['estimate'])} [{fmt(r[2]['lo90'])}, {fmt(r[2]['hi90'])}]" for r in rows if r[0] == "row")
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" {FONT}>',
         f"<title>Figure 4. U2 with 90% intervals</title><desc>{escape(desc)}</desc>",
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>']
    top, bot = 40, y - 4
    for t in (-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3):
        p.append(f'<line x1="{x(t):.1f}" y1="{top}" x2="{x(t):.1f}" y2="{bot}" stroke="{GRID}" stroke-width="1"/>')
        p.append(f'<text x="{x(t):.1f}" y="{bot + 16}" font-size="10.5" fill="{INK2}" text-anchor="middle">{fmt(t)[:-1] if t else "0"}</text>')
    p.append(f'<line x1="{x(0):.1f}" y1="{top}" x2="{x(0):.1f}" y2="{bot}" stroke="{INK2}" stroke-width="1.2"/>')
    p.append(f'<line x1="{x(0.10):.1f}" y1="{top}" x2="{x(0.10):.1f}" y2="{bot}" stroke="{INK2}" stroke-width="1.2" stroke-dasharray="4 3"/>')
    p.append(f'<text x="{x(0.10) + 4:.1f}" y="{top - 6}" font-size="10.5" fill="{INK2}">+0.10</text>')
    p.append(f'<text x="{x(0) - 4:.1f}" y="{top - 6}" font-size="10.5" fill="{INK2}" text-anchor="end">0</text>')
    p.append(f'<text x="{(LEFT + RIGHT) / 2:.1f}" y="{bot + 31}" font-size="10.5" fill="{INK2}" text-anchor="middle">U2: uptake on S levels minus uptake on N levels</text>')
    p.append(f'<text x="{RIGHT + 12}" y="{top - 6}" font-size="10.5" fill="{INK2}">estimate [90% interval]</text>')
    for kind, name, d, colour, yy in rows:
        if kind == "head":
            p.append(f'<text x="12" y="{yy + 4}" font-size="10.5" font-weight="600" fill="{INK}">{escape(name)}</text>')
            continue
        p.append(f'<text x="24" y="{yy + 4}" font-size="11" fill="{INK}">{escape(name)}</text>')
        p.append(f'<line x1="{x(d["lo90"]):.1f}" y1="{yy}" x2="{x(d["hi90"]):.1f}" y2="{yy}" stroke="{colour}" stroke-width="2" stroke-linecap="round"/>')
        p.append(f'<circle cx="{x(d["estimate"]):.1f}" cy="{yy}" r="4.5" fill="{colour}" stroke="#ffffff" stroke-width="1.5"/>')
        p.append(f'<text x="{RIGHT + 12}" y="{yy + 4}" font-size="10.5" fill="{INK}">{fmt(d["estimate"])} [{fmt(d["lo90"])}, {fmt(d["hi90"])}]</text>')
    p.append("</svg>")
    open(out, "w", encoding="utf-8").write("\n".join(p) + "\n")
    print(out, len(rows), "rows")


if __name__ == "__main__":
    main(sys.argv[1])
