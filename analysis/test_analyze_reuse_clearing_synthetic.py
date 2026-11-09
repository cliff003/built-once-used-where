"""Engineering check of analyze_reuse_clearing.py and prepare_units.py on SYNTHETIC data. Not evidence about any agent.

DRAFT: frozen together with analyze_reuse_clearing.py and prepare_units.py when Amendment 4 is appended.

Part 1: three hand-built transcripts with a made-up levels file and exact expected counts: timeouts in
        both rendering formats, a start failure, a crashed child, a traceback and a model-printed
        "Sandbox process" line that must not count, and uptake before / after the first clearing.
Part 2: 25 games x 2 passes on the frozen levels.csv in which the model takes up kept functions
        at the same rate on S and N levels, but timeouts empty the table on most N levels.
        The primary U2 must read this as 'selective'; T2, which drops the clearing levels, must not.
Part 3: a synthetic request log (append-only history, a context drain, response rows) with known
        retention notices for the request-log agreement check.
Part 4: prepare_units.py on synthetic sessions (final_generated_tokens 0, as on Kaggle; tokens in history):
        invalid (no action, or zero history tokens), cut and missing game-runs, the 20% rule over the
        expected games, two one-pass sessions, a rerun of an incomplete pass, no silent overwrite,
        no rerun of a complete pass, at most one rerun per pass, and an unexpected game.

Usage: python3 -I test_analyze_reuse_clearing_synthetic.py <levels.csv> <scratch dir>
"""

import csv
import gzip
import json
import os
import random
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "analyze_reuse_clearing.py")
KEPT = "Your retained functions from earlier Python calls in this game: {}. These are your previous definitions.\n"


def snippet(code):
    return f"[TOOL CALL: python]\n<tool_call>\n<function=python>\n<parameter=code>\n{code}\n</parameter>\n</function>\n"


def result(text):
    return f"[TOOL RESULT: python]\n{text}\n"


def prompt(step, level, kept=()):
    return f"[USER PROMPT]\nCurrent state: step {step}, level {level}.\n" + (KEPT.format(", ".join(f"{k}(x)" for k in kept)) if kept else "")


ACT = "action([{'action': 'MOUSE', 'row': 1, 'col': 1}])"

UNIT_A = "".join([
    "[SYSTEM PROMPT]\nYou play a game.\n",
    prompt(0, 1), snippet("def f(x):\n    return x\ndef g(x):\n    return x\nprint(f(1), g(1))"), result("1 1"),
    snippet(ACT), result("ok"),
    prompt(3, 1, ["f", "g"]), snippet("y = 1"), result("Tool timed out after 30s"),          # clearing at level 1
    snippet("def g(x):\n    return x\n" + ACT), result("ok"),                                # g redefined, f lost
    prompt(9, 2, ["g"]), snippet("v = g(2)\n" + ACT),
    result("Traceback (most recent call last):\n  File \"<python_tool>\", line 1, in <module>\nNameError: name 'f' is not defined"),
    prompt(15, 3, ["g"]), snippet("x = 1"), result("partial\n\nerror:\nTool timed out after 30s"),  # clearing at level 3
    snippet(ACT), result("ok"),
    prompt(20, 4), snippet("def h(x):\n    return x\n" + ACT), result("ok"),
    prompt(26, 5, ["h"]), snippet("v = h(1)\n" + ACT), result("ok"),
])
UNIT_B = "".join([
    prompt(0, 1), snippet("def f(x):\n    return x\n" + ACT), result("ok"),
    prompt(4, 1, ["f"]), snippet("z = f(1)"), result("Sandbox process could not start."),  # clearing at level 1
    snippet(ACT), result("ok"),
    prompt(8, 2), snippet(ACT), result("ok"),
])
UNIT_C = "".join([
    prompt(0, 1), snippet("def f(x):\n    return x\n" + ACT), result("ok"),
    prompt(5, 2, ["f"]), snippet("v = f(1)"), result("1"),                                    # carried call ...
    snippet("y = 1"), result("Sandbox process exited unexpectedly."),                         # ... then a crash: clearing at 2
    snippet("def f(x):\n    return x\n" + ACT), result("ok"),
    prompt(9, 3, ["f"]), snippet("z = 1"), result("Tool timed out after 30s"),                # clearing at 3 first ...
    snippet("v = f(2)\n" + ACT), result("ok"),                                                # ... then the call
    prompt(14, 4, ["f"]), snippet("print('line one'); print('Sandbox process note')"),
    result("line one\nSandbox process note"),                                                # model output: not a clearing
    snippet(ACT), result("ok"),
])
EXPECT = {
    "zz01-00000000_p0.txt": {"eligible": 3, "available": 2, "reused": 2, "reused_available": 2, "calls": 9,
                              "clearings": [[1, "Tool timed out after"], [3, "Tool timed out after"]]},
    "zz01-00000000_p1.txt": {"eligible": 1, "available": 0, "reused": 0, "reused_available": 0, "calls": 4,
                              "clearings": [[1, "Sandbox process"]]},
    "zz01-00000000_p2.txt": {"eligible": 1, "available": 1, "reused": 1, "reused_available": 1, "calls": 8,
                              "clearings": [[2, "Sandbox process"], [3, "Tool timed out after"]]},
}


