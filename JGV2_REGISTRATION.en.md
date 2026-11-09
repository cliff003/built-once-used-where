> English translation of `JGV2_REGISTRATION.md` (sha256 `19483062bbbdc4c404d6e90aa97c1eb9268a2d3c2c8a63bd0231b77f2f64d9a5`). The original, written in Chinese, is the registered version; where the two differ, the original governs. Translated on 2026-11-09.
>
> Translator's note: quotations are translated as well and marked "(translated)". Single capital letters (A–G) are the project's internal agent workstreams, for example F for independent review and G for the paper; "the coordinator" is the session that coordinated them. The tags [V], [C] and [E] mean checked by the writer, claimed by someone else (a letter after C names the source) and estimated. COLLAB-0xx are rows of the internal coordination board, and DECISIONS and RUN_REGISTER are internal logs. Paths that are not in this repository refer to the project's private working tree.

---

# JGV-2 supplementary registration (R-09): additional runs for JGV, post hoc and exploratory

- **Written**: 2026-10-29T11:55:51Z (`date -u` was run before writing), workstream G. Not changed after freezing; the hash is recorded in the `.sha256` file and in the R-09 line of RUN_REGISTER.
- **Basis**: the coordinator's decision of 10-29 about 12:0xZ (that day's line in DECISIONS): do only (c), 4 additional arms for JGV. The coordinator quoted the user's words: "if these jobs can be used in the paper, that works too" (translated).
- **Data status when written**:
  - None of these 4 new arms has been queued, and there is no output of theirs on the B200.
  - The results of R-08's three arms T1, T2 and V are known (verdict NO). So JGV-2 is an additional experiment designed after seeing R-08, and it is reported as exploratory only.
- **What does not change**:
  - R-08's pre-registration (`research/agi2/jgv/PREREG_JGV_20261029.md`, `9249b44b…a1c`) and its verdict;
  - the paper's reporting plan `paper-track/JGV_REPORTING_PLAN.md` (`dfe4096a…8df5`).
  - JGV-2's results are reported alongside R-08 and do not replace R-08's verdict.

## 1. Questions

- **Q1 (primary)**: after a few more seeds, for the same cost of one more run, does the image presentation cover more tasks than one more text run?
- **Q2 (secondary)**: when the turn limit is relaxed from 6 to 12, does the image presentation gain more than text? This hypothesis was raised after seeing R-08: 65/176 of V's episodes stopped at the 6-turn limit.
- **Q3 (descriptive)**: how much does the score vary when only the seed of the same configuration changes?

## 2. The four new arms

Each arm runs once. Tasks, model and serving parameters are the same as in R-08; the harness of the text arms is the same as T2's, and that of the image arms the same as V's.

| Arm | Presentation | seed | `max_turns` | Harness and serving |
|---|---|---|---|---|
| T3 | digits | 2 | 6 | Same as T2: original harness 0.2.2, `--language-model-only` |
| V2 | image | 1 | 6 | Same as V: the JGV patched copy, vision tower loaded, image pre-check |
| T12 | digits | 0 (harness default) | 12 | Same as T2 |
| V12 | image | 0 (harness default) | 12 | Same as V |

- **Configuration**:
  - based on `fn27_t24_64k.json` and JGV's `jgv_v.json` / `jgv_t2.json`;
  - only `seed` (T3, V2) and `max_turns` (T12, V12) change; the image arms' `grid_format` is the same as V's.
  - All other keys stay unchanged, including temperature 1.0, top_p 0.95, top_k 20, effort xhigh, episodes 2 + pass2 1, stop_agree 1, and `episode_tokens` and `task_tokens` both 64000.
  - So T12 and V12 have the same token budget as the other arms; only the number of turns no longer binds first.
- **Order**: first T3 + V2, which the primary reading needs; then T12 + V12. Each of the two GPUs runs one arm.
- **Cut-off rule**: `RUN_MIN` 180, the same as R-08.
- **Voiding rule** (worded as in R-08): an arm is void if any of the following occurs:
  - the image pre-check fails;
  - the server does not start;
  - no `submission.json` covering the 120 tasks is produced;
  - more than 5% of the 172 test inputs lack attempt_1.
- **Consequences of voiding**: a void arm is reported as it is, without further interpretation. If T3 or V2 is void, Q1 is recorded as "insufficient data"; if T12 or V12 is void, Q2 is recorded as "insufficient data".
- **Data cut-off**: if the B200 is destroyed before completion, or an arm has not finished by the 10-31 07Z watchdog, the unfinished arms are treated as void.

## 3. Readings

