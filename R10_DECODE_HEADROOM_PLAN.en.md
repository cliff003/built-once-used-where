> English translation of `R10_DECODE_HEADROOM_PLAN.md` (sha256 `5e4482fc3b9d4f4511b94cf252a904b45ce9bc4494941e310a554f922ce49329`). The original, written in Chinese, is the registered version; where the two differ, the original governs. Translated on 2026-11-09.
>
> Translator's note: quotations are translated as well and marked "(translated)". Single capital letters (A–G) are the project's internal agent workstreams, for example F for independent review and G for the paper; "the coordinator" is the session that coordinated them. The tags [V], [C] and [E] mean checked by the writer, claimed by someone else (a letter after C names the source) and estimated. COLLAB-0xx are rows of the internal coordination board, and DECISIONS and RUN_REGISTER are internal logs. Paths that are not in this repository refer to the project's private working tree.

---

# R-10 registration: how the paper reports the ARC3 decoding headroom (the T0 ceiling and the calibration of the existing draft)

- **Written**: 2026-11-01T00:20:35Z (`date -u` was run before writing), workstream G. Not changed after freezing; the hash is recorded in the `.sha256` file and in RUN_REGISTER.
- **Basis**: the coordinator's message of 11-01 00:17Z: "T0 (6716854) and the MTP calibration (6716855) are running on PACE as research; the results can be used for the paper." (translated) How the two jobs were submitted is in `operations/2026-11-01T001713Z-claude-coordinator-blanket-release-c007.md`.
- **Data status when written**:
  - 6716854 and 6716855 are both queued (PENDING). This is the coordinator's record of 00:15Z; G did not check PACE itself.
  - T0's only earlier job, 6672420, failed at its self-check, so there is no T0 data (COLLAB-012).
  - There is no AL data either: when F's `MTP_DISTILL_PREREG_20261031.md` was written there was no AL yet; since then only the CPU cross-check 6703280 has run, and it only checks that the forward passes agree (COLLAB-010).
  - G has not seen any output of these two jobs.
- **The verdict rules are F's registrations; this document sets none of its own**:
  - T0's C1–C3 and the 2.95 threshold follow `research/review/ARC3/T0_CEILING_PREREG_B_20261030.md` (`9e2a8a79…`);
  - the definitions of the calibration readings, the requirement that the sampling settings agree, and the three conditions of CP2 follow §1–§2 of `research/review/ARC3/MTP_DISTILL_PREREG_20261031.md` (`166b3ec6…`).
  - This document only sets what the paper reports and where.

## 1. Readings the paper reports (whether the results are good or bad)

- **T0 (6716854)**:
  - at both temperatures, the share of logged tokens that fall outside the support set, and the T selected by C1;
  - T0_mc and T0_exp at this T, and whether each of C1–C3 passed;
  - the conclusion under F's rule ("worth doing" or "not worth doing"), quoted as it stands, together with the two limitations F requires to be stated.
- **Calibration (6716855)**:
  - AL_base (the primary reading, that is, AL_mc), AL_exp, and their difference;
  - whether AL_base falls within 2.52–2.77, and whether AL_base ≤ T0_mc + 0.05 holds;
  - the sha of the draft weight file, and the sha of the position list and the number of positions.
- **The paper adds only one derived reading of its own, called the "accept-length headroom"**: T0_mc − AL_base, together with the ratio T0_mc / AL_base.
  - It counts as headroom only if both jobs produced results, all of C1–C3 and the three conditions of CP2 pass, and the three sampling settings agree (F's §1).
  - If any condition fails, only the raw readings are reported, with the reason why it does not count as headroom.
- **What the headroom means**: how many more tokens per verify step a better draft could accept at most. The paper does not convert it into a wall-clock speed-up or a score, because accept length and wall-clock time are not linearly related, and we have not measured that conversion.
- **No confidence intervals are reported**: the readings are point estimates from one run. The numbers of positions and games are stated as they are, and this is also written into the limitations.

## 2. Where it goes

- Appendix E, "Decoding headroom (exploratory)": one paragraph and one small table.
- One sentence in the §10 limitations: the headroom is an offline estimate, not validated on Kaggle.
- Not in the abstract or the conclusion, not in R-06's analysis, and it changes no conclusion of R-07, R-08 or R-09.
- Appendix E states which notebook's sampling settings the readings use (F's rule names S9 `39fc6f22`), and whether v1 in §6 of the paper uses the same decoding settings. The latter is a fact check, done at the time of writing.

## 3. Failures, reruns and the deadline

- If a job fails, is cancelled, or has no result by 11-05 00:00Z, the paper says "not completed", with the job ID, the reason and the GPU-minutes used. G does not request a rerun for the paper.
- If someone else reruns under their own authorisation, the paper reports **the first job that passes its self-check and writes a result file**, and lists all earlier failed jobs; it does not pick among several finished jobs.
- If a check fails, this is reported as it is, and the conclusion follows F's rule. If someone later changes the code and runs it again, the new result is reported alongside as a separate run, stating what changed; it does not replace the first reading.

## 4. Blinding and data

- Both jobs read the H10 held-out windows (sft_v3's `heldout_late_w96x_h10.jsonl`), not `ARC-AGI-3/runs/paper/`. When G reads the results, G checks the input paths in the job logs.
- These two items are outside R-06's blinding. When G searches files, G excludes `ARC-AGI-3/runs/paper/` as usual.
- Job IDs, start and end times and GPU-minutes are recorded in the R-10 line of RUN_REGISTER, and the paper's compute table copies them.