def run(d, levels_csv):
    out = subprocess.run([sys.executable, "-I", SCRIPT, d, levels_csv, "--json", os.path.join(d, "report.json")],
                         capture_output=True, text=True)
    return out, (json.load(open(os.path.join(d, "report.json"))) if out.returncode == 0 else None)


def part1(scratch):
    d = os.path.join(scratch, "exact")
    os.makedirs(d, exist_ok=True)
    levels_csv = os.path.join(d, "levels_zz.csv")
    with open(levels_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["game", "level", "n_levels", "label"])
        for lv, lab in enumerate(["first", "S", "N", "V", "S", "N"], start=1):
            w.writerow(["zz01", lv, 6, lab])
    for name, text in (("zz01-00000000_p0.txt", UNIT_A), ("zz01-00000000_p1.txt", UNIT_B), ("zz01-00000000_p2.txt", UNIT_C)):
        open(os.path.join(d, name), "w").write(text)
    out, rep = run(d, levels_csv)
    if rep is None:
        print(out.stdout + out.stderr)
        return False
    ok = True
    for u in rep["units"]:
        got = {k: u[k] for k in EXPECT[u["path"]]}
        got["clearings"] = [list(c) for c in got["clearings"]]
        if got != EXPECT[u["path"]]:
            print("mismatch", u["path"], got, "expected", EXPECT[u["path"]])
            ok = False
    d = rep["descriptive"]
    opp, before = d["opportunity_levels_with_clearing"], d["uptake_before_first_clearing"]
    ok = (ok and opp.get("N", [None] * 3)[1:] == [2, 2] and opp.get("S", [None] * 3)[1:] == [1, 3]
          and opp.get("V", [None] * 3)[1:] == [0, 1]
          and before.get("S", [None] * 3)[1:] == [1, 1] and before.get("N", [None] * 3)[1:] == [0, 2])
    print(f"== part 1, exact counts: {'OK' if ok else 'FAILED'}  (opportunity levels with clearing: {opp}; "
          f"uptake before first clearing: {before})")
    return ok


def transcript(game_id, labels, n, rng, p_up=0.5, p_clear_n=0.7):
    out, step, kept = ["[SYSTEM PROMPT]\nYou play a game.\n"], 0, []
    for lv in range(1, n + 1):
        out.append(prompt(step, lv, kept))
        if lv > 1 and kept:
            if labels[(game_id[:4], lv)] == "N" and rng.random() < p_clear_n:
                out += [snippet("while True:\n    pass"), result("Tool timed out after 30s"),
                        snippet("\n".join(f"def {k}(x):\n    return x + 1" for k in kept)), result("ok")]
            elif rng.random() < p_up:
                out += [snippet(f"v = {kept[0]}(2)\n" + ACT), result("ok")]
        if lv in (1, 3, 5):
            name = f"helper_l{lv}"
            out += [snippet(f"def {name}(x):\n    return x + 1\nprint({name}(1))"), result("2")]
            kept.append(name)
        out += [snippet(ACT), result("ok")]
        step += rng.randint(5, 40)
    out.append("[action] MOUSE(row=1, col=1) -> RUN COMPLETE\n")
    return "".join(out)


