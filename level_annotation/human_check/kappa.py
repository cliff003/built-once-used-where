"""Agreement between the frozen AI labels (manual_labels.csv) and the blind human labels (labels_human.csv).
Prints the 3x3 confusion table, raw agreement, unweighted Cohen's kappa with a game-bootstrap 90% interval
(2,000 resamples, seed 20261026), and S-vs-N agreement on levels both annotators put in S or N.
Usage: python3 -I kappa.py ../manual_labels.csv labels_human.csv"""
import csv, random, sys
from collections import Counter, defaultdict
CATS = ("S", "V", "N")
ai = {(r["game"], int(r["level"])): r["label"].strip().upper() for r in csv.DictReader(open(sys.argv[1]))}
hu = {(r["game"], int(r["level"])): r["label"].strip().upper() for r in csv.DictReader(open(sys.argv[2]))}
blank = [k for k, v in hu.items() if v == ""]
bad = [k for k, v in hu.items() if v and v not in CATS]
if blank or bad:
    sys.exit(f"unfinished: {len(blank)} blank, {len(bad)} not in S/V/N: {bad[:5]}")
pairs = defaultdict(list)
for k, h in hu.items():
    pairs[k[0]].append((ai[k], h))

def kappa(ps):
    n = len(ps); po = sum(a == h for a, h in ps) / n
    ca, ch = Counter(a for a, _ in ps), Counter(h for _, h in ps)
    pe = sum(ca[c] * ch[c] for c in CATS) / n / n
    return None if pe == 1 else (po - pe) / (1 - pe)

allp = [p for g in pairs for p in pairs[g]]
print(f"{len(pairs)} games, {len(allp)} levels")
print("AI\\human " + " ".join(f"{c:>4}" for c in CATS))
for a in CATS:
    print(f"{a:>8} " + " ".join(f"{sum(1 for x, h in allp if x == a and h == c):>4}" for c in CATS))
k = kappa(allp)
rng, gs, boots = random.Random(20261026), sorted(pairs), []
for _ in range(2000):
    v = kappa([p for g in (rng.choice(gs) for _ in gs) for p in pairs[g]])
    if v is not None: boots.append(v)
boots.sort()
lo, hi = boots[int(0.05 * len(boots))], boots[int(0.95 * len(boots)) - 1]
print(f"raw agreement {sum(a == h for a, h in allp) / len(allp):.3f}; kappa {k:.3f} (90% game bootstrap {lo:.3f} to {hi:.3f})")
sn = [(a, h) for a, h in allp if a in "SN" and h in "SN"]
if sn: print(f"S-vs-N agreement where both chose S or N: {sum(a == h for a, h in sn)}/{len(sn)}")
