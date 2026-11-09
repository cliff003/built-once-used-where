> English translation of `registrations/T0_CEILING_PREREG_B_20261030.md` (sha256 `9e2a8a79b31193e9b5cae6823e034f1ef7fb6a1e0c9ed1b11fc75ff744b00442`). The original, written in Chinese, is the registered version; where the two differ, the original governs. Translated on 2026-11-09.
>
> Translator's note: quotations are translated as well and marked "(translated)". Single capital letters (A–G) are the project's internal agent workstreams, for example F for independent review and G for the paper; "the coordinator" is the session that coordinated them. The tags [V], [C] and [E] mean checked by the writer, claimed by someone else (a letter after C names the source) and estimated. COLLAB-0xx are rows of the internal coordination board, and DECISIONS and RUN_REGISTER are internal logs. Paths that are not in this repository refer to the project's private working tree.

---

# ARC3 T0 ceiling test, registered again (measurement only, no training; 1 PACE H200)

- **Frozen**: 2026-10-30T05:07:07Z (`date -u`), F (COLLAB-014). The coordinator revived this item following the user's "don't waste PACE" (translated) [C D]. It replaces the withdrawn `T0_CEILING_PREREG_20261029.md` (71fe79e9).
- **Files** [V local sha]: t0_tf.py `f6d024eb` (unchanged), t0_ceiling.sbatch `e6b1c408`, D's draft registration research/agi3/analysis_D/t0/T0_PREREG.md.
- **F chooses (a)**: the original specification required "reproduce Kaggle's 2.62–2.67 ± 0.1 with the existing draft" (translated), but the HF forward pass has no MTP layer, so this cannot be done. D's three conditions are used instead:
  - **C1**: the sampling setting is identifiable. Among T ∈ {0.7, 1.0} (both with top-k 20 and top-p 0.95, in SGLang's filtering order), at least one T makes the share of logged tokens that fall outside the support set ≤ 1%.
  - **C2**: at the T selected by C1, |T0_mc − T0_exp| ≤ 0.10. T0_exp is the mean of 64 fixed-seed replays, each drawing a Bernoulli on the processed p(argmax).
  - **C3**: T0_mc ≥ 2.62 (the ceiling should not be below the measured value of the existing draft).
  - **Notation**: T0_mc = generated tokens ÷ verify steps, including the 1 extra token after verification, the same notation as SGLang's accept_len. C3 also guards the notation: if the notation is wrong, C3 will most likely fail.
- **Verdict**: C1–C3 all pass and T0_mc ≥ 2.95 → draft distillation is "worth doing"; otherwise → not worth doing.
- **Limitations, which the conclusion must state**:
  - the simulator was not calibrated against the existing draft, and C1–C3 only check internal consistency and a lower bound, so the absolute value of T0 may be biased;
  - the user has decided not to rent more GPUs, so even a "worth doing" verdict will not start training automatically; it is for information and for the paper only.
- Tonight the user has cleared the permission gate for PACE jobs; E checks the resources.