def part2(levels_csv, scratch):
    rows = list(csv.DictReader(open(levels_csv)))
    labels = {(r["game"], int(r["level"])): r["label"] for r in rows}
    n_levels = {r["game"]: int(r["n_levels"]) for r in rows}
    d = os.path.join(scratch, "clearing_on_N")
    os.makedirs(d, exist_ok=True)
    rng = random.Random(11)
    for g in sorted(n_levels):
        for k in range(2):
            open(os.path.join(d, f"{g}-00000000_p{k}.txt"), "w").write(transcript(f"{g}-00000000", labels, n_levels[g], rng))
    out, rep = run(d, levels_csv)
    if rep is None:
        print(out.stdout + out.stderr)
        return False
    ok = rep["U2"]["verdict"] == "selective" and rep["T2"]["verdict"] != "selective"
    print(f"== part 2, clearing on N levels: {'OK' if ok else 'FAILED'}  (U2 -> {rep['U2']['verdict']} "
          f"{rep['U2']['estimate']:+.3f}; T2 -> {rep['T2']['verdict']} {rep['T2']['estimate']:+.3f})")
    return ok


def tool_msg(cid, stdout="", error="", retention=None):
    payload = {"stdout": stdout, "error": error}
    if retention is not None:
        payload["function_retention"] = retention
    return {"role": "tool", "tool_call_id": cid, "content": json.dumps(payload, indent=2)}


def part3(scratch):
    d = os.path.join(scratch, "requests")
    os.makedirs(d, exist_ok=True)
    levels_csv = os.path.join(scratch, "exact", "levels_zz.csv")
    open(os.path.join(d, "zz01-00000000_p0.txt"), "w").write(UNIT_A)
    sysm, user = {"role": "system", "content": "rules"}, {"role": "user", "content": "Current state: step 0, level 1."}
    asst = {"role": "assistant", "content": "", "tool_calls": [{"id": "c", "type": "function"}]}
    h = [sysm, user]
    rows = [h[:]]
    h += [asst, tool_msg("t1", "1 1", "", "Retained your function f(x) for later Python calls in this game.")]
    rows.append(h[:])
    timeout = tool_msg("t2", "", "Tool timed out after 30s", "Your previous function f is no longer retained; redefine it if needed.\n"
                                                             "Your previous function g is no longer retained; redefine it if needed.")
    h += [asst, timeout]
    rows.append(h[:])
    rows.append(h[:])                                                  # a re-sent request: nothing new
    h += [asst, tool_msg("t3", "", "", "Your retained functions were cleared: restoration failed; redefine needed functions.")]
    rows.append(h[:])
    rows.append([sysm, {"role": "user", "content": "summary 0"}, asst, timeout])   # drain that repeats t2: counted once
    h = [sysm, {"role": "user", "content": "summary of earlier turns"}, asst,
         tool_msg("t4", "", "", "Your previous function h is no longer retained; redefine it if needed.")]      # context drain
    rows.append(h[:])
    h += [asst, tool_msg("t5", "partial", "Tool timed out after 30s")]
    rows.append(h[:])
    for name in ("y", "z"):                                           # two different messages with an empty id: both count
        h += [asst, tool_msg("", "", "", f"Your previous function {name} is no longer retained; redefine it if needed.")]
        rows.append(h[:])
    with open(os.path.join(d, "zz01-00000000_p0_requests.jsonl"), "w") as f:
        for i, msgs in enumerate(rows):
            f.write(json.dumps({"event": "request", "messages": msgs}) + "\n")
            f.write(json.dumps({"event": "response", "usage": {"completion_tokens": i}}) + "\n")
    out = subprocess.run([sys.executable, "-I", SCRIPT, d, levels_csv, "--requests-dir", d, "--json", os.path.join(d, "report.json")],
                         capture_output=True, text=True)
    if out.returncode != 0:
        print(out.stdout + out.stderr)
        return False
    chk = json.load(open(os.path.join(d, "report.json")))["descriptive"].get("request_log_check", {})
    want = {"infra_errors": 2, "infra_cleared": 1, "silent_cleared": 1, "voluntary_drop": 3}
    got = {k: chk.get("request_counts", {}).get(k, 0) for k in want}
    ok = got == want and chk.get("units_agreeing_on_infra_errors") == 1 and chk.get("transcript_clearings") == 2
    print(f"== part 3, request-log check: {'OK' if ok else 'FAILED'}  ({chk})")
    return ok


