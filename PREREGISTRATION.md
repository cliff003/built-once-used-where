# Pre-registration: carried code across ARC-AGI-3 levels

Frozen 2026-10-25, before any ablation run. The analysis code is `analysis/analyze_ablation.py`. File hashes are recorded in `FREEZE.txt`. Any later change goes in the Amendments section at the end, with its date and reason, and must say whether any ablation data had been seen.

## 1. Question and contrast

When the agent's own Python helpers stay available across levels, do they save actions on levels that only recombine known elements, without costing actions on levels that add new elements?

| Arm | `ARC3_PERSISTENT_FUNCTIONS_SCOPE` | `ARC3_LEVEL_TRANSFER_GUIDANCE` |
|---|---|---|
| `game-g1` (Franzen default; expected submission) | game | 1 |
| `levelup-g1` | levelup | 1 |
| `game-g0` (only in the full 2×2) | game | 0 |
| `levelup-g0` (only in the full 2×2) | levelup | 0 |

- **Primary contrast (R)**: `game-g1` minus `levelup-g1`.
- **Held fixed**: every other flag equals the submission, including solved-level memory on and `ARC3_PERSISTENT_FUNCTIONS=1`. The token cap `max_generated_tokens_per_game` is also fixed, and its value is read from each run's config.
- **Data**: the 25 public games.
- **Primary model**: the submission model (Qwen, on Kaggle). Other models (Gemma 4 or Muse on PACE) are analysed separately as replications and never pooled with it.

## 2. Labels and units

- **Labels**: `level_annotation/levels.csv` as frozen here. S = only known element types, V = known elements in a new configuration, N = new element types. Level 1 has no label.
  - If a human second annotation exists before the analysis is run, it is reported as a sensitivity analysis. The primary analysis still uses these frozen labels.
- **Reached and completed**: in a run, level ℓ is *reached* if ℓ ≤ levels_completed + 1, and *completed* if ℓ ≤ levels_completed.
- **Actions**: only completed levels contribute action counts.
- **Per (game, level, arm)**: the mean of log(actions) over the passes that completed the level, and the conditional completion rate c = completed passes / reached passes.
- **Comparable pair**: a (game, level) is comparable for efficiency if at least one pass completed it in both arms, and comparable for completion if at least one pass reached it in both arms.
- **Per-level difference**: d = value(arm A) − value(arm B).
- **Game summary**: the mean of d over that game's comparable levels of the stratum.
- **Statistic**: the mean of the game summaries over games with at least one comparable level.
- **Uncertainty**: bootstrap over games (10,000 resamples, seed 20261025), with 90% percentile intervals. Their ends serve as one-sided 95% bounds for the directional rules below.

## 3. Primary predictions (claim requires both)

**P1, benefit on S levels.** Efficiency on S levels improves under `game-g1` versus `levelup-g1`: d = mean log(actions) difference < 0.
- *Supported*: upper bound < 0 and estimate ≤ log(0.90) = −0.105, i.e. at least 10% fewer actions.
- *Contradicted*: lower bound > 0.
- *Otherwise*: inconclusive.

**P2, no harm on N levels.** Efficiency on N levels is not worse by more than 10%.
- *Supported*: upper bound < log(1.10) = 0.0953.
- *Harm*: lower bound > 0.
- *Otherwise*: inconclusive.

**Data floor.** Each of P1 and P2 needs at least 8 games and 15 comparable levels in its stratum. Below that the verdict is "insufficient data" and only descriptions are reported.

## 4. Secondary analyses (reported whatever they show)

- **S1, completion.** Conditional completion difference on S and on N levels. Read "helps" for S if lower bound > 0; read "no harm" for N if lower bound > −0.10.
- **S2, score.** Official game score: mean difference over games of the per-game mean over passes. "Improves" if lower bound > 0.
- **S3, position (P3).** Among comparable S levels, regress d on relative position ℓ/L, with a game-bootstrap interval for the slope. More benefit later means slope < 0. "Supported" if upper bound < 0. This is exploratory if fewer than 10 comparable S levels sit in the last third of their games.
- **S4, tokens (P4).** Mean generated tokens per game in each arm. If the arms differ by more than 10%, flag it, and repeat P1 and P2 on actions per 1,000 tokens.
- **S5, guidance (only with the full 2×2).**
  - On N levels, carried code should hurt more without guidance: d_N(`game-g0` vs `levelup-g0`) − d_N(`game-g1` vs `levelup-g1`) > 0. "Supported" if lower bound > 0.
  - On S levels, guidance should not erase the benefit: d_S(G=1) − d_S(G=0) < log(1.10). "Supported" if upper bound < 0.0953.
- **V levels**: reported descriptively with the same statistics, and not used for any decision.

## 5. Validity and exclusions

- **Invalid run**: a run with zero generated tokens or zero turns is an infrastructure failure. It is dropped and the drop is reported.
- **Rerun rule**: if more than 20% of a pass's runs are invalid, that pass is rerun once. If it fails again, it is dropped and reported.
- **Missing or zero actions**: a completed level with zero or missing actions is dropped and reported.
- **Minimum design**: at least 2 valid passes per arm.
- **Matched conditions**: both arms of a contrast run on the same hardware type and the same model build.
- **Hidden games**: leaderboard scores are reported descriptively only, because hidden games cannot be labelled.

## 6. What the paper will say

| P1 | P2 | Wording |
|---|---|---|
| supported | supported | Carrying the agent's own helpers across levels saves actions where levels recombine known elements, without costing actions where they add new ones (public games, model X). |
| supported | harm | Carried helpers help on recombination levels but cost on novelty levels: reuse is not selective. |
| supported | inconclusive | Helps on recombination levels; the novelty-level cost could not be bounded at this sample size. |
| inconclusive | any | No detectable effect at this sample size. Never "no effect". |
| contradicted | any | Carried helpers cost actions even on recombination levels. |
| insufficient data | any | Descriptive results only. |

Optional arms (solved-level memory off, the helper check) get their own predictions added here before their first run.

## 7. Sample size and the blinded pass rule

**Planning estimate.** The source is `analysis/power_synthetic.py`: synthetic runs with an assumed noise SD of log actions per level and run, and a 10% per-level failure rate. This is not evidence about any agent.

| Noise | Passes | P1 supported, true 20% benefit on S | P1 supported, no effect | P2 supported, no harm on N |
|---|---|---|---|---|
| 0.3 | 2 / 3 / 4 | 98% / 100% / 98% | 0% / 0% / 0% | 42% / 65% / 72% |
| 0.6 | 2 / 3 / 4 | 48% / 72% / 85% | 2% / 2% / 2% | 22% / 28% / 38% |

