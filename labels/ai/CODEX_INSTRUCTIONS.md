# 用 Codex 做 LLM 标注的操作说明

## 准备（只做一次）

1. 在 Codex 里打开本项目文件夹（`NLP/Final Project`），选择模型 gpt 6 luna。
2. 把 Codex 界面显示的完整模型名和版本记到 `labels/ai/run_log.csv`。如果界面里能看到设置（推理强度等），一并记下，后续不要再改。
3. 提示词文件：`prompts/label_prompt_v1.md`，SHA256 见同名 `.sha256` 文件。跑任何一批之前，都不要修改这个文件。

## 每一批的操作

在 Codex 里粘贴下面这段话，只改尖括号里的两个路径：

```
请严格按照 prompts/label_prompt_v1.md 的要求标注 <输入文件，例如 labels/ai_inputs/dev.jsonl>。
逐条阅读每个条目并亲自判断，不要编写或运行任何代码、关键词规则或正则表达式来打标签，不要上网查找。
对输入的每一行输出一行 JSON，顺序与输入相同，写入 <输出文件，例如 labels/ai/gpt-6-luna__v1/dev_batch01.jsonl>。
除了这个输出文件，不要修改任何其他文件。完成后告诉我写了多少行。
```

如果一个文件太长、Codex 做不完，可以要求它分几次写入 `dev_batch01.jsonl`、`dev_batch02.jsonl` 等，文件名都以 split 名开头。

## 顺序（不能颠倒）

1. 开发集：`labels/ai_inputs/dev.jsonl`（100 条），输出到 `labels/ai/gpt-6-luna__v1/`。
   运行 `python src/annotation/score_ai.py labels/ai/gpt-6-luna__v1 dev` 看表现。
   如果需要改提示词，另存为 `label_prompt_v2.md`，输出目录相应改为 `…__v2`，只在开发集上重跑。每个版本的开发集表现都保留。
2. 冻结提示词版本后，测试集 `labels/ai_inputs/test.jsonl`（260 条）只跑一次。
3. 自身一致性：用同一个提示词版本，把测试集的前 26 条（10%）再跑一次，写到 `labels/ai/gpt-6-luna__vN_repeat/`。然后运行：
   `python src/annotation/score_ai.py labels/ai/gpt-6-luna__vN test labels/ai/gpt-6-luna__vN_repeat`
4. 正式编码：`labels/ai_inputs/corpus_batch_001.jsonl` 至 `corpus_batch_058.jsonl`，共 11,431 条，每批 200 条，用冻结的提示词版本。
   输出到 `labels/ai/<冻结版本的运行目录名>_corpus/`，文件名与输入相同，例如 `corpus_batch_001.jsonl`。
   每批跑完后可以运行 `python src/annotation/check_corpus_batch.py <输出目录>` 检查格式和漏条。

## 注意

- 不要把 `labels/adjudicated.csv`、`labels/sample_key.csv` 或金标准相关文件给 Codex 看。
- Codex 无法设定温度，这一点在报告中如实说明，并用第 3 步的重复运行一致率来量化随机性。
