"""Sensitivity analyses for involuntary clearing of kept functions (Amendment 4, section 4).

DRAFT: not frozen. It is frozen only when Amendment 4 is appended to PREREGISTRATION.md and this
file's hash is recorded in FREEZE.txt, before any confirmatory run.

Reuses the frozen parser and statistics of analyze_reuse.py unchanged (loaded by path) and adds:
  T1  U1 over *available* kept functions: eligible functions that are listed as kept at the start
      of a level after the level where they were first defined (needs no loss detection)
  T2  U2 on opportunity levels without an involuntary clearing at that level
An involuntary clearing is a '[TOOL RESULT: python]' block whose first non-empty line, or the line
right after an 'error:' line, begins with 'Tool timed out after' or 'Sandbox process' (timeout,
start failure, crashed child 'Sandbox process exited unexpectedly.', invalid or unknown response).
The sandbox result then lacks keepable_functions and the harness empties the whole kept table.
Ordinary Python errors (tracebacks) keep the table and are not counted. Restoration or collection
failures inside the sandbox and recorder errors also empty the table but leave no trace in the
transcript; they are not counted here. Where request logs exist (--requests-dir), the harness's own
retention notices are counted as an agreement check that also sees those silent clearings.

Usage:
  python3 -I analyze_reuse_clearing.py <transcript dir> <levels.csv> [--requests-dir DIR] [--json report.json]
"""

import argparse
import bisect
import csv
import glob
import gzip
import importlib.util
import json
import os
import random
import re
import statistics as st
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("analyze_reuse", os.path.join(HERE, "analyze_reuse.py"))
AR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(AR)

SECTION = re.compile(r"^\[(?P<label>[A-Z][A-Za-z :_-]*)\][ \t]*$", re.M)   # e.g. [USER PROMPT], [TOOL RESULT: python]
INFRA = re.compile(r"(?P<kind>Tool timed out after|Sandbox process)")
GONE, CLEARED = "is no longer retained", "Your retained functions were cleared"


def infra_kind(body):
    """Infrastructure failure named by a tool-result block, or None (see the module docstring)."""
    lines = body.split("\n")
    first = next((l.strip() for l in lines if l.strip()), "")
    m = INFRA.match(first)
    if m:
        return m.group("kind")
    for i in range(len(lines) - 1):
        if lines[i].strip() == "error:":
            m = INFRA.match(lines[i + 1].strip())
            if m:
                return m.group("kind")
    return None