def write_run(run_dir, spec, gz=(), missing=(), zero_token_history=()):
    """A synthetic Kaggle session: benchmark.json (pass-major game_runs) and transcripts.
    As on Kaggle, final_generated_tokens is 0 in every game-run; the generated tokens live in history
    (one action carrying the row's token count; no action when the count is 0)."""
    tdir = os.path.join(run_dir, "transcripts")
    os.makedirs(tdir, exist_ok=True)
    runs = []
    for k, rows in enumerate(spec):
        for g, state, tok, wall in rows:
            gid = g + "-00000000"
            stem = f"{gid}_p{k}"
            if stem in zero_token_history:
                history = [{"action": "RESET", "generated_tokens": 0, "uncached_input_tokens": 0, "wallclock_seconds": 1.0}]
            else:
                history = [{"action": "MOUSE", "generated_tokens": tok, "uncached_input_tokens": 0, "wallclock_seconds": 1.0}] if tok else []
            runs.append({"game_id": gid, "state": state, "final_generated_tokens": 0, "final_wallclock_seconds": wall,
                         "history": history})
            if stem in missing:
                continue
            if stem in gz:
                with gzip.open(os.path.join(tdir, stem + ".txt.gz"), "wt") as f:
                    f.write(f"gz {run_dir} {stem}")
            else:
                open(os.path.join(tdir, stem + ".txt"), "w").write(f"{run_dir} {stem}")
    json.dump({"n_passes": len(spec), "game_runs": runs}, open(os.path.join(run_dir, "benchmark.json"), "w"))


def prepare(out_dir, levels, runs, manifest, fresh=True):
    if fresh and os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    cmd = [sys.executable, "-I", os.path.join(HERE, "prepare_units.py"), out_dir, "--levels", levels]
    for r in runs:
        cmd += ["--run", r]
    return subprocess.run(cmd + ["--json", manifest], capture_output=True, text=True)


