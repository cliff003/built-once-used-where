> English translation of `registrations/MTP_DISTILL_PREREG_20261031.md` (sha256 `166b3ec6d128fa7c5a4c6c8337c3dc4f5e5db7936e2b85e587fd078b2dca12d8`). The original, written in Chinese, is the registered version; where the two differ, the original governs. Translated on 2026-11-09.
>
> Translator's note: quotations are translated as well and marked "(translated)". Single capital letters (A–G) are the project's internal agent workstreams, for example F for independent review and G for the paper; "the coordinator" is the session that coordinated them. The tags [V], [C] and [E] mean checked by the writer, claimed by someone else (a letter after C names the source) and estimated. COLLAB-0xx are rows of the internal coordination board, and DECISIONS and RUN_REGISTER are internal logs. Paths that are not in this repository refer to the project's private working tree.

---

# ARC3 MTP draft distillation: registration of the thresholds and checkpoints (before any AL data)

- **Frozen**: 2026-10-31T17:56:39Z (`date -u`), F (COLLAB-014). When this was written there was no AL_base, AL_new or T0 data yet [C B].
- **Basis**:
  - B's message of about 17:5xZ, which set out the definitions and three checkpoints;
  - DECISIONS 10-31 ~17:5x (the user cleared all tests, including PACE training; the coordinator opened this line) and ~18:1x (the coordinator set three hard checkpoints);
  - `research/strategy/COMPUTE_ADVANTAGE_20261029.md` §1③;
  - F's `T0_CEILING_PREREG_B_20261030.md` (T0's C1–C3 and T0_mc).
- B's definitions are taken over largely as they were. F added the items marked **[F added]** below: the primary reading, the upper-bound check, reading only once on the held-out set, agreement of the sampling settings, and how it enters the final selection once submitted.

## 1. Definitions of the readings
- **Positions**: generated tokens of the H10 held-out games, the same batch of positions as T0; reasoning weight 2; the same deduplication rule as T0.
  - **[F added]** Before the first AL is computed, freeze the sha of the position list and the number of positions. AL_base, AL_new and T0 all use this same list.
- **Chain**: NEXTN 3 steps, eagle-topk 1.
  - At each step the draft proposes its own argmax; the recursion uses the draft's own hidden state and the token proposed at the previous step.
  - If step k's proposal differs from the logged token, the chain stops there.
- **Unit**: generated tokens ÷ verify steps, including the 1 extra token after verification, the same notation as SGLang's accept_len, with values in [1, 4].
- **[F added] The primary reading is AL_mc**: along the teacher-forced logged sequence, "logged token == draft argmax" counts as acceptance, the same kind of reading as T0_mc.
  - The logged token is a sample from the processed p, so the probability that each step is accepted is exactly p(d), which is the acceptance probability of target-only verification. Once the chain has accepted, the context agrees with the log, so sampling along the whole chain is unbiased as well.
  - **AL_exp is only a consistency check**: at each step, a Bernoulli on the processed p(d), 64 fixed-seed replays, with the same sampling settings as T0. After accepting a d ≠ the logged token it still uses the logged context, so it is an approximation.
- **[F added] Sampling settings**: the processing order is the same as SGLang's, that is, temperature, top-k 20, top-p 0.95.
  - The temperature must equal the T selected by T0's C1, and must also match the actual sampling settings in the S9 notebook (`39fc6f22`).
  - If the three disagree, the verdict is UNDETERMINED and we stop: such an AL_mc would not measure the acceptance rate at deployment.
  - The target distribution of the KL in training also uses this same set of settings.

## 2. Three checkpoints (stop if any item is not met; no extensions)

### CP1: before 11-01 00:00Z
- Judged by `T0_CEILING_PREREG_B`: C1–C3 all pass and T0_mc ≥ 2.95.
- Stop if T0 < 2.95, if any of C1–C3 fails, or if there is no result by then. **[F added]** The condition "C1–C3 all pass" is a verdict the T0 registration already contains.

### CP2: calibration, before 11-01 00:00Z
- With albucino's existing draft, through B's PyTorch forward pass, compute AL_base (the primary reading). Require **2.52 ≤ AL_base ≤ 2.77**, that is, Kaggle's 2.62–2.67 ± 0.1.
- **[F added]**:
  - |AL_mc − AL_exp| ≤ 0.10, as in T0's C2;
  - **AL_base ≤ T0_mc + 0.05**. T0 is the upper bound "with the target's argmax as the draft"; exceeding it means the code is wrong, for example teacher forcing off by one position so that the draft sees the next token in the log.
  - Record the sha of the draft weight file. AL_new must use the same forward-pass code, with only the weights changed.
