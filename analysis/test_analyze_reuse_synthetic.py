"""Engineering check of analyze_reuse.py on SYNTHETIC transcripts.

Writes made-up transcripts with the Kaggle Franzen-harness markers and known
reuse behaviour, runs the frozen analysis, and checks its verdicts. Not
evidence about any agent.

Usage: python3 -I test_analyze_reuse_synthetic.py <levels.csv> <scratch dir>
"""

import csv
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# probability that a level with kept functions gets a carried call, by label
SCENARIOS = {
    "selective": ({"S": 0.85, "V": 0.5, "N": 0.10}, "selective"),
    "rare": ({"S": 0.03, "V": 0.03, "N": 0.03}, "no meaningful selectivity"),
    "reverse": ({"S": 0.10, "V": 0.4, "N": 0.80}, "reverse"),
}
EXPECT_U1 = {"rare": "rarely reused"}


def snippet(code):
    return f"[TOOL CALL: python]\n<tool_call>\n<function=python>\n<parameter=code>\n{code}\n</parameter>\n</function>\n"


def transcript(game_id, labels, n, p_uptake, rng):
    # the system prompt mentions WIN in prose; it must not count as a cleared run
    out, step, kept = ["[SYSTEM PROMPT]\nYou play a game.\n- `WIN` means the whole game is solved.\n"], 0, []
    for lv in range(1, n + 1):
        out.append(f"[USER PROMPT]\nCurrent state: step {step}, level {lv}.\n")
        if kept:
            listing = ", ".join(f"{k}(x)" for k in kept)
            out.append(f"Your retained functions from earlier Python calls in this game: {listing}. "
                       "These are your previous definitions, available to call directly.\n")
        if lv in (1, 3, 5):  # new helpers appear on a few levels
            name = f"helper_l{lv}"
            out.append(snippet(f"def {name}(x):\n    return x + 1\nprint({name}(1))"))
            kept.append(name)
        if lv > 1 and kept[:-1 if lv in (3, 5) else None] and rng.random() < p_uptake.get(labels[(game_id[:4], lv)], 0):
            old = kept[0]
            out.append(snippet(f"v = {old}(2)\naction([{{'action': 'MOUSE', 'row': v, 'col': 1}}])"))
        if lv == 2:
            out.append(snippet("for x in range(:\n    pass"))  # syntax error is counted, not parsed
        out.append(snippet("action([{'action': 'MOUSE', 'row': 1, 'col': 1}])"))
        step += rng.randint(5, 40)
    # both end-of-run formats seen in real transcripts
    out.append("[action] MOUSE(row=1, col=1) -> RUN COMPLETE\n" if rng.random() < 0.5
               else f"[action] batch of 3 actions, 3 executed\nWIN lvl {n} completed False over False run_complete\n")
    return "".join(out)


def main(levels_csv, scratch):
    rows = list(csv.DictReader(open(levels_csv)))
    labels = {(r["game"], int(r["level"])): r["label"] for r in rows}
    n_levels = {r["game"]: int(r["n_levels"]) for r in rows}
    game_ids = sorted({r["game"] for r in rows})
    failures = 0
    for name, (p_uptake, expect_u2) in SCENARIOS.items():
        d = os.path.join(scratch, name)
        os.makedirs(d, exist_ok=True)
        rng = random.Random(7)
        for g in game_ids:
            for k in range(2):
                gid = f"{g}-00000000"
                with open(os.path.join(d, f"{gid}_p{k}.txt"), "w") as f:
                    f.write(transcript(gid, labels, n_levels[g], p_uptake, rng))
        out = subprocess.run([sys.executable, "-I", os.path.join(HERE, "analyze_reuse.py"), d, levels_csv],
                             capture_output=True, text=True)
        text = out.stdout + out.stderr
        u1 = next((l.rsplit("->", 1)[1].strip() for l in text.splitlines() if l.startswith("U1")), None)
        u2 = next((l.rsplit("->", 1)[1].strip() for l in text.splitlines() if l.startswith("U2")), None)
        ok = out.returncode == 0 and u2 == expect_u2 and (name not in EXPECT_U1 or u1 == EXPECT_U1[name])
        print(f"== synthetic scenario '{name}': {'OK' if ok else 'FAILED'}  (U1 -> {u1}; U2 -> {u2})")
        if not ok:
            failures += 1
            print(text)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
