# JGV-2 补充登记 · 附注 1（入队前）

- **写定**：2026-10-29T11:59:01Z（写之前运行了 `date -u`），工作流 G。冻结后不改，哈希记在 `.sha256` 和 RUN_REGISTER。
- **依据**：F 的审查 `research/review/REVIEW_JGV_SUPP_20261029.md`（11:55:44Z），由 E 转达。
- **数据状态**：4 个新臂都还没有入队。
- **与原登记的关系**：不改 `JGV2_REGISTRATION.md`（sha256 `19483062…d9a5`）的任何读数和判定规则，只补下面三点。

## 1. 12 轮的两臂可能先被 token 卡住

- 每题的 token 预算仍是 64k：`episode_tokens` 和 `task_tokens` 都是 64000。
- 放宽到 12 轮后，episode 很可能先撞到 token 上限。
- 所以 D2 量的是"token 上限不变时，把轮数上限从 6 放到 12"的效果，不是"不限轮数"的效果。

## 2. 新增只报告的读数 D6

D6 不进任何判定。

- **内容**：T1、V、T12、V12 各臂的 episode 按结束方式分三类：撞到轮数上限（harness 状态 `turns`），撞到 token 上限（状态 `tokens` 或 `task_tokens`），以及其他。报前两类各占多少比例，token 一类再分开报 `tokens` 和 `task_tokens`。其余各臂也一并列出。
- **来源**：各臂 `run.json` 的 summary 里的 `statuses` 和 `episodes`。`jgv2_analyze.py` 已经把它们存进输出的 `run_summaries`，脚本不用改。
- **读法**（采纳 F 的提示，事先写定）：
  - 6 轮的臂如果很少撞到轮数上限，T12、V12 与原臂的差别只能读作"token 上限不变时，放开轮数几乎没有作用"；
  - 只有当原臂常撞轮数上限（如 V 的 65/176），而 12 轮的臂明显少撞时，D2 才能用来检验"轮数上限压住了图像"。

## 3. 分析在哪里跑

- runner 末尾不跑分析。F 已核过这一点，目的是不覆盖 R-08 的 `jgv_result.json`。
- 第二组跑完后，在 B200 上单独执行原登记 §3 的命令，输出写到 `jgv2_result.json`，不覆盖 `jgv_result.json`。
- 如果到时箱子已经销毁：把 7 个臂的 `submission.json`、`run.json` 和 solutions 拉回，由 G 在本机跑一次（单步，只需几秒），并记录下来。

运行顺序仍照原登记 §2：先跑 T3 + V2，再跑 T12 + V12。