- The ±0.1 band covers the difference in position sets (H10 against Kaggle's games). It only checks the total; it cannot show that the layers match SGLang one by one, which needs the Kaggle smoke run of CP3.

### CP3: start training before 11-01 02:00Z, pass the offline threshold before 08:00Z, smoke run before 12:00Z, ask the user before 14:00Z
- **Start of training**: the job's actual Start time in the queue is earlier than 02:00Z. Record the job ID; E checks the resources.
- **Training data**: the non-held-out part of sft_v1, with H10 removed by game id, not touching `ARC-AGI-3/runs/paper/`.
  - **[F added]** Before training starts, hand over two lists of game ids (for training and for H10) and the sha of the training file; F checks that the two lists are disjoint.
- **Training scope**: train mtp-dense only, with the INT4 experts frozen. The KL fits the processed target distribution, with 3 recursive steps.
- **[F added] Read only once on H10**:
  - AL_new is computed for one checkpoint only, chosen without looking at H10: either the last one, or one chosen on a validation set split off separately from the non-held-out part of sft_v1.
  - Comparing several checkpoints on H10 and picking one is not allowed; that would bring in a winner's bias.
- **Offline threshold** (before 08:00Z). All three must pass:
  - **AL_new ≥ 1.06 × AL_base**: the same position list, the same code, the primary reading;
  - **[F added]** AL_new ≤ T0_mc + 0.05;
  - **[F added]** |AL_mc − AL_exp| ≤ 0.10.
  - In addition, the ratio for AL_exp is only reported.
- **Smoke run** (before 12:00Z):
  - Upload a private model and keep it private.
  - **[F added]** Before uploading, check that the new draft's tensor names, shapes and dtypes are exactly the same as albucino's.
  - Run one Kaggle commit smoke run, not a submission. The notebook's diff against S9 `39fc6f22` may contain only the source and path of the draft model.
  - Following E208's definition, T is computed by `research/agi3/analysis_D/e208/parse_serve_log.py` (`261c42d6…`). Require T ≥ 728.1, T − 693.4 > 10.8, and 0 retracts.
  - The accept_len on the Kaggle side is only reported. **[F added]** The server log must show that the new draft was actually loaded.
- **Before 14:00Z**: the coordinator asks the user whether to submit. If any step was not achieved, stop.

## 3. How it enters the final selection once it has passed: [F added] counted as a run of S9
- **Reasons**:
  - Verification with NEXTN topk 1 and threshold 1.0 is lossless residual sampling (`ROUND2_PREREG.md` §M.0); changing only the draft does not change the distribution of any token, only the speed.
  - Treating it as a new configuration with its own m would throw away S9's data: a strictly faster S9 could look worse in the table than S9 itself, which makes no sense.
  - Precedent: v1, v2 and v3a of the v2 family were treated as one configuration.
  - This registration comes before any score; it is not an adjustment after the fact.
- **Therefore**:
  - In the 11-01 slot, it is the "one more S9 draw" in the ARC3_SLOT_1101 table (`3fded4ec`), only run with the new draft. At σ = 2 the gain is recorded as +0.67; the benefit of the speed-up is not counted, which is conservative.
  - After it scores, it is treated as one run of S9: m 29.5, veto line 25.5 at σ = 2, and the final selection then follows §5 of that table.
  - If CP1–CP3 all pass, F recommends submitting this version in the 11-01 slot in place of an ordinary extra S9 draw; if any fails, submit an ordinary extra S9 draw as the table says. Either way, ask the user first (DECISIONS 10-31 ~12:4x: the user wants to decide on 11-01 after the reset).
- **Timing**: if submitted at 14Z, the score comes about 9.3 h later, that is, 11-01 about 23:20Z. If it is invalid (cd2245ca), one more submission is still possible on 11-02 ≤ 12Z.

## 4. What the conclusion must state
- The positions of the offline AL are H10's logs, not Kaggle's games. CP2 only checks the total; the speed at deployment is judged by the T of the Kaggle smoke run.
- Expectation [E]: a conditional gain of LB +0.3 to +1.2, with a probability of about 20–25% of passing the threshold (the estimate of B / the coordinator). This is not a measured value.
