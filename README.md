# Built Once, Used Where? Self-Written Tools Across ARC-AGI-3 Levels

Materials for our ARC Prize 2026 Paper Track entry (ARC-AGI-3 track). The paper is [`paper.pdf`](paper.pdf); its source is `drafts/PAPER_FINAL.md`. Paths in the paper are relative to the root of this repository.

The paper asks whether a code-writing ARC-AGI-3 agent reuses the Python functions it writes on later levels, and whether it reuses them more on levels that only recombine known elements. The labels, parser, analysis code, pre-registration and frozen outputs are here.

## Contents

| Path | What it is |
|---|---|
| `paper.pdf` | The paper |
| `PREREGISTRATION.md`, `FREEZE.txt`, `frozen_history/` | Pre-registration with its amendments, and the SHA-256 of every frozen file; the `.en.md` copies translate its five quotations in Chinese (see Languages) |
| `analysis/` | Transcript parser and frozen analysis (`prepare_units.py`, `analyze_reuse.py`, `analyze_reuse_clearing.py`) with their synthetic tests; the Amendment 4 versions in `frozen_a4/`; the R-07 gate (`gate_only.py`); the R-09 analysis of the ARC-AGI-2 side study (`jgv2_analyze.py`) |
| `level_annotation/` | First frames of all 183 public levels (`frames/`), the S/V/N labels of the 158 levels from level 2 on (`manual_labels.csv`), the table the analysis reads (`levels.csv`) and the rendering script |
| `level_annotation/human_check/` | The blind human check behind Table A2 (see below) |
| `runs/arc3-paper-v1cfg-v1/` | The primary run R-06: `benchmark.json.gz`, the 50 transcripts, `summary.txt` and the sealing manifest `SHA256SUMS.txt` |
| `results/` | Outputs of the frozen analysis: `r06_v1cfg_v1/` (R-06, hashes in `OUTPUTS.sha256`), `s7_franzen_m2_v3/` (parent-configuration replication), `r07_muse_a0/` (R-07 gate), `human_check_20261107/` (Table A2) |
| `R06_ADDENDUM_HARD_STOP.md`, `R10_DECODE_HEADROOM_PLAN.md`, `JGV2_REGISTRATION*.md`, `registrations/` | Registrations for the R-06 hard stop and the side studies; `.sha256` files where the registration had one; an English translation (`.en.md`) beside each one written in Chinese |
| `third_party/franzen_m2_v3/` | Our hash manifests of Franzen's public runs, used for the replication |
| `sft_v3/heldout_late_w96x_h10.jsonl` | The held-out windows read in Appendix E |
| `drafts/` | The paper source and its PDF build script; Figure 1 as a draw.io source (`figures/overview.drawio`) with its SVG and PNG exports; the scripts for Figures 2–4 (`make_figures.py`, `make_forest.py`, both run from the repository root) and their SVGs; the case-selection script; the Writeup cover (`WRITEUP_cover.png`) with its draw.io source |
| `MANIFEST.sha256` | SHA-256 of every other file in this repository |

## Checking and reproducing

The analysis uses only the Python standard library. From the repository root:

```bash
shasum -a 256 -c <(tail -21 FREEZE.txt | head -20)
```

should report 20 lines OK, and

```bash
shasum -a 256 -c MANIFEST.sha256
```

checks every file here. `runs/arc3-paper-v1cfg-v1/SHA256SUMS.txt` was written when the run was sealed and lists the hashes of the run's files before compression, including files not copied here; `gzip -dc` a file to compare it.

The commands are in Appendix C of the paper. Step 5 (`analyze_reuse_clearing.py`) also reads the 50 per-game request logs `*_requests.jsonl` (about 0.6 GB compressed), which are not in this repository. They are in the output of the Kaggle notebook `kefeiyan/arc3-paper-v1cfg`, version 1; put them, plain or gzipped, in `runs/arc3-paper-v1cfg-v1/`. Steps 1 to 4 need nothing outside this repository.

## Human check

Two project members labelled the same 44 levels from 7 games, each on their own, in `level_annotation/human_check/blind_label.html`. The page works offline, shows only first frames and the label definitions, and contains no AI label. It is in Chinese, the language the annotators worked in; `blind_label.en.html` is the same page in English (see Languages).

- `labels_human_A.csv` and `labels_human_B.csv` are their files. The `annotator` column is coded A and B, and the mapping to names is not published. In the `note` column, `unsure` stands for the page's "unsure" box, which the page wrote in Chinese. Nothing else was changed. `labels_human.csv` is the blank template.
- To reproduce Table A2, run from `level_annotation/human_check/` (we used Python 3.12.8):

