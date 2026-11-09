# Marginal game-score cost of one extra action on level i, under
# level_score = min(h/a, 1)^2 and level-index weights w_i = i / sum(1..L).
# d/da (h/a)^2 = -2 h^2 / a^3; at a = k*h this is -2 / (k^3 h).
# The official scorer caps (h/a)^2 at 1.15 rather than 1; that only matters
# below about 0.93 h actions, so the k >= 1 numbers printed here are unchanged.
# Usage: python3 -I action_cost_by_level.py <environment_files dir>

import json, sys, glob, os, statistics as st
root = sys.argv[1]
games = []
for m in sorted(glob.glob(os.path.join(root, '*', '*', 'metadata.json'))):
    d = json.load(open(m))
    b = d['baseline_actions']; L = len(b); W = L * (L + 1) / 2
    games.append((d['game_id'], b, L, W))
def lam(i, h, W, k):  # points (0-100 scale) per extra action
    return 100 * (i / W) * 2 / (k ** 3 * h)
for k in (1.0, 1.5, 2.0, 3.0):
    first = [lam(1, b[0], W, k) for g, b, L, W in games]
    last = [lam(L, b[-1], W, k) for g, b, L, W in games]
    allv = [lam(i + 1, h, W, k) for g, b, L, W in games for i, h in enumerate(b)]
    print(f"k={k:>3}: per-action cost  level1 median {st.median(first):.3f}  last-level median {st.median(last):.3f}  all-levels median {st.median(allv):.3f}  (game-score pts)")
# ratio last/first per game at parity
r = [lam(L, b[-1], W, 1) / lam(1, b[0], W, 1) for g, b, L, W in games]
print("per-game ratio (last-level cost / level-1 cost) at k=1: median", round(st.median(r), 2), "min", round(min(r), 2), "max", round(max(r), 2))
# 'sunk level' effect: cost of an action at k=3 vs k=1 on the same level
print("same level, cost at k=3 vs k=1:", round(1 / 27, 3))
