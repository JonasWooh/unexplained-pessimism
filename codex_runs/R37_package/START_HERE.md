# R3.7 替换测试：Codex 运行说明

本目录只含冻结提示词 v2 和 4 个输入批次，每批 120 条，共 480 条。请把整个目录复制到项目文件夹以外（例如 `NLP/LLM_R37_Run`），在复制后的目录里打开 Codex。
模型和推理设置与正式编码完全相同：GPT 6 luna，推理强度 high。

- 提示词：`prompts/label_prompt_v2.md`，SHA256 = 9f95f20aa319fff0ecf6c4a29d2ab81bfcc9503d72a581ea64cc6a661b6e16bd
- 输入：`inputs/r37_batch_1.jsonl` 至 `r37_batch_4.jsonl`
- 输出：`outputs/r37_batch_N.jsonl`（与输入同名）；运行日志：`outputs/run_log.csv`

## 发给 Codex 的启动 prompt（一次发送）

```text
请完整读取本目录 START_HERE.md，完成 4 个批次的标注。
每个批次交给一个独立的新上下文子代理（spawn_agent 的 fork_turns="none"），一个子代理只处理一个批次，不得读取其他批次的输入或输出，也不得读取主对话历史。最多可同时运行 4 个子代理。
子代理继承当前模型和推理设置，不指定、不切换模型。
子代理必须完整读取 prompts/label_prompt_v2.md 并核对 SHA256，逐条亲自阅读 text（context 只用于理解评论）后判断标签，按提示词的格式对每条输入输出一行 JSON，顺序与输入相同，写入 outputs/ 下同名文件。
不得用代码、关键词、正则或规则生成标签，不联网；代码只可用于读写文件和格式校验。
主 agent 只负责调度和非语义核验：每个输出的 ID 序列与输入完全一致、17 个键齐全、取值合法、证据摘录能在对应 text 或 context 中逐字找到。发现问题时交回原子代理复读原文修正，主 agent 不替它改标签。
主 agent 把每个批次的开始和结束时间（America/New_York，带时区）、条数、核验结果写入 outputs/run_log.csv，表头为：
run_dir,split,files,model_name_as_displayed,settings,prompt_file,prompt_sha256,started_local,finished_local,notes
其中 run_dir 写 codex__v2_r37，split 写 r37；模型名和设置如界面不可见就写“不可见”。
4 个批次全部核验通过后报告各批条数和核验结果；有任何批次未完成时如实报告，不得宣称完成。
```

## 完成后

把 `outputs/` 整个文件夹复制回项目的 `labels/ai/codex__v2_r37/`，告诉 Claude 即可。