```bash
python3 -I -B recompute_u2_human.py --check
python3 -I -B kappa.py ../manual_labels.csv labels_human_A.csv
python3 -I -B kappa.py ../manual_labels.csv labels_human_B.csv
python3 -I -B recompute_u2_human.py labels_human_A.csv
python3 -I -B recompute_u2_human.py labels_human_B.csv
python3 -I -B kappa.py labels_human_A.csv labels_human_B.csv
python3 -I -B recompute_u2_human.py ../manual_labels.csv
```

The first command rebuilds the R-06 units from `runs/` and checks that the frozen analysis reproduces `results/r06_v1cfg_v1/analyze_reuse.json` byte for byte. The last two give the descriptive A–B row and the AI-label row; in the A–B table the header "AI" stands for file A.

- `results/human_check_20261107/` was produced with these coded files in this layout; `u2_A.json` and `u2_A.txt` were produced again on 2026-11-09, after the note change, and only the recorded hash of A's file changed. Its numbers are byte-identical to the first computation on the uncoded files; only file names and label-file hashes differ.

## How this copy differs from our working copy

- `level_annotation/human_check/recompute_u2_human.py`: the `RUN` line points at `runs/arc3-paper-v1cfg-v1`, and one docstring line says so. Nothing else changed.
- The two human label files: the annotator field, and in seven notes of A's file the Chinese word for "unsure", written here as `unsure` (see above). No label changed, and the Table A2 commands give the same numbers.
- The two files in `registrations/` were kept elsewhere in our project. They are byte-identical, and their hashes match the ones the paper cites.
- Not included: the R-08 registration of the ARC-AGI-2 side study; Appendix D gives its hash.
- Not included: our internal run log `RUN_REGISTER.md`, which holds internal coordination notes; the R-06 request logs and other run outputs (prompts, artifacts, server logs); Franzen's run data; and the Appendix E code (`mtp_cal.py` and the modules it imports), which the paper identifies by hash.
- Added for this copy: the English translations (`.en.md`), and the English labelling page `blind_label.en.html` with the script that made it, `make_label_page_en.py` (see Languages).
- Some sealed outputs contain absolute paths from the machine that ran them. They are unchanged because their hashes are recorded.

## Languages

Everything we wrote for this repository is in English. Some files are kept exactly as they were registered or used, and they contain Chinese:

- **Registrations.** `JGV2_REGISTRATION.md`, `JGV2_REGISTRATION_ADDENDUM1.md`, `R06_ADDENDUM_HARD_STOP.md`, `R10_DECODE_HEADROOM_PLAN.md` and the two files in `registrations/` were written in Chinese. Each has an English translation beside it, named `<name>.en.md`, which states the SHA-256 of its original. The originals are the registered versions and their hashes are recorded, so they are not changed; where a translation and its original differ, the original governs.
- **Pre-registration.** `PREREGISTRATION.md` and `frozen_history/PREREGISTRATION.after_a4.md` are in English apart from five quotations in Chinese: four replies from other agent workstreams about what they had computed before the analysis, and the user's approval of the R-06 run. `PREREGISTRATION.en.md` and `frozen_history/PREREGISTRATION.after_a4.en.md` are full copies with those quotations translated; every other line is unchanged.
- **Human check.** The annotators worked in Chinese. `level_annotation/human_check/blind_label.html`, the page they used, and `build_label_page.py`, the script that built it, are unchanged and contain Chinese. `blind_label.en.html` is the same page with its interface, including the label definitions, in English; `make_label_page_en.py` makes it from `blind_label.html` and checks that only the Chinese text changes. The AI annotator's definitions were also in Chinese, and Section 4 of the paper gives them in English.
- **Transcripts.** The transcripts in `runs/arc3-paper-v1cfg-v1/transcripts/` are the model's output, copied verbatim. In two of them the model itself wrote a Chinese character (`ka59-38d34dbb_p0`) or a full-width parenthesis (`m0r0-492f87ba_p1`); we left them as they are.

## Notes

- AI coding agents wrote most of the code and drafted the text, as the paper states.
- The level frames and transcripts show the ARC-AGI-3 public games from the competition data, which the competition rules list under Apache 2.0. `sft_v3/heldout_late_w96x_h10.jsonl` is derived from Franzen's public runs.
- License: CC BY 4.0, see `LICENSE`.