def scan(text):
    """Snippet levels, infrastructure clearings and carried-call positions, by the frozen rules."""
    marks, level, snippet_levels = [], 1, []
    kept_at_start, snippet_seen, redefined = {}, set(), defaultdict(set)
    carried_pos = defaultdict(list)          # level -> positions of snippets with a carried call
    carried_fns = defaultdict(set)           # level -> names with a carried call (cross-check)
    for m in AR.EVENTS.finditer(text):       # same loop as analyze_reuse.parse_transcript
        if m.group("level") is not None:
            level = int(m.group("level"))
            marks.append((m.start(), level))
        elif m.group("kept") is not None:
            names = set(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\(", m.group("kept")))
            if level not in snippet_seen and level not in kept_at_start:
                kept_at_start[level] = names
        elif m.group("done") is not None:
            continue
        else:
            snippet_seen.add(level)
            snippet_levels.append(level)
            defs, calls = AR.defs_and_calls(m.group("code"))
            if defs is None:
                continue
            start = kept_at_start.get(level, set())
            for fn in defs:
                if fn in start:
                    redefined[level].add(fn)
            hits = {fn for fn in calls - defs if fn in start and fn not in redefined[level]}
            if hits:
                carried_pos[level].append(m.start())
                carried_fns[level] |= hits
    pos = [p for p, _ in marks]
    heads = list(SECTION.finditer(text))
    clearings = []                           # (level, kind, position)
    for i, h in enumerate(heads):
        if h.group("label") != "TOOL RESULT: python":
            continue
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        kind = infra_kind(text[h.end():end])
        if kind:
            j = bisect.bisect_right(pos, h.start()) - 1
            clearings.append((marks[j][1] if j >= 0 else 1, kind, h.start()))
    return snippet_levels, clearings, carried_pos, carried_fns


def message_text(m):
    c = m.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(str(p.get("text", "")) for p in c if isinstance(p, dict) and p.get("type") == "text")
    return ""


def request_events(path):
    """Retention notices in a save_request_logs file, one count per new message that carries one
    (tool messages counted once per tool_call_id)."""
    opener = gzip.open if path.endswith(".gz") else open
    ev, prev, seen_ids = Counter(), None, set()
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("event") not in (None, "request"):
                continue
            msgs = row.get("messages") or []
            if prev is None:
                new = []
            elif len(msgs) >= len(prev) and msgs[:len(prev)] == prev:
                new = msgs[len(prev):]
            else:                            # context drain: the messages after the last assistant turn
                k = len(msgs)
                while k > 0 and msgs[k - 1].get("role") != "assistant":
                    k -= 1
                new = msgs[k:]
            prev = msgs
            for m in new:
                text = message_text(m)
                if m.get("role") == "user":
                    ev["silent_cleared"] += CLEARED in text
                    continue
                if m.get("role") != "tool":
                    continue
                cid = m.get("tool_call_id")
                if cid:                          # the harness writes "" when a call has no id
                    if cid in seen_ids:          # a re-sent request repeats the same tool message
                        continue
                    seen_ids.add(cid)
                try:
                    payload = json.loads(text)
                except ValueError:
                    payload = None
                err = str(payload.get("error", "") or "") if isinstance(payload, dict) else ""
                ret = str(payload.get("function_retention", "") or "") if isinstance(payload, dict) else text
                infra = bool(INFRA.match(err.strip()))
                ev["infra_errors"] += infra
                if CLEARED in ret:
                    ev["silent_cleared"] += 1    # restoration or collection failure, recorder error
                elif GONE in ret:
                    ev["infra_cleared" if infra else "voluntary_drop"] += 1
    return ev


def load(transcript_dir, labels, n_levels, requests_dir=None):
    units = []
    for path in sorted(glob.glob(os.path.join(transcript_dir, "**", "*.txt"), recursive=True)):
        m = AR.FILE_NAME.search(os.path.basename(path))
        if not m:
            continue
        game = m.group("game_id").split("-")[0]
        if game not in n_levels:
            continue
        text = open(path, encoding="utf-8", errors="replace").read()
        p = AR.parse_transcript(text)
        snippet_levels, clearings, carried_pos, carried_fns = scan(text)
        if dict(carried_fns) != {lv: set(fns) for lv, fns in p["carried"].items() if fns}:
            raise SystemExit(f"{path}: carried-call replica disagrees with analyze_reuse.parse_transcript")
        n = n_levels[game]
        # the same eligibility and reuse sets as analyze_reuse.load
        reused = set().union(*p["carried"].values()) if p["carried"] else set()
        eligible = {fn for fn in p["kept_ever"] if fn in p["defined_at"] and p["defined_at"][fn] < p["reached"]}
        available = {fn for fn in eligible
                     if any(lv > p["defined_at"][fn] and fn in names for lv, names in p["kept_at_start"].items())}
        cleared_at, calls_at = Counter(lv for lv, _, _ in clearings), Counter(snippet_levels)
        first_clear = {}
        for lv, _, at in clearings:
            first_clear.setdefault(lv, at)
        levels = [{"level": lv, "label": labels.get((game, lv)), "kept": len(p["kept_at_start"].get(lv, set())),
                   "uptake": bool(p["carried"].get(lv)), "clearings": cleared_at[lv], "calls": calls_at[lv],
                   "uptake_before_clearing": (any(at < first_clear[lv] for at in carried_pos.get(lv, []))
                                              if lv in first_clear else None)}
                  for lv in range(2, min(p["reached"], n) + 1)]
        stem = os.path.basename(path)[:-4]
        req = None
        if requests_dir:
            cands = [os.path.join(requests_dir, stem + s) for s in ("_requests.jsonl", "_requests.jsonl.gz")]
            found = next((c for c in cands if os.path.exists(c)), None)
            req = dict(request_events(found)) if found else None
        units.append({"path": os.path.relpath(path, transcript_dir), "game": game, "n_levels": n,
                      "eligible": len(eligible), "available": len(available), "reused": len(eligible & reused),
                      "reused_available": len(available & reused), "levels": levels,
                      "clearings": [(lv, kind) for lv, kind, _ in clearings], "calls": len(snippet_levels),
                      "level1": {"calls": calls_at[1], "clearings": cleared_at[1]}, "requests": req})
    return units


def spread(xs):
    xs = sorted(xs)
    if not xs:
        return None
    q = lambda f: xs[min(len(xs) - 1, int(f * len(xs)))]
    return {"n": len(xs), "median": st.median(xs), "q25": q(0.25), "q75": q(0.75), "mean": st.mean(xs)}


def descriptive(units):
    elig = sum(u["eligible"] for u in units)
    avail = sum(u["available"] for u in units)
    kinds = Counter(k for u in units for _, k in u["clearings"])
    per_label = defaultdict(lambda: [0, 0])          # label -> [clearings, python calls]
    opp = defaultdict(lambda: [0, 0])                # label -> [opportunity levels with a clearing, all]
    before = defaultdict(lambda: [0, 0])             # label -> [uptake before first clearing, levels with clearing]
    calls_by = {"with_clearing": [], "without_clearing": []}
    for u in units:
        per_label["first"][0] += u["level1"]["clearings"]
        per_label["first"][1] += u["level1"]["calls"]
        for lv in u["levels"]:
            per_label[lv["label"]][0] += lv["clearings"]
            per_label[lv["label"]][1] += lv["calls"]
            if lv["kept"] > 0:
                opp[lv["label"]][0] += lv["clearings"] > 0
                opp[lv["label"]][1] += 1
                calls_by["with_clearing" if lv["clearings"] else "without_clearing"].append(lv["calls"])
                if lv["clearings"]:
                    before[lv["label"]][0] += bool(lv["uptake_before_clearing"])
                    before[lv["label"]][1] += 1
    out = {"survival_share": (avail / elig) if elig else None, "eligible": elig, "available": avail,
           "clearings_by_kind": dict(kinds),
           "clearings_per_100_calls": {k: (100 * c / n if n else None, c, n) for k, (c, n) in per_label.items()},
           "opportunity_levels_with_clearing": {k: (c / n if n else None, c, n) for k, (c, n) in opp.items()},
           "uptake_before_first_clearing": {k: (c / n if n else None, c, n) for k, (c, n) in before.items()},
           "calls_per_opportunity_level": {k: spread(v) for k, v in calls_by.items()}}
    with_req = [u for u in units if u["requests"] is not None]
    if with_req:
        tot = Counter()
        agree = 0
        for u in with_req:
            tot.update(u["requests"])
            agree += u["requests"].get("infra_errors", 0) == len(u["clearings"])
        out["request_log_check"] = {"units": len(with_req), "transcript_clearings": sum(len(u["clearings"]) for u in with_req),
                                    "request_counts": dict(tot), "units_agreeing_on_infra_errors": agree}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript_dir")
    ap.add_argument("levels_csv")
    ap.add_argument("--requests-dir", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    labels, n_levels = {}, {}
    for r in csv.DictReader(open(args.levels_csv)):
        labels[(r["game"], int(r["level"]))] = r["label"]
        n_levels[r["game"]] = int(r["n_levels"])
    # primary, exactly as analyze_reuse.py computes it (same units, seed and order)
    rng = random.Random(AR.SEED)
    frozen = AR.load(args.transcript_dir, labels, n_levels)
    p1, p2 = AR.u1(frozen, rng), AR.u2(frozen, rng)
    units = load(args.transcript_dir, labels, n_levels, args.requests_dir)
    print(f"transcripts: {len(units)}; python calls {sum(u['calls'] for u in units)}; "
          f"infrastructure clearings {sum(len(u['clearings']) for u in units)}")
    # sensitivity, through the frozen statistics with a fresh generator in the same order
    rng = random.Random(AR.SEED)
    t1 = AR.u1([{"game": u["game"], "reused": u["reused_available"], "eligible": u["available"]} for u in units], rng)
    t2 = AR.u2([{"game": u["game"], "levels": [lv for lv in u["levels"] if not (lv["kept"] > 0 and lv["clearings"] > 0)]}
                for u in units], rng)
    print(f"U1 primary (as analyze_reuse.py): {AR.fmt(p1)} -> {p1['verdict']}")
    print(f"T1 over available functions:      {AR.fmt(t1)} -> {t1['verdict']}")
    print(f"U2 primary (as analyze_reuse.py): {AR.fmt(p2)}  (levels S={p2['S_levels']} N={p2['N_levels']}) -> {p2['verdict']}")
    print(f"T2 without clearing levels:       {AR.fmt(t2)}  (levels S={t2['S_levels']} N={t2['N_levels']}) -> {t2['verdict']}")
    d = descriptive(units)
    print("descriptive:", json.dumps(d, default=str))
    if args.json:
        json.dump({"U1": p1, "T1": t1, "U2": p2, "T2": t2, "descriptive": d,
                   "units": [{k: v for k, v in u.items() if k != "levels"} for u in units]},
                  open(args.json, "w"), indent=1, default=str)
        print("wrote", args.json)


if __name__ == "__main__":
    main()
