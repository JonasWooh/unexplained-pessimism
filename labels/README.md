# labels/

人工标注（R3.4）的交接文件，生成脚本为 `src/process/export_labels.py`。原始工作簿保留在 `annotation/`。

| 文件 | 内容 |
|---|---|
| `sample_for_annotation.csv` | 30 条校准样本加 360 条正式样本，即标注员看到的盲标文本，含 split（calibration/dev/test） |
| `sample_key.csv` | 每条的来源、分层、日期、URL、抽样权重；不给标注员看 |
| `sampling_design.json`、`sampling_frame_sizes.csv` | 抽样设计（种子 20261015）和各格抽样框大小 |
| `annotator_A.csv`、`annotator_B.csv` | 两名人工标注员各自独立的标注（项目负责人声明：均为人工完成，未使用 AI 或脚本） |
| `annotator_A_time_log.csv`、`annotator_B_time_log.csv` | 用时记录，原样保留；B 的记录是补录估计，非实测 |
| `agreement_summary.csv`、`confusion_matrices.csv` | Cohen's κ、Krippendorff's α、原始一致率，按 all/dev/test/全国/地方/社交 分列 |
| `adjudication_log.xlsx` | 593 个分歧项的裁决结果及书面理由 |
| `adjudicated.csv`、`adjudicated_calibration.csv` | 金标准 v1 |
| `gold_overview.json` | 裁决统计 |
| `ai/` | 留给 LLM 标注输出，命名为 `<model_id>__<prompt_version>.jsonl` |

评估口径（用户 2026-10-16 确认）：
- 金标准中 relevant=unsure 的 32 条（开发集 8 条、测试集 24 条），不计入 relevant 的精确率和召回率，单列数量；其余维度照常评估。
- 只在 100 条开发集上调整提示词；冻结后在 260 条测试集上评估一次。
