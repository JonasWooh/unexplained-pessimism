# How to run LLM labeling with Codex

## Setup (once only)

1. Open this project folder (`NLP/Final Project`) in Codex and select the model gpt 6 luna.
2. Record the full model name and version shown in the Codex interface in `labels/ai/run_log.csv`. If the settings (reasoning effort, etc.) are visible in the interface, record them too, and do not change them afterwards.
3. Prompt file: `prompts/label_prompt_v1.md`; its SHA256 is in the `.sha256` file of the same name. Do not modify this file before running any batch.

## Steps for each batch

Paste the following text into Codex, changing only the two paths in angle brackets:

```
Label <input file, e.g. labels/ai_inputs/dev.jsonl> strictly according to the requirements of prompts/label_prompt_v1.md.
Read each item one by one and judge it yourself; do not write or run any code, keyword rules or regular expressions to assign labels, and do not look anything up online.
For each input line, output one line of JSON, in the same order as the input, and write it to <output file, e.g. labels/ai/gpt-6-luna__v1/dev_batch01.jsonl>.
Do not modify any file other than this output file. When you are done, tell me how many lines you wrote.
```

If a file is too long for Codex to finish, you can ask it to write in several parts to `dev_batch01.jsonl`, `dev_batch02.jsonl`, etc.; every file name starts with the split name.

## Order (must not be reversed)

1. Development set: `labels/ai_inputs/dev.jsonl` (100 items), output to `labels/ai/gpt-6-luna__v1/`.
   Run `python src/annotation/score_ai.py labels/ai/gpt-6-luna__v1 dev` to see performance.
   If the prompt needs changes, save it as `label_prompt_v2.md`, change the output directory to `…__v2` accordingly, and rerun only on the development set. Keep the development-set performance of every version.
2. After the prompt version is frozen, run the test set `labels/ai_inputs/test.jsonl` (260 items) only once.
3. Self-consistency: with the same prompt version, run the first 26 items (10%) of the test set again and write them to `labels/ai/gpt-6-luna__vN_repeat/`. Then run:
   `python src/annotation/score_ai.py labels/ai/gpt-6-luna__vN test labels/ai/gpt-6-luna__vN_repeat`
4. Production coding: `labels/ai_inputs/corpus_batch_001.jsonl` to `corpus_batch_058.jsonl`, 11,431 items in total, 200 items per batch, using the frozen prompt version.
   Output to `labels/ai/<run directory name of the frozen version>_corpus/`, with the same file names as the inputs, e.g. `corpus_batch_001.jsonl`.
   After each batch you can run `python src/annotation/check_corpus_batch.py <output directory>` to check the format and missing items.

## Notes

- Do not let Codex see `labels/adjudicated.csv`, `labels/sample_key.csv` or any gold-standard files.
- Codex cannot set the temperature; state this plainly in the report, and quantify the randomness with the agreement rate of the repeat run in step 3.