P1 is well powered unless the noise is large. P2's 10% margin is hard to reach: even when there is no harm, "inconclusive" is the likely P2 verdict. The paper will report the P2 upper bound so readers can see which margins the data do exclude. The margin is not widened.

**Blinded pass rule.**
1. Run 2 passes per arm.
2. Run `analysis/analyze_ablation.py <root> <levels.csv> --noise-only`. It reports only within-arm noise, never a between-arm difference.
3. If the pooled within-arm SD exceeds 0.45 and compute allows, add one more pass to every arm.
4. Decide this before running the full analysis. Never add passes after seeing a between-arm result.

## Amendments

### Amendment 1 — 2026-10-25, before any ablation data existed

**Reason.** At 18:55 UTC the user decided, in the ARC-AGI-3 conversation, that the ablation runs on PACE with Muse or Gemma, not on Kaggle with the submission's Qwen model. Qwen cannot run on PACE, and the Kaggle GPU quota is shared with ARC-AGI-2. No run of any arm existed when this amendment was written.

**Changes to §1 "Primary model".** These replace that line; all decision rules are unchanged.
- **Primary ablation model**: Gemma 4 26B-A4B, served on PACE by `ARC-AGI-3/pace/serve/gemma_serve.sh`.
  - Both primary arms must use the same build. The build is recorded from each run's config.
  - If more than one Gemma 4 build has two complete primary arms, the build whose primary-arm runs finished first is primary.
- **Fallback**: if no Gemma 4 build has both primary arms with ≥ 2 valid passes by 2026-11-06 23:59 UTC, Muse Glimmer-30B becomes primary under the same rule.
- **Replications**: when both models have data, Gemma 4 is primary and Muse is a separately reported replication. Results are never pooled, and neither is chosen by its result.
- **No data**: if neither model has complete primary-arm data by 2026-11-06 23:59 UTC, the paper reports the design and the annotation only, and makes no P1/P2 claim.
- **Wording**: the paper states that the ablation model differs from the submitted model (Qwen3.8-Flash-Next). Ablation results describe the harness's reuse behaviour under the ablation model, not the submitted agent.
- **Directory layout**: runs go under `ARC-AGI-3/runs/paper/<model>/<arm>/`. The analysis is run once per model root.

### Amendment 2 — 2026-10-25, before any ablation data existed

**What the smoke run was.** The ARC-AGI-3 conversation ran a smoke test and reported it to this conversation:
- Model: Gemma 4 26B-A4B.
- Configuration: the `game-g1` configuration only. There was no `levelup-g1` run, so no between-arm information exists.
- Scope: 2 public games (ft09, sp80), 60k tokens per game.

**What it showed.** The manipulation cannot act with this model:
- 0 function definitions in 446 python calls (439 were one-line action guesses; 53 had syntax errors);
- 0 levels completed.

Without functions, `ARC3_PERSISTENT_FUNCTIONS_SCOPE` has nothing to keep. Without completed levels, there is nothing to compare, and the data floor would return "insufficient data". Amendment 1's fallback only fires on missing passes, not on valid but uninformative ones; this amendment closes that gap.

**Manipulation-check gate.** A model may serve as the ablation model only if a smoke run meets all three conditions below.
- **Smoke run**: the `game-g1` configuration only, never compared with another arm, on the public games ft09, sp80, ls20 and vc33.
- **G1**: at least 3 functions accepted for retention, in total.
- **G2**: at least one retained function is called on a level after the level where it was defined.
- **G3**: at least 2 levels completed, in total.

These thresholds only check that the manipulation can act and that completed levels exist. They carry no information about the effect, and they are fixed before any smoke run of the remaining candidates.

**Gemma 4 26B-A4B is excluded.** It failed G1 and G3 in the smoke run above, so it gets no further runs.

**Candidate order.** The first candidate to pass the gate is primary. Any later candidate that also passes is a separately reported replication; results are never pooled.
1. Qwen3.8-Flash-Next, the submitted model, on Kaggle — only if the user approves the GPU quota for it.
2. Muse Glimmer-30B on PACE.

**Deadlines.**
- The gate decision is due by 2026-10-30 23:59 UTC.
- Complete primary-arm data (at least 2 valid passes per primary arm) are due by 2026-11-06 23:59 UTC.
- If no model passes the gate, or the data are incomplete at the deadline, the paper makes no P1/P2 claim. It then reports the design, the annotation and the smoke results descriptively.

**Wording.** If Qwen becomes primary, Amendment 1's proxy-model caveat no longer applies to the primary analysis.

### Amendment 3 — 2026-10-26: new primary question, written before any confirmatory data existed

**Reason.** The ARC-AGI-3 conversation parsed the only two existing Qwen3.8-Flash-Next transcripts. Both are ft09 commit smoke runs of the submission configuration, and no other arm or game existed.
- Qwen wrote functions: 16 defined / 7 kept in one run, 23 defined / 10 kept in the other, each clearing 6/6 levels.
- Kept functions were rarely called on later levels: 0 calls in one run, 2 in the other.

With so little cross-level use, a keep-vs-clear contrast changes almost nothing, and the R ablation would most likely be uninformative. On 2026-10-26 the user decided to make the reuse behaviour itself the primary question. The ablation of §1–§3 becomes optional.

**Primary question.** In the submitted configuration, how often does the agent call functions it kept from earlier levels? And is it more likely to do so on levels that only recombine known elements (S) than on levels that add new ones (N)?

