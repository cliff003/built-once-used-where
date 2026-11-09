> English translation of `R06_ADDENDUM_HARD_STOP.md` (sha256 `f968f01fda66f8bcbc1a5d4a204ea3d4ede5f91c9c9ee6ee5905eb8587c0e61c`). The original, written in Chinese, is the registered version; where the two differ, the original governs. Translated on 2026-11-09.
>
> Translator's note: quotations are translated as well and marked "(translated)". Single capital letters (A–G) are the project's internal agent workstreams, for example F for independent review and G for the paper; "the coordinator" is the session that coordinated them. The tags [V], [C] and [E] mean checked by the writer, claimed by someone else (a letter after C names the source) and estimated. COLLAB-0xx are rows of the internal coordination board, and DECISIONS and RUN_REGISTER are internal logs. Paths that are not in this repository refer to the project's private working tree.

---

# R-06 addendum: a hard stop for each session, counted from the start of the run (a safety measure)

- **Written**: 2026-10-31T17:47:02Z (`date -u` was run before writing), workstream G. Not changed after freezing; the hash is recorded in the `.sha256` file and in RUN_REGISTER.
- **Basis**: the coordinator's message of 10-31, which set this rule under the authorisation: add the hard stop E asked for, counted from the start of the run, at 45 minutes for the smoke run and 290 minutes for the main run. It is a safety addendum, used only to make sure that no session exceeds the 5.0 GPU-h the user approved.
  - The user's words, 10-27 about 10:00Z: "Yes: a single session of no more than 5.0 GPU hours counts as within the approval; above 5.0 hours, ask me again." (translated)
- **Data status when written**: neither R-06 nor the smoke run has been pushed. The local `ARC-AGI-3/runs/` does not exist (checked at 17:46:56Z [V]). The two notebooks are still the versions G checked on 10-31: main run `884b6f15…`, smoke run `23b38451…` [V].
- **What does not change**: Amendment 4, Amendment 5, the frozen analysis code, the four changes in §1 of `KAGGLE_RUN_SPEC.md`, and every setting of the agent.

## 1. Content

- **Stop time**: counted from when the notebook starts running, each session stops solving at 45 minutes for the smoke run and at 290 minutes (4.83 h, below 5.0 h) for the main run.
- **Implementation**: D adds it to the notebook; it is the notebook's only new change.
  - Before the stop time, it changes nothing in the behaviour of the agent or the scheduling.
  - At the stop time, it must make solving stop and write `benchmark.json`, `summary.txt` and the transcripts as usual, rather than letting Kaggle kill the session and lose the outputs.
- **Not expected to trigger**:
  - the main run has a per-game clock of 14,509 s (about 242 min); with the 50 games starting together and about 20–30 min of start-up, it should finish at about 262–272 min;
  - the smoke run has 600 s per game and, with start-up, should finish within about 30 min.

## 2. If it triggers

- Games stopped by the cut-off are classified by the existing rule of `KAGGLE_RUN_SPEC.md` §4: a game whose `state` is not `won` and whose `final_wallclock_seconds` is more than 300 s short of the per-game clock counts as a truncated game.
- The classification is done by the frozen `prepare_units.py`; this addendum does not change the rule.
- If invalid, truncated and missing-transcript games together exceed 20% of a pass, then, as §4 says, G and the coordinator are told first and nobody reruns on their own; a rerun needs the user's approval again (Amendment 4 §6).
- Whether the stop triggered, and when, is recorded in R-06's record. The methods section of the paper states that this safety stop exists.

## 3. Checks

- After D's change, G checks the diff: compared with the version G checked on 10-31, the only addition may be the stop.
- After the check, D waits for the user to give the go-ahead in D's session, then pushes.