def part4(scratch):
    d = os.path.join(scratch, "prepare")
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    levels = os.path.join(d, "levels_zz5.csv")
    with open(levels, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["game", "level", "n_levels", "label"])
        for i in range(1, 6):
            w.writerow([f"zz0{i}", 1, 1, "first"])
    budget = 14509
    ok_all = True
    good = [("zz01", "won", 1000, 500.0), ("zz02", "gave_up", 2000, 14400.0), ("zz03", "won", 900, 300.0),
            ("zz04", "won", 800, 200.0), ("zz05", "won", 700, 100.0)]
    bad = [("zz01", "won", 1000, 500.0), ("zz02", "gave_up", 2000, 14400.0), ("zz03", "gave_up", 2000, 1000.0),
           ("zz04", "gave_up", 0, 14500.0), ("zz05", "won", 900, 300.0)]           # 2/5 not ok -> incomplete

    def check(name, cond):
        nonlocal ok_all
        print(f"== part 4{name}: {'OK' if cond else 'FAILED'}")
        ok_all &= bool(cond)

    # (a) one session, two passes: pass 0 incomplete (40%), pass 1 complete (20%: one missing transcript)
    p1 = [("zz01", "won", 1000, 600.0), ("zz02", "gave_up", 2000, 14300.0), ("zz03", "gave_up", 2000, 14250.0),
          ("zz04", "won", 800, 200.0), ("zz05", "gave_up", 3000, 14509.0)]
    write_run(os.path.join(d, "A"), [bad, p1], gz={"zz02-00000000_p1"}, missing={"zz04-00000000_p1"})
    out = prepare(os.path.join(d, "u_a"), levels, [f"{d}/A:{budget}"], os.path.join(d, "m_a.json"))
    man = json.load(open(os.path.join(d, "m_a.json"))) if out.returncode == 0 else {"units": [], "passes": {}}
    status = {u["stem"]: u["status"] for u in man["units"]}
    files = sorted(os.listdir(os.path.join(d, "u_a"))) if out.returncode == 0 else []
    check("a, one session", out.returncode == 0
          and all(status.get(k) == v for k, v in {"zz03-00000000_p0": "cut", "zz04-00000000_p0": "invalid",
                                                 "zz04-00000000_p1": "missing", "zz02-00000000_p0": "ok"}.items())
          and man["passes"]["0"]["complete"] is False and man["passes"]["1"]["complete"] is True
          and files == [f"zz0{i}-00000000_p1.txt" for i in (1, 2, 3, 5)]
          and open(os.path.join(d, "u_a", "zz02-00000000_p1.txt")).read().startswith("gz ")
          and "primary data exist (>= 2 complete passes): no" in out.stdout)
    # (b) two one-pass sessions, numbered in session order
    write_run(os.path.join(d, "S1"), [good])
    write_run(os.path.join(d, "S2"), [good])
    out = prepare(os.path.join(d, "u_b"), levels, [f"{d}/S1:{budget}", f"{d}/S2:{budget}"], os.path.join(d, "m_b.json"))
    files = sorted(os.listdir(os.path.join(d, "u_b"))) if out.returncode == 0 else []
    check("b, two sessions", out.returncode == 0
          and files == sorted(f"zz0{i}-00000000_p{k}.txt" for i in range(1, 6) for k in (0, 1))
          and open(os.path.join(d, "u_b", "zz01-00000000_p1.txt")).read().endswith("S2 zz01-00000000_p0")
          and "primary data exist (>= 2 complete passes): yes" in out.stdout)
    # (c) a rerun of an incomplete pass replaces it
    write_run(os.path.join(d, "A2"), [good, bad])
    write_run(os.path.join(d, "R"), [good])
    out = prepare(os.path.join(d, "u_c"), levels, [f"{d}/A2:{budget}", f"{d}/R:{budget}:1"], os.path.join(d, "m_c.json"))
    man = json.load(open(os.path.join(d, "m_c.json"))) if out.returncode == 0 else {"passes": {}}
    check("c, rerun replaces an incomplete pass", out.returncode == 0 and man["passes"]["1"]["complete"] is True
          and man["passes"]["1"]["run_dir"].endswith("/R") and man["passes"]["1"]["reruns"] == 1
          and "primary data exist (>= 2 complete passes): yes" in out.stdout)
    # (d) an existing destination file is an error, never a silent overwrite
    first = prepare(os.path.join(d, "u_d"), levels, [f"{d}/S1:{budget}"], os.path.join(d, "m_d.json"))
    again = prepare(os.path.join(d, "u_d"), levels, [f"{d}/S1:{budget}"], os.path.join(d, "m_d2.json"), fresh=False)
    check("d, no silent overwrite", first.returncode == 0 and again.returncode != 0 and "exists" in (again.stdout + again.stderr))
    # (e) a rerun may not replace a complete pass
    out = prepare(os.path.join(d, "u_e"), levels, [f"{d}/S1:{budget}", f"{d}/S2:{budget}", f"{d}/R:{budget}:1"], os.path.join(d, "m_e.json"))
    check("e, no rerun of a complete pass", out.returncode != 0 and "is complete" in (out.stdout + out.stderr))
    # (f) a pass may be rerun only once
    write_run(os.path.join(d, "B"), [bad])
    out = prepare(os.path.join(d, "u_f"), levels, [f"{d}/A2:{budget}", f"{d}/B:{budget}:1", f"{d}/R:{budget}:1"], os.path.join(d, "m_f.json"))
    check("f, at most one rerun per pass", out.returncode != 0 and "already rerun" in (out.stdout + out.stderr))
    # (g) completeness counts expected games: 3 of 5 played -> 2 missing -> incomplete; an unexpected game is an error
    write_run(os.path.join(d, "P"), [good[:3]])
    out = prepare(os.path.join(d, "u_g"), levels, [f"{d}/P:{budget}"], os.path.join(d, "m_g.json"))
    man = json.load(open(os.path.join(d, "m_g.json"))) if out.returncode == 0 else {"passes": {}}
    write_run(os.path.join(d, "X"), [good + [("zz06", "won", 500, 100.0)]])
    extra = prepare(os.path.join(d, "u_x"), levels, [f"{d}/X:{budget}"], os.path.join(d, "m_x.json"))
    check("g, expected game set", out.returncode == 0 and man["passes"]["0"]["complete"] is False
          and man["passes"]["0"]["not_ok"] == 2 and extra.returncode != 0 and "not in the expected set" in (extra.stdout + extra.stderr))
    # (h) a history with actions but zero generated tokens is invalid; final_generated_tokens (0 on Kaggle) is ignored
    write_run(os.path.join(d, "H"), [good], zero_token_history={"zz03-00000000_p0"})
    out = prepare(os.path.join(d, "u_h"), levels, [f"{d}/H:{budget}"], os.path.join(d, "m_h.json"))
    man = json.load(open(os.path.join(d, "m_h.json"))) if out.returncode == 0 else {"units": []}
    status = {u["stem"]: u["status"] for u in man["units"]}
    check("h, history-based invalid rule", out.returncode == 0 and status.get("zz03-00000000_p0") == "invalid"
          and status.get("zz01-00000000_p0") == "ok" and sum(v == "ok" for v in status.values()) == 4)
    return ok_all


def main(levels_csv, scratch):
    results = [part1(scratch), part2(levels_csv, scratch), part3(scratch), part4(scratch)]
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