**Data.**
- Kaggle Save & Run transcripts of the submitted configuration (Franzen M2 plus the submission's patches, including solved-level memory) on the 25 public games, with at least 2 passes. Record the notebook version and the model.
- Each transcript file `<game_id>_p<k>.txt` is one (game, pass) unit.
- The two ft09 pilot transcripts in `ARC-AGI-3/kaggle/outputs/arc3-franzen-ka-v1` and `arc3-franzen-ka2-v3` were seen before this amendment. They are excluded from all confirmatory statistics.
- Deadline: complete data by 2026-11-06 23:59 UTC.

**Parsing** (frozen in `analysis/analyze_reuse.py`).
- *Snippet*: each `[TOOL CALL: python]` code block.
- *Level of a snippet*: the most recent `Current state: step N, level L.` line before it. A harness turn ends once a snippet acts, so this is exact.
- *Kept at start of level ℓ*: the names in the first "Your retained functions from earlier Python calls in this game" line seen at level ℓ before its first snippet. None means zero.
- *Carried call at level ℓ*: a call by name (AST) to a function kept at the start of ℓ that has not been redefined at level ℓ up to and including that snippet.
- *Reached*: the highest level seen in `Current state` lines.
- *Completed*: reached − 1, or every level when the run ends cleared. A cleared run shows `-> RUN COMPLETE` after a single action, or a line starting `WIN lvl N` after a batch; prose mentioning WIN in the system prompt does not count.
- *Parser validation*: on the two already-seen pilot transcripts, the parser reproduces the counts reported independently by the ARC-AGI-3 conversation:
  - functions defined: 16 and 23;
  - functions kept: 7 and 10;
  - functions with a carried call: 0 and 2;
  - levels cleared: 6 and 6.

  No confirmatory data was used.
- *Opportunity level*: a reached level ℓ ≥ 2 with at least one function kept at its start.
- *Uptake*: an opportunity level with at least one carried call.

**Primary measures.** Both use a game bootstrap (10,000 resamples, seed 20261025) and 90% percentile intervals.
- **U1, reuse share.** A kept function is eligible if a level after the one where it was first defined was reached. A kept function counts as reused if it gets a carried call on any later level. The per-game share is Σ reused / Σ eligible over passes. The statistic is the mean over games with at least one eligible function.
  - *Rarely reused*: upper bound < 0.25.
  - *Commonly reused*: lower bound > 0.50.
  - *Otherwise*: intermediate.
- **U2, selectivity.** The uptake rate on S opportunity levels minus the uptake rate on N opportunity levels, each pooled over levels and passes, with games resampled as clusters.
  - *Reverse*: upper bound < 0.
  - *Selective*: lower bound > 0.
  - *No meaningful selectivity*: upper bound < 0.10, i.e. a 10-point S advantage is excluded.
  - *Otherwise*: inconclusive.
- **Data floors.**
  - U1 needs at least 8 games with eligible functions.
  - U2 needs at least 8 games contributing opportunity levels, and at least 15 opportunity levels in each of S and N.
  - Below a floor the verdict is "insufficient data".

**Descriptive only** (no verdicts):
- the opportunity rate;
- uptake on V levels, and by position (levels 2–3, middle, last two);
- revised reuse (a kept function redefined at a later level);
- for S levels, approximate actions per completed level with and without uptake, from the step counters (confounded);
- the Amendment 2 gate counts G1–G3 on ft09, sp80, ls20 and vc33 from these runs, which decide whether the optional ablation is eligible.

**Claim boundary.** The measurement is observational. It cannot show that reuse improves efficiency; only the optional ablation could.

**What the paper will say**

| U1 | U2 | Wording |
|---|---|---|
| rarely reused | no meaningful selectivity or inconclusive | The agent writes reusable code but seldom carries it forward, and not more where levels recombine known elements: reuse opportunities, concentrated in the late high-weight levels, go unused. |
| rarely reused | selective | Reuse is rare but concentrated where it fits. |
| intermediate or commonly reused | selective | The agent carries its own tools forward, selectively. |
| any | reverse | The agent reuses more where levels add new elements, the opposite of what fits. |
| any | inconclusive | State the share and the interval; no selectivity claim. |
| insufficient data | insufficient data | Descriptive results only. |

**The ablation becomes optional.** If it is run, §3's rules and Amendment 2's gate apply unchanged, as a secondary analysis.

### Amendment 4 — 2026-10-27: seen-data list, timeout clearing of kept functions, measured configuration, data source, parent-configuration replication

**Reason.** Amendment 3 left five things open, and this amendment settles them before any confirmatory data exist: which runs and statistics other workstreams had already seen; how a known harness behaviour, the emptying of the kept table after a sandbox timeout, bears on the frozen measures; what exactly "the submitted configuration" is; where the data come from, after the user paused PACE (2026-10-27 02:15 UTC) and approved a Kaggle run (2026-10-27 03:20 UTC); and a zero-compute replication on the parent configuration whose transcripts already exist. The amendment was reviewed by an independent workstream before freezing (`research/review/REVIEW_PAPER_AMENDMENT4_20261027.md`).

**Data status when written.** No confirmatory data exist. No run of the submitted configuration on the 25 public games has been made for this study, and nothing exists under `ARC-AGI-3/runs/paper/`. The author of this amendment has not opened any PACE transcript and has not computed any reuse statistic, except the single pooled value on excluded commit-smoke transcripts disclosed in §1. Information that reached the paper workstream before this amendment is disclosed in §1. Everything in §2 is excluded from all confirmatory and secondary statistics of this study.

#### 1. Disclosure: what was seen

- **Pilot transcripts.** The two ft09 commit-smoke transcripts were already excluded by Amendment 3.
- **PACE held-out runs of Qwen3.8-Flash-Next.** These ran on 4 held-out games (cd82, m0r0, su15, tn36), 177k tokens per game, with solved-level memory on, under the PACE vLLM port of the harness. Another workstream (ARC-AGI-3 science, "C") read three transcripts in full for qualitative coding: `su15-1944f8ab_p0`, `tn36-ef4dde99_p0` and `m0r0-492f87ba_p1`, all from job 6599000. An independent reviewer ("F") parsed the `events.jsonl` of four run directories to count dropped retained functions. Its aggregate counts reached this workstream: base model, 16 game-runs, 15 sandbox timeouts, 13 of which emptied the kept table, 154 functions dropped; LoRA model, 16 game-runs, 9 timeouts, all of which emptied the table, 188 functions dropped. These are counts of drop events, not of calls or reuse.
- **No-op guard A/B (job 6609164).** Results and summaries of both arms were read: argv, scores, levels. This was 1 pass with a truncated budget, and it is not eligible as confirmatory data anyway.
- **Third-party public Kaggle runs.** About 480 request logs of other teams' public notebooks sit in `ARC-AGI-3/train/sft_v1/`. They were processed to build fine-tuning data and to compute scores, levels and token use. Fine-tuning windows derived from them (`sft_v1`, `v2w48`) were counted by the reviewer for windows, tokens and level shares. No reuse statistic was computed from them.
- **Code.** The timeout-clearing mechanism of §4 was verified in the harness source.
- **Formats and configs.** The author also read the `config.json` of `flashnext-6599000-base-heldout` (serving and flag fields only) and searched the two excluded ft09 pilot transcripts for format strings (retained-function lines, tool-result blocks).
- **An inadvertent look (author, 2026-10-27, about 03:40 UTC).** A format check of the analysis code was pointed at the directory `ARC-AGI-3/kaggle/outputs/`. Besides the two pilots, that directory contained `arc3-franzen-ka3-v1`, a commit smoke of a different configuration (version 1 plus E201/E209, the same model, ft09 only), so its transcript was parsed too. The script printed the pooled U1 share of that single game, 0.188 (insufficient data). Nothing else was computed from it, and it is excluded in §2. Format checks since then use explicit file lists.
- **Reviewer's reads (F, 2026-10-27).** F read the harness source, the version 1 notebook and the parent notebook. From the excluded pilot outputs, F read only the field names of `benchmark.json`, the lengths of its two free-text fields, and string counts in the live logs. From version 3's summary files, F read the pass count, start and end times, the minimum, median and maximum per-game wall-clock time, end-state counts (33 won, 67 gave up) and `git_status.txt`. F opened no transcript, events or request log.
- **Statements** (asked before freezing, quoted verbatim): question "since 10-26, have you computed any reuse, retention or clearing statistic on any Flash-Next run, and which?"
  - C (COLLAB-011, received 2026-10-27; quoted verbatim): "本会话（COLLAB-011，10-26 15:27Z 起）没有对任何 Flash-Next 运行计算过复用、保留或清空统计，没读过 events 的 dropped、kept_*、carried_* 字段，没解析过 \"retained functions\" 行，也拒绝了 D 要“超时前一刻 kept 函数个数”的请求。下面三条是相关但不同的量，以及之前的历史：(1) 和清空相关的量：只数过 30 s 沙箱超时的次数，也就是 events 的 error 字段含 \"Timeout\" 的条数，按 177k 前后分开计。运行是 E111a（6614732/6615716）和 E111b（6620991/6621209）。按 E209 缺陷，每次超时都会清空函数表，但清空了多少个函数没有数。(2) 第三方日志：在 romantamrazov_v74/v75、yongjiehishi_v5、heliosli_v1、tantan0327_v1 的转写里，数过“含模拟器类函数定义（def step/apply/simulate…）的关卡比例”和思考文本的 n-gram 重复率。数的是“定义”，不是保留或调用。(3) 10-26 以前（COLLAB-007 workflow 第一轮的 Session C，以及它的审查和修订）：已看清单内的 6599000/6609924 base 和 FT held-out 运行上，有一项“超时清空函数表次数和丢失函数个数”（base 13/15 次、154 个；FT 9/9 次、188 个）。这是 F 用 timeout_drops.py 算的，AGI3 修订者重跑过；第一轮 C 本身只在 3 份已看转写里定性读到过“函数被清空”。关于两个文件：没读过 arc3-franzen-ka3-v1。sft_v1 只读过 turn_index.jsonl 和 runs.json 的计数字段；另外为了查格式，打开过 segments 文件的一个 romantamrazov_v74 片段（只看了系统提示开头和消息条数），以及 turns_heldout 的第一条记录（franzen_m2_v3 cd82，只看了字段名和系统提示前 200 字符）。没读过任何派生窗口（build_windows 的输出）。"
    - Note by the author: E111a and E111b are non-confirmatory (R-01, R-05). The one record C opened from a file derived from the §7 data (`turns_heldout`, franzen_m2_v3 cd82) was read for field names and the first 200 characters of the system prompt, which is the same in every run and carries no retention or reuse information.
  - D (COLLAB-012, received 2026-10-27; quoted verbatim): "10-26 以来，D（含 D 派生的后台子任务）只对一组 Flash-Next 运行计算过“清空”类统计，就是 E209 影响分析。由 D 的子任务在 10-26 约 15:30–15:40Z 完成，脚本为 research/agi3/analysis_D/e209/timeout_wipe_impact.py，输出为同目录的 .txt 和 .json。- 运行：PACE held-out 的 base（flashnext-6599000-base-heldout、flashnext-6609924-base-heldout-p34）和 FT（flashnext-sft-6609924-heldout、flashnext-sft-6609924-heldout-p34）。C 此前已分析过这些运行，读的是 research/agi3/analysis_C/data/ 下的 events.jsonl。- 量：沙箱超时次数；超时导致的函数表清空次数；每次清空丢失的函数数（读了 snippet 事件的 dropped 和 kept_available 字段）；其中多少之后被重新定义，以及估算的重定义 token；清空后 10 个 snippet 内 NameError/ImportError 的比率。- 没读 kept_refs、carried_*、kept_calls，也没算任何复用率。其他 Flash-Next 运行都没有算过复用、保留或清空的统计：- fnab A/B 的转写只用于 E202 的 no-op guard 重放，以及 R1 的物体卡片回放；- E111a/E111b 没碰；- 本地 stub 测试（E201、E103）用的是假模型。关于 ka3-v1（ARC-AGI-3/kaggle/outputs/arc3-franzen-ka3-v1，1 局 ft09 的 commit 冒烟）：我打开过 transcripts/ft09-0d8bbf25_p0.txt。为了写解析脚本，我数了块标记，并打印过其中一条模型回复（约 30 行：META、工具调用代码开头、THINKING 开头）。之后用脚本算了回复数 62、回合数 38、无工具调用数 0、无动作回复数 34。没有在那里统计任何清空或保留；与 E209 相关的检查只看了 kernel 日志里的 “E209_PATCH on” 一行。"
  - COLLAB-008 (relayed verbatim by the orchestrator, 2026-10-27): "COLLAB-008 回答 G 的问题（已查我会话及其 workflow 子代理的全部工具调用记录，没有做新分析）：10-26 以来我这边做过两类相关计算，都不涉及 B0a/B0b、T1 评测（6614347、6616215、6617889、6619753、6620448）：① 10-26 约 14:01Z，项目审计 workflow（wf_924f5e43）里的一个只读子代理用冻结的 `paper-track/analysis/analyze_reuse.py`，在 `ARC-AGI-3/kaggle/outputs/arc3-franzen-ka-v1` 和 `arc3-franzen-ka2-v3` 两份 ft09 试点转写上复跑，复现了已有记录里的计数：定义 16/23、保留 7/10、跨关调用 0/2、通关 6/6。它另外跑了 reuse 的合成数据测试。② 构建 v2w48 和 V-B3 时，在 sft_v1 的派生段和窗口上做了“保留函数被清空”事件（AGI3-R03 bug）的普查：- 量包括：清空事件按原因计数（全是 timeout，非 H10 段去重后 51 次）、被丢弃的函数数（去重后 825）、清空之后的目标数（804，按关卡分）、窗口内含清空事件的目标数（v2w48 38 个、V-B3 92 个）等；- 数据在 `ARC-AGI-3/train/sft_v2/stats_v2w48.json` 和 `stats_vb3.json` 的 `retained_fn_bug*` 字段。在 B0a、B0b、T1 评测上只算过关数、分数、健康项（无 tool call、长度截断、snippet 错误率、L1 token 占比）和 GAME_OVER，没有算过任何复用、保留或清空的统计。"
    - COLLAB-008, second reply (relayed verbatim by the orchestrator; no numbers): "1. 时间：普查在 2026-10-26 约 15:33Z–16:27Z 做的，是 v2w48 构建的一部分，去重修订在 16:18–16:27Z；V-B3 的 stats 在约 19:52Z–20:03Z 生成。按来源拆分：**没有**。`retained_fn_bug*` 只按训练集/held-out、游戏、关卡和普查范围（非 H10 训练段 / H10 段 / 全部 sft_v1 段）拆，没有单独给出 franzen_m2_v3 或 lalalia9 的数；scratch 里也没找到按来源拆的中间结果。提醒两点：- 有按游戏拆的数。若某个游戏的数据全部来自单一来源，它的按游戏数实际上就等于按来源的数；哪些游戏是单一来源，我没查（查了就是新分析）。- 我上一条回复里带了几个汇总数（全部来源合计，没有按来源拆），请 G 自行判断是否影响盲态。2. 确认：§7 分析完成前，我不再对 franzen_m2_v3 或 lalalia9 派生的数据计算任何保留、清空或复用统计；用这些数据训练不受影响。这条已写进 COLLAB-008。"
    - Assessment by the author, with the reviewer's check. ① concerns the two pilots already excluded by Amendment 3 and reproduces their recorded counts; nothing new was exposed.
    - ② is a clearing census on fine-tuning segments derived from third-party logs, made on 2026-10-26 and stored readable on disk in `ARC-AGI-3/train/sft_v2/stats_v2w48.json` and `stats_vb3.json`.
      - It pools about 32 sources, among them the §7 data (`franzen_m2_v3`) and `lalalia9`. It has three scopes (non-H10 segments, H10 segments, all segments) and per-game and per-level counts, but no split by source or by S/V/N label. It contains no reuse or cross-level call quantity: its "carried" fields count message copies carried across context drains. The reviewer read only its field names and descriptions.
      - The author checked, from run metadata only (`ARC-AGI-3/train/sft_v1/runs.json`: source, game, split, segment counts; no retention field), that no game's segments come only from `franzen_m2_v3` or `lalalia9`. The one single-source game is sk48, from `romantamrazov_v74`. So the per-game counts are not source-specific counts of the §7 data.
      - §7's primary U1 and U2 stay blind. Clearing frequency is a nuisance quantity, and a pooled census of it existed before freezing; the pooled totals reached the author through the orchestrator's relay at about 03:47 UTC. §7 reports its two clearing-frequency descriptives as not blind (§7).
    - Timing. The T1/T2 rules and their code were written before these totals reached the author. The reviewer recorded the code's hash (`428fb1b62d0d`) at 03:45:12 UTC; the later changes only implement the reviewer's requests R13–R18 (multiple sessions and reruns in `prepare_units.py`, the per-level set cross-check, and `tool_call_id` deduplication). They do not touch the definitions of T1, T2, the clearing rule or the descriptives.
  - F (this reviewer, COLLAB-014, from 2026-10-26 15:27 UTC): none. Only source code, run-summary fields and synthetic tests were read or run, plus, at 03:49 UTC, the field names and scope descriptions of the pooled clearing census in ARC-AGI-3/train/sft_v2/stats_*.json (no values). The drop counts in the PACE bullet above come from the earlier review REVIEW_AGI3 (2026-10-26 14:40–15:15 UTC).

#### 2. Seen-run list (excluded; the unit is the whole run directory, all games and passes)

| Run | Why excluded |
|---|---|
| `ARC-AGI-3/kaggle/outputs/arc3-franzen-ka-v1`, `arc3-franzen-ka2-v1`, `-v2`, `-v3` | commit smoke outputs; the ft09 pilots (Amendment 3) |
| `ARC-AGI-3/kaggle/outputs/arc3-franzen-ka3-v1` | commit smoke of a different configuration (version 1 plus E201/E209); parsed inadvertently by the author's format check (§1) |
| COLLAB-008 runs B0b (job 6616215) and the T1 evaluations (jobs 6617889, 6619753, 6620448); B0a (6614347) is R-04 | not created for this study; other workstreams read their levels, scores and health fields (COLLAB-008's statement, §1) |
| PACE `flashnext-6599000-base-heldout` (passes 1–2) | three transcripts read; events parsed for drops |
| PACE `flashnext-6609924-base-heldout-p34` (passes 3–4) | events parsed for drops |
| PACE `flashnext-sft-6609924-heldout`, `-p34` | events parsed; LoRA model, not the submission |
| PACE `flashnext-6599000-e2e` | smoke run; directory copied by another workstream |
| PACE `fnab-6609164-A-base`, `fnab-6609164-B-noopguard` | results read; 1 pass, truncated (`--deadline-s 9934`) |
| Any other run directory created before this amendment's freeze time | not created for this study |

Third-party logs in `ARC-AGI-3/train/sft_v1/` are not data of the submitted configuration, so they can never be confirmatory. §7 governs their use.

Runs declared **non-confirmatory** in `paper-track/RUN_REGISTER.md` are likewise excluded, and any workstream may read them: R-01 AGI3-E111a, R-02 the AGI3-E103 treatment arms, R-03 the AGI3-E103 control arm (archived with Option A′), R-04 B0a, R-05 AGI3-E111b. R-04 and R-05 were registered after their submission, which matters only for read access. The register is kept by the paper workstream; each entry is timestamped, and entries are made before the job is submitted except where stated.

#### 3. Blinding from now on

- Confirmatory runs start only after this amendment is frozen. They are recorded as versions of the dedicated paper notebook (`RUN_REGISTER.md` R-06).
- Until `analysis/analyze_reuse.py` has been run once on the complete data, nobody opens their transcripts, `events.jsonl` or request logs, and nobody computes any reuse, retention or clearing statistic from them.
- Anyone may read, from `summary.txt` and `benchmark.json`, the fields `final_score`, `levels_completed`, `actions_per_level`, token and wall-clock totals and `state`. These carry no reuse information.
- The free-text fields `solver_note` and `solver_analysis_html` stay sealed with the transcripts.
- Reruns and extra passes are triggered only by the validity rules of §6, never by these summaries.
- Whoever watches the live logs stops reading and reports if transcript content (`[TOOL`, `Current state`, `def `) appears in them.
- The analysis is run once. Any rerun after a bug fix is reported together with the fix.

#### 4. Known mechanism: involuntary clearing of kept functions

**Mechanism** (verified in the harness source that both the Kaggle submission and the PACE port use). With `ARC3_PERSISTENT_FUNCTIONS_SCOPE=game`:
- When a Python call times out (30 s), the sandbox returns a result without the `keepable_functions` field. The same happens when the sandbox child cannot start, crashes (reported to the model as the fixed text `Sandbox process exited unexpectedly.`), or returns an invalid or unknown response.
- `_record_retained_functions` then replaces the kept table with an empty one. The next message tells the model that each previous function "is no longer retained; redefine it if needed".
- Under game scope, level transitions do not clear the table. It is emptied when a tool result lacks `keepable_functions` (timeout, start failure, child crash, invalid or unknown response), when restoring or collecting kept functions fails inside the sandbox, or when recording them raises an error.

**Effect on the frozen measures.** The definitions of Amendment 3 are unchanged:
- A function cleared during level ℓ still counts as kept at the start of ℓ, but it can no longer receive a carried call. This lowers uptake at ℓ and lowers U1.
- A clearing late in level ℓ−1 can leave level ℓ with no kept function. Level ℓ then stops being an opportunity level.
- A function redefined after a clearing counts as redefined, not carried.
- If clearings occur more often on one label than on another, U2 is shifted. The direction is not known in advance.

**Primary analysis: unchanged.** The study measures the submitted agent as it behaves, and clearing is part of that behaviour. The claim boundary gains one sentence: *"Low uptake can be partly mechanical: a sandbox timeout empties the kept table."*

**Pre-registered sensitivity analyses** (secondary; they never replace the primary verdicts; same bootstrap, seed and interval rules as Amendment 3):
- *Involuntary clearing* (transcript-based).
  - **Definition.** An involuntary clearing at level ℓ is a `[TOOL RESULT: python]` block at level ℓ whose first non-empty line, or the line right after an `error:` line, begins with `Tool timed out after` or `Sandbox process`. This is where the transcript renders a sandbox error; a model that prints such text later in its own output is not counted. These are exactly the sandbox failures after which the result lacks `keepable_functions` and the harness empties the table. The level is the frozen rule's level, i.e. the latest `Current state` line before the block.
  - **Not counted.** Ordinary Python errors (rendered as `Traceback …`) return `keepable_functions` and keep the table. In-sandbox restoration or collection failures and recorder errors also empty the table, but they leave no trace in the transcript, so they are not counted. A crashed sandbox child is reported as `Sandbox process exited unexpectedly.` and is counted.
  - **Why not compare successive retained lists.** The transcript shows each tool result's stdout, result and error, but not the harness's retention notices (verified in `_render_tool_result_display` and on the two excluded pilots). After a timeout the model often redefines the same names within the turn, so the next list can look unchanged even though the table was emptied.
- **T1, availability-adjusted U1.** A kept function is *available* if it appears in the kept-at-start list of at least one level after the level where it was first defined. This uses only the kept-at-start lists, so it needs no loss detection. T1 is the per-game share Σ reused / Σ available, averaged over games with at least one available function. Same thresholds and the same 8-game floor as U1.
- **T2, clearing-free U2.** U2 recomputed on opportunity levels with no involuntary clearing at that level. Same thresholds and floors as U2. T2 conditions on a level-level outcome correlated with activity; it bounds rather than removes the clearing effect.
- **Statistics.** T1 and T2 go through the frozen `u1` and `u2` functions of `analyze_reuse.py`, with a fresh `random.Random(20261025)` used in the order T1 then T2.
- **Descriptive.**
  - Survival share Σ available / Σ eligible.
  - Involuntary clearings per 100 Python calls, by the label of the level (level 1 as "first").
  - Share of opportunity levels with an involuntary clearing, by label.
  - Among opportunity levels with a clearing, the share with uptake before the first clearing, by label. A carried call is placed by the position of its snippet. The order is recomputed with the frozen rules, and the script stops if the recomputed carried functions disagree with the frozen parser's, level by level, as sets of names, on any transcript.
  - Python calls per opportunity level, with and without a clearing (median and quartiles).
- **Wording.** When a T verdict differs from its primary verdict, the paper reports both, with no causal claim. A T1 difference is attributed to the loss of kept functions before a later level (clearing or retention rejection); a T2 difference is attributed to clearing.
- **Code.**
  - Location: `analysis/analyze_reuse_clearing.py`. It loads the frozen `analyze_reuse.py` by path, reuses its parser and statistics unchanged, and also prints the primary U1/U2 exactly as the frozen script computes them, for a side-by-side table.
  - Testing (`analysis/test_analyze_reuse_clearing_synthetic.py`, synthetic only):
    - Part 1: three hand-built transcripts with exact expected counts. They cover a timeout in both rendering formats, a start failure, a crashed child, a traceback and a model-printed "Sandbox process" line that must not count, and uptake before and after the first clearing.
    - Part 2: 25 games × 2 passes in which uptake is equal on S and N, but timeouts empty the table on most N levels. The primary U2 reads this as "selective"; T2 must not.
    - Part 3: a synthetic request log (append-only history, a context drain, response rows) for the agreement check.
    - Part 4: `analysis/prepare_units.py` on synthetic sessions: invalid, cut and missing game-runs, the 20% rule over the expected games, two one-pass sessions, a rerun of an incomplete pass, no silent overwrite, no rerun of a complete pass, at most one rerun per pass, and an unexpected game.
  - Format check: the two excluded ft09 pilots parse (91 Python calls, 0 clearings). They contain no timeout, so they test the format, not the detection.
  - Freeze: the code is frozen with this amendment, before any confirmatory run.
  - **Agreement check.** This applies where request logs exist (`save_request_logs`): §7 has them; the Kaggle run is checked at its smoke test. The harness's own retention notices in the request logs are counted per game-run, once per `tool_call_id` so that a re-sent request is not counted twice, under four headings: infrastructure errors; functions reported "no longer retained" after such an error; whole-table "cleared" notices (restoration, collection or recorder failure); and drops after error-free calls. These are compared with the transcript rule. They also count the silent clearings the transcript cannot show. The counts are reported descriptively; the definition stays the transcript rule.

#### 5. Measured configuration

"The submitted configuration" in Amendment 3 means **the agent configuration of `kefeiyan/arc3-franzen-ka` version 1, which produced the scored submission 57639912**:
- Franzen Milestone 2, Qwen3.8-Flash-Next W4A16 AutoRound with the MTP drafter, the Duck/TAAF harness bundle as attached, the startup keep-alive and solved-level memory;
- every environment flag as set in that notebook, recorded verbatim from its customization cell;
- the harness bundle and serving build attached by slug without a version, namely `dfranzen/taaf-kaggle-source-bundle-copy` (last updated 2026-09-28) and `dfranzen/pennyroyal-v253` (last updated 2026-09-29), both earlier than version 1. The paper run checks both dates before it is pushed and logs the bundle's file hashes at start.

`kefeiyan/arc3-franzen-ka2` version 3 differs only in infrastructure: keep-alive retries, a late-start guard and input-path discovery. Its agent flags are the same and are checked flag by flag before the runs.

This choice does not depend on when that notebook becomes public; on 2026-10-26 the user decided not to publish any notebook before the lock. If a later scored submission from `arc3-franzen-ka2` keeps the agent flags and harness patch of version 1, the measured configuration also describes it, and the paper may cite that submission's ID.

If a later submission changes agent behaviour, the paper reports it as different from the measured configuration and gives its leaderboard score separately. Examples: the no-op repeat guard, a timeout fix that keeps the table, a fine-tuned model, a different token budget. Any later data on such a configuration is never pooled with this study's data.

#### 6. Data source: Option B, Kaggle Save & Run of the submitted configuration

**Approval.** The user approved this run in the paper workstream's session on 2026-10-27 at 03:20 UTC: "批准 10-31 配额重置后在 Kaggle 上跑论文主数据：提交配置（v1），25 局 × 2 遍，约 4.5 GPU 小时的 ARC3 配额。" Options A and A′ (PACE) are not used. PACE was paused by the user on 2026-10-27 at 02:15 UTC and neither option was approved. The approval did not depend on any reuse data.

**The run.**
- **Notebook.** A private Kaggle notebook built from `kefeiyan/arc3-franzen-ka` version 1 (submission 57639912).
  - Unchanged: the agent code, the harness bundle, the model inputs and every agent environment flag.
  - Changed: only the run-mode settings. A Save & Run plays the 25 public games locally, two passes, and keeps the transcripts. The commit mode also keeps diagnostics and request logs on (`TAAF_RUN_AS_SUBMISSION=0`, `TAAF_MINIMAL_DIAGNOSTICS=0`, `save_request_logs=True`); these affect logging, not the agent, and are checked in the run's logged environment.
  - Before the run starts, its slug, version and diff against version 1 are recorded in `RUN_REGISTER.md` (R-06); the diff must touch run-mode settings only. No competition submission is made from it.
- **Budget (as version 1 handles it on Kaggle).** No per-game token cap: version 1 leaves `max_generated_tokens_per_game` unset. In the competition rerun it runs 110 games concurrently, each with `max_runtime_s_per_game = 532 × 60` under priority scheduling.
  - The paper run scales the per-game wall-clock budget to give each game-run the same share: `max_runtime_s_per_game = 532 × 60 × N / 110` seconds, where N is the number of game-runs played concurrently in the session. With both passes in one session, N = 50 and the budget is about 242 minutes; with one pass per session, N = 25 and it is about 121 minutes.
  - The solver concurrency equals N, as version 1 sets it for commit runs, and priority scheduling stays on as in the submission.
  - This follows the method of Franzen's version 3 (§7), so the primary data and the replication share the same budget rule. The 177,000-token budget of the archived PACE options does not apply.
- **Passes.** Passes 0 and 1, in one or two Save & Run sessions on the RTX PRO 6000 machine type of the submission. All 25 public games are played; the commit-run exclusion list of version 1 is emptied.
- **Time and quota.** The run starts after this amendment is frozen and after the quota reset of 2026-10-31 00:00 UTC. The approved quota is about 4.5 GPU-hours.
  - Because the per-game budget is a wall-clock budget, a one-session run lasts about 4.0 hours of play plus start-up, roughly 4.4–4.6 hours whatever the throughput. The quota tolerance is an authorization matter recorded in `RUN_REGISTER.md` (R-06); it changes no rule of this amendment.
  - Any rerun or extra session would exceed the approval, so it needs the user's renewed approval first.
- **Validity.**
  - A game-run with zero generated tokens or zero turns is invalid (§5 of the original registration).
  - A game-run is *cut* if its `state` in `benchmark.json` is not `won` and its `final_wallclock_seconds` is more than 300 s below its budget. Typical causes are the session limit, a crash or a server failure. Cut game-runs are reported and excluded from U1 and U2.
  - The k-th game-run of a game in `benchmark.json` is pass k: the framework appends game-runs pass by pass, and the solver names transcripts `<game_id>_p<pass>.txt`.
  - These rules are applied by `analysis/prepare_units.py`, frozen with this amendment, which reads only the summary fields. The frozen analysis then runs on the transcripts it selects.
  - A pass is checked against the expected games, the 25 public games of `level_annotation/levels.csv`. An expected game with no game-run in the pass counts as missing, and a game outside the set is an error.
  - A pass with more than 20% of the expected games invalid, cut or missing (no game-run or no transcript) is rerun once, if the user approves the extra quota; if it fails again, or the rerun is not approved, it is dropped and reported. A rerun may replace only an incomplete pass, and each pass at most once.
  - Passes are numbered in session order. A rerun of pass k replaces pass k. `prepare_units.py` takes all sessions in one call, with `--levels` naming the expected games; it refuses to overwrite a selected transcript, to rerun a complete pass, or to rerun a pass twice.
  - At least 2 valid passes are needed by 2026-11-06 23:59 UTC. Otherwise the primary question is "insufficient data" (Amendment 3) and §7 governs.
  - Primary data *exist* when §6 yields at least two valid passes by the deadline, whatever the data floors of U1 and U2 give. §7's role is then a replication, even if a primary verdict is "insufficient data".
- **Outputs.**
  - The transcripts `<game_id>_p<k>.txt` are downloaded to `ARC-AGI-3/runs/paper/qwen-reuse/<slug>-v<version>/transcripts/` with a SHA-256 manifest, without being opened.
  - The notebook version, the model inputs and the logged environment are recorded.
  - `summary.txt` and `benchmark.json` may be read by anyone, within the fields listed in §3.
  - Per-game generated tokens and the session's aggregate tokens per second are reported descriptively. The budget rule gives each game-run the same per-game share of wall-clock time as in the competition, not necessarily the same compute.
- **Wording.** "The submitted configuration's agent, run on Kaggle's own runtime on the 25 public games." Leaderboard scores of the hidden games are reported separately and descriptively.
- The blinded pass rule of §7 of the original registration is not used. U1 and U2 have no noise-only step.

**Archived options.** The texts of Options A and A′ in the drafts before 2026-10-27 03:20 UTC (dedicated PACE run; the E103 control arm, `RUN_REGISTER.md` R-03) are not part of this amendment.

#### 7. Parent-configuration replication

- **Data.** The Kaggle transcripts of Franzen's own Milestone 2 notebook, `dfranzen/arc-agi-3-milestone-2-solution` version 3: 100 game-runs, 25 games × 4 passes.
  - Version 3 reruns his open-sourced version 1 with 4 passes on all 25 games, using a runtime budget scaled to the competition's time per game (his notebook text).
  - This is the parent configuration, without our patches or solved-level memory, which about 1,500 leaderboard teams copied (forum estimate). It ran on Kaggle's own runtime.
  - **Location.** `paper-track/third_party/franzen_m2_v3/transcripts/`, gzip-compressed copies of the 100 `<game_id>_p<k>.txt` files, with the originals' SHA-256 in `MANIFEST_transcripts_events.sha256`. They were copied on 2026-10-27 from a temporary directory, verified, and never opened.
- **Analysis.** The frozen parser and the same U1/U2 rules, plus T1/T2 and the request-log agreement check of §4, with the same seed and order. Results are never pooled with the primary data.
- **Validity.** §6's validity and cut rules apply with N = 100, a budget of 29,018 s, and the same expected games. By the summary fields, no game-run of version 3 is cut, and the median per-game wall-clock time is 29,114 s.
- **Role, fixed now.**
  - If primary data (§6) exist, §7 is reported as a replication on the parent configuration.
  - If they do not, §7 is the paper's only pre-registered U1/U2 result. It is worded as a result about the parent configuration, not about our submission, and the primary question keeps the Amendment 3 "insufficient data" wording.
- **Feasibility check.** At freezing time, a blind check confirms only that the files decompress to the recorded hashes and that the parser finds snippets and `Current state` lines. It prints counts of parsed files, snippets and level lines; it never prints kept, carried, retained-line or level-reached counts. If the format does not parse, this section lapses.
- **Blinding.** Until §7 is analysed, no workstream opens these transcripts, events or request logs, or computes retention, clearing or reuse quantities from `franzen_m2_*` or `lalalia9_*` logs. This also covers files derived from these logs (fine-tuning windows): they may be used for training, but not for retention, clearing or reuse statistics. The pooled clearing census in `ARC-AGI-3/train/sft_v2/stats_*.json` is not split by source or label, and no workstream derives a `franzen_m2_v3`-specific clearing count from these stats or the segments until §7 is analysed.
- **Reporting labels.** §7's two clearing-frequency descriptives (clearings per 100 calls; share of opportunity levels with a clearing) are reported as "not blind: a pooled census of this quantity was computed before freezing (§1)". The other descriptives, including uptake before the first clearing, and the U1, U2, T1 and T2 verdicts are reported as blind.
- **Provenance.** The source is recorded as `dfranzen/arc-agi-3-milestone-2-solution` version 3 (`ARC-AGI-3/train/sft_v1/sources.json`). The parent notebook used to compare the agent flags is the local copy `ARC-AGI-3/kaggle/base/arc-agi-3-milestone-2-solution.ipynb` (`n_passes = 4`), not itself verified to be version 3. Its flags (`SCOPE=game`, `GUIDANCE=1`, `BATCH_NOOP_BLOCK=1`, `TOOL_TIMEOUT=30`) match version 1's.

#### 7b. Partial human second annotation (refines §2 of the original registration)

- **Sample.** Whole games drawn with seed 20261026 until at least 40 levels (level ≥ 2): lf52, bp35, ls20, sc25, g50t, m0r0, sp80, 44 levels in total. Script: `level_annotation/human_check/make_sample.py`.
- **Procedure.** The human annotator labels these levels blind to the AI labels, using the same S/V/N definitions and first frames only.
- **Report.**
  - Unweighted Cohen's kappa over S/V/N, with a game-bootstrap 90% interval (`human_check/kappa.py`), and S-vs-N agreement.
  - U2 recomputed on these 7 games with the human labels: estimate and interval only, no verdict. Seven games are below the 8-game floor, and a subset this small has no power.
- **Primary labels.** The primary analysis keeps the frozen AI labels.

#### 8. Unchanged

- The labels (`levels.csv`), the parser and the U1/U2 rules and thresholds of Amendment 3. The frozen `levels.csv` also defines the expected games of §6 and §7.
- The optional ablation and the Amendment 2 gate.
- The 2026-11-06 23:59 UTC data deadline.

### Amendment 5 — 2026-10-27: invalid game-runs on Kaggle

**Reason.** The feasibility check of Amendment 4 §7 was run right after Amendment 4 was frozen (2026-10-27 04:02 UTC). At that check, `analysis/prepare_units.py` classified all 100 game-runs of the parent configuration as invalid.
- The cause is the data format, not the runs: Kaggle's `benchmark.json` leaves `final_generated_tokens` at 0 in every game-run.
- The generated tokens are recorded per action in the game-run's `history`. For our version 1 pilot their sum is 70,376, the figure its `summary.txt` reports.
- Amendment 4's rule, which reads `final_generated_tokens`, would therefore mark every Kaggle game-run invalid, including the primary data of §6.
- The fields used by the cut rule are filled on Kaggle: `state`, and `final_wallclock_seconds`, whose median per game-run is 29,114 s in version 3.

**Data status.** No confirmatory data exist, and §7 has not been analysed.
- Only fields that Amendment 4 §3 lists as readable were used: the token totals of `benchmark.json`, whether each game-run's history is empty, and its generated tokens summed. The code does not read what the actions are.
- In version 3, `final_generated_tokens` is 0 in 100 of 100 game-runs; the history is empty in 0 game-runs; and the history's generated tokens sum to 0 in 0 game-runs (the reviewer's counts).
- No reuse, retention or clearing quantity was computed.

**Change.** In Amendment 4 §6, and through it in §7, a game-run is *invalid* if its `benchmark.json` history has no action, or the generated tokens summed over its history are 0.
- This is the original §5 rule, "zero generated tokens or zero turns", read from where Kaggle records the tokens.
- It needs no access to the sealed transcripts before the analysis.
- On the §7 data it marks 0 game-runs invalid, as the withdrawn alternative below also would, so the choice does not depend on the result.
- `final_generated_tokens` is no longer used.

**A withdrawn draft and the frozen files.**
- A first draft of this change, never frozen, judged a game-run invalid when its transcript held no python snippet. It was withdrawn because it would have read the sealed transcripts before the analysis.
- That draft was written, at about 04:04 UTC, over the two files that Amendment 4 had frozen: `analysis/prepare_units.py` and `analysis/test_analyze_reuse_clearing_synthetic.py`. This should not have happened.
- The frozen bytes are archived in `analysis/frozen_a4/`. They match the Amendment 4 hashes, and `FREEZE.txt` records both the archive and the Amendment 5 versions now at the original paths.
- From now on a frozen file is archived before it is changed.

**Code.**
- `analysis/prepare_units.py` now sums `generated_tokens` over `history`, and records that sum, not `final_generated_tokens`, in its manifest.
- Its synthetic test writes `final_generated_tokens: 0` in every game-run, as Kaggle does. Invalid game-runs are made from an empty history, or from a history whose tokens sum to 0.
- `analysis/check_s7_format.py`, the one-off feasibility check run at the freezing of Amendment 4, is recorded with its hash.
- Everything else in Amendment 4 is unchanged.

**Review.** Checked by an independent workstream before freezing (`research/review/REVIEW_PAPER_AMENDMENT5_20261027.md`).