**Notation**:
- S(X): run X's sum of ARC task scores over the 120 tasks, with two attempts per test input.
- S(X+Y): the oracle union of the four attempts of X and Y together.
- Text arms (6 turns) 𝒯 = {T1, T2, T3}, image arms (6 turns) 𝒱 = {V, V2}.

**Primary reading D1 (Q1)**:
- **Definition**: D1 = the mean of S(t+v) over the 6 text–image pairs, minus the mean of S(t+t′) over the 3 text–text pairs.
- **Confidence interval**: task-paired bootstrap, 10,000 draws, `random.Random(20261030)`. Each draw resamples the 120 tasks only once, and every statistic is recomputed on that one set of tasks; take the 2.5% / 97.5% quantiles.
- **Verdict** (R-08's rules carried over):
  - D1 ≥ +3 and CI lower bound > 0: WORTH_PURSUING;
  - D1 ≤ 0: NO;
  - otherwise: UNDETERMINED.
  - Also report whether the CI upper bound is < +3, that is, whether "solving at least 3 more tasks" is excluded.

**Secondary reading D2 (Q2)**:
- **Definition**: D2 = [S(V12) − S(V)] − [S(T12) − S(T1)], all four arms with seed 0. Same bootstrap; the two differences are also reported separately.
- **Readings written in advance**:
  - CI lower bound > 0: read as "relaxing the limit favours images more";
  - CI upper bound < 0: read as "favours text more";
  - otherwise: read as "not separable from seed variation".

**Descriptive readings**:
- **D3 (Q3)**: S of T1, T2 and T3, with the sample standard deviation and the range of the three; S of V and V2; the 2×2 tables of "task score > 0" between each pair of text arms.
- **D4**: the mean single-run S of the image arms minus the mean single-run S of the text arms, same bootstrap.
- **D5**: the two submittable guesses, by the same rule as R-08's M3. Text–image pairs put text first; text–text pairs average the two orders. Report "text–image mean minus text–text mean", same bootstrap.
- **Run description**: for each arm, the wall-clock time, the number of calls, the number of episodes and each end status (`turns`, `tokens`, `task_tokens`, `verified`, `stopped`), prompt and completion tokens, tasks cut off by the deadline, and test inputs with missing attempts.

**Code**: `paper-track/analysis/jgv2_analyze.py`, sha256 `3b5b6a6c9d30e70925c2552dfbcbc73fd9bc87a1e7b13a860690104d43677173`.
- It implements every reading in this section except the run description, which is read from each arm's `run.json`.
- G checked it item by item on synthetic data with 3 tasks: S, D1, D2, D4, D5, the standard deviation and the range all match hand computation; it also runs without T12/V12, in which case it gives no D2.

**Command** (run after both groups have finished):

`python3 -I jgv2_analyze.py --solutions SOL --t1 <Q27> --t2 <T2> --t3 <T3> --v <V> --v2 <V2> --t12 <T12> --v12 <V12> --out jgv2_result.json`

T1, T2 and V point to R-08's three run directories, the same paths as in `run_jgv.sh`.

## 4. Reporting wording (written in advance)

- **D1**: written with the three wordings of `JGV_REPORTING_PLAN.md` §4, each noting "on these 120 tasks, in-sample, exploratory".
- **If it disagrees with R-08**: both are reported, with no causal interpretation; R-08's verdict does not change.
- **D2**: written with the three readings set in §3, without saying "the limit caused R-08's result".
- **Biases**: the biases of `JGV_REPORTING_PLAN.md` §5 still apply: eval-120 is not a held-out set; V is not purely visual; V and T1 share a seed; the tasks may have been seen in pretraining.
- **New biases**:
  - this additional experiment was designed after seeing R-08's results, and the values of T1, T2 and V were known when they entered D1;
  - T12 and T1, and V12 and V, both use seed 0, but GPU numerical non-determinism means they are not strictly paired.

## 5. Division of work and freezing

- **G**: after writing this file and the script, computes the sha256, writes the `.sha256` files and records them in R-09 of RUN_REGISTER. Neither file changes afterwards.
- **E**: rewrites the run specification following JGV's original specification, including the 4 jobs, with configurations that change only the keys of §2, and calls the command above after the second group finishes.
- **F**: checks E's diff: the configuration differences match §2 and the analysis call matches §3.
- **Queueing**: E queues after F's check.
- **Where the results go**: into §7.x and Appendix D of the paper, marked "post hoc, exploratory". R-06 is not touched; every job, grep and find excludes `ARC-AGI-3/runs/paper/`.
