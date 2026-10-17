# R3.7 replacement test: Codex run instructions

This directory contains only the frozen prompt v2 and 4 input batches of 120 items each, 480 items in total. Copy the whole directory outside the project folder (for example `NLP/LLM_R37_Run`) and open Codex in the copied directory.
The model and reasoning settings are exactly the same as in production coding: GPT 6 luna, reasoning effort high.

- Prompt: `prompts/label_prompt_v2.md`, SHA256 = 9f95f20aa319fff0ecf6c4a29d2ab81bfcc9503d72a581ea64cc6a661b6e16bd
- Input: `inputs/r37_batch_1.jsonl` to `r37_batch_4.jsonl`
- Output: `outputs/r37_batch_N.jsonl` (same name as the input); run log: `outputs/run_log.csv`

## Startup prompt for Codex (send once)

```text
Read this directory's START_HERE.md in full and complete the labeling of the 4 batches.
Give each batch to a separate subagent with a fresh context (spawn_agent with fork_turns="none"). Each subagent handles only one batch and must not read the inputs or outputs of other batches, nor the main conversation history. At most 4 subagents may run at the same time.
Subagents inherit the current model and reasoning settings; do not specify or switch models.
Each subagent must read prompts/label_prompt_v2.md in full and verify its SHA256, read each text itself item by item (context only to understand comments) before deciding the labels, output one line of JSON per input item in the prompt's format, in the same order as the input, and write it to the file of the same name under outputs/.
Labels must not be generated with code, keywords, regular expressions or rules; no internet access; code may be used only for reading and writing files and for format validation.
The main agent is responsible only for scheduling and non-semantic verification: each output's ID sequence exactly matches the input, all 17 keys are present, values are valid, and evidence quotes can be found verbatim in the corresponding text or context. When a problem is found, it is sent back to the original subagent, which rereads the original text and fixes it; the main agent does not change labels on its behalf.
The main agent writes the start and end time of each batch (America/New_York, with time zone), the item count and the verification result to outputs/run_log.csv, with the header:
run_dir,split,files,model_name_as_displayed,settings,prompt_file,prompt_sha256,started_local,finished_local,notes
where run_dir is codex__v2_r37 and split is r37; if the model name and settings are not visible in the interface, write "not visible".
After all 4 batches pass verification, report the item count and verification result of each batch; if any batch is not complete, report this truthfully and do not claim completion.
```

## After completion

Copy the whole `outputs/` folder back to the project's `labels/ai/codex__v2_r37/` and tell Claude.
