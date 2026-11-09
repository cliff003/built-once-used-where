> English translation of `JGV2_REGISTRATION_ADDENDUM1.md` (sha256 `656171394aa1715bdb9005b4d261b080b8fa8d645e25174384dcf892b0bf8b10`). The original, written in Chinese, is the registered version; where the two differ, the original governs. Translated on 2026-11-09.
>
> Translator's note: quotations are translated as well and marked "(translated)". Single capital letters (A–G) are the project's internal agent workstreams, for example F for independent review and G for the paper; "the coordinator" is the session that coordinated them. The tags [V], [C] and [E] mean checked by the writer, claimed by someone else (a letter after C names the source) and estimated. COLLAB-0xx are rows of the internal coordination board, and DECISIONS and RUN_REGISTER are internal logs. Paths that are not in this repository refer to the project's private working tree.

---

# JGV-2 supplementary registration · Addendum 1 (before queueing)

- **Written**: 2026-10-29T11:59:01Z (`date -u` was run before writing), workstream G. Not changed after freezing; the hash is recorded in the `.sha256` file and in RUN_REGISTER.
- **Basis**: F's review `research/review/REVIEW_JGV_SUPP_20261029.md` (11:55:44Z), relayed by E.
- **Data status**: none of the 4 new arms has been queued.
- **Relation to the original registration**: no reading and no verdict rule of `JGV2_REGISTRATION.md` (sha256 `19483062…d9a5`) changes; only the three points below are added.

## 1. The two 12-turn arms may hit the token limit first

- The per-task token budget is still 64k: `episode_tokens` and `task_tokens` are both 64000.
- With the limit relaxed to 12 turns, an episode will quite likely hit the token limit first.
- So D2 measures the effect of "raising the turn limit from 6 to 12 with the token limit unchanged", not the effect of "no turn limit".

## 2. A new report-only reading, D6

D6 enters no verdict.

- **Content**: for each of the arms T1, V, T12 and V12, episodes are split into three classes by how they ended: hit the turn limit (harness status `turns`), hit the token limit (status `tokens` or `task_tokens`), and other. Report the share of each of the first two classes, with the token class also split into `tokens` and `task_tokens`. The other arms are listed as well.
- **Source**: `statuses` and `episodes` in the summary of each arm's `run.json`. `jgv2_analyze.py` already stores them in the output's `run_summaries`, so the script needs no change.
- **Reading** (adopting F's hint, written in advance):
  - if the 6-turn arms rarely hit the turn limit, the difference between T12, V12 and the original arms can only be read as "with the token limit unchanged, lifting the turn limit has almost no effect";
  - only if the original arms often hit the turn limit (such as V's 65/176) and the 12-turn arms clearly hit it less often can D2 be used to test "the turn limit held the images back".

## 3. Where the analysis runs

- The runner does not run the analysis at its end. F has checked this; the purpose is not to overwrite R-08's `jgv_result.json`.
- After the second group finishes, the command of §3 of the original registration is run separately on the B200, with its output written to `jgv2_result.json`, not overwriting `jgv_result.json`.
- If the box has been destroyed by then: pull back the 7 arms' `submission.json`, `run.json` and solutions, and G runs it once on the local machine (a single step that takes a few seconds) and records it.

The run order is still that of §2 of the original registration: first T3 + V2, then T12 + V12.
