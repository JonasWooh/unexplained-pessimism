# One main conversation that completes all frozen v2 labeling automatically

These instructions replace the earlier entry point that required opening several conversations by hand. Open only this parent directory, LLM_Labeling_v2_Run, in Codex and use a single working conversation.
The main agent handles scheduling, structural verification and log aggregation; independent labeling subagents do the actual reading and label decisions.
You do not need to send a message for each batch, switch folders by hand, or start new test/repeat conversations.
This change only reorganizes how the task is run; no labeling has been started, and neither the frozen prompt nor any input has been modified.

## The complete startup prompt, sent only once

First, select in the interface the same model and reasoning settings that were used for the evaluated v2; the model selection does not change automatically because the prompt names a particular model.
The model description below may use the wording shown in the interface; when no verifiable information is available, record that truthfully and do not guess the model version.
In a single conversation in this directory, send the whole code block at once:

```text
Read this directory's START_HERE.md in full and complete all frozen v2 labeling according to its "Main agent execution protocol" and "Labeling subagent protocol".
I explicitly authorize you to use labeling subagents with independent contexts and to schedule them automatically in the order test set → independent repeat → production coding; I do not need to open other chats by hand or confirm each batch.
Create a persistent goal for this task: complete the 260 test items, the 26 independent repeat items, and the 11,431 production-coding items in 58 batches, plus file-by-file verification and aggregation of the real run logs; end the goal only after all of this is done.
Subagents must use a new context that does not inherit the current conversation history (spawn_agent with fork_turns="none"), and receive only the protocol for their assigned task, the frozen prompt path and the input/output paths; they must not receive any existing labels or answers from other stages.
All labeling subagents inherit the currently selected model and reasoning settings; do not specify another model, and do not switch or upgrade models automatically; do not turn a subtask into a new chat that the user has to operate.
Model and settings description: use the model and settings actually selected in this conversation, which match the development-set v2 run; the log records only verifiable information from the runtime environment or provided by me, and if it is not visible, state explicitly that it is not visible.
The main agent only does scheduling, non-semantic validation, verbatim archiving and real log recording; it does not fill in labels on behalf of subagents, does not read the gold standard, does not change v2, and does not pass the first test results to the repeat subagent.
The test set and the repeat set each get exactly one independent labeling task, and the two run strictly one after the other; the production-coding stage is scheduled as 58 non-overlapping batches, with at most 3 labeling subagents at a time, and actual concurrency limited by available slots.
Each batch has only one writer; when a batch is done, schedule the next one automatically. Do not ask me after each batch whether to continue, and do not stop and wait for me at stage boundaries.
Use the existing local files and file read/write tools; do not call model APIs and do not go online. Code may only process files, validation, hashes, logs or verbatim aggregation; it must not generate labels with keywords, regular expressions, rules or programs.
Announce completion only after all 60 prediction files, all 11,717 records and the run logs have passed verification; if a real quota or permission interruption occurs, keep the progress and report the blocker clearly, and do not falsely report completion.
```

11,717 = 260 + 26 + 11,431; 60 files = test + test_repeat + 58 production batches.
"One conversation" means one main conversation that schedules all the work automatically; it does not mean one model context personally completes both the test and the repeat.
If the execution environment has no tool for subagents with independent contexts, state this limitation before labeling starts; the same context must not read the first answers and then pass off its work as an independent repeat.

## Main agent execution protocol

### 1. Fixed files, versions and responsibilities

- Work only inside this execution package; do not read the original project, other chats, human labels, the gold standard, the source key, or the development-set predictions.
- Fixed prompt SHA256: 9f95f20aa319fff0ecf6c4a29d2ab81bfcc9503d72a581ea64cc6a661b6e16bd. Read and verify the copy for each stage; do not modify the prompt or the category definitions.
- The main agent may use code to check input IDs, file counts, hashes and output structure; do not print predicted labels into the main conversation, and do not use them as context for any subagent.
- Give the subagent the original text of the "Labeling subagent protocol" below together with the specific configuration of its task; do not let the subagent read the whole START_HERE or the files of other stages.
- Dispatch with fork_turns="none", and omit the model and reasoning_effort parameters so that the current settings are inherited; it is forbidden to inherit the main conversation history, to reuse the first test agent for the repeat, or to send the first test answers to the repeat agent.
- Subagents do not delegate further to subagents. The main agent keeps only the concurrent tasks that are needed and releases slots that can be released once tasks finish; it does not schedule later stages early.
- The above are constraints on context and read/write scope; they do not claim that the shared file system provides an extra permission sandbox.

### 2. Stage order and exact paths

Stage 1: one new-context labeling agent, 260 items, split=test.
- Working scope: 01_test.
- Prompt: 01_test/prompts/label_prompt_v2.md.
- Input: 01_test/labels/ai_inputs/test.jsonl.
- Output: 01_test/labels/ai/codex__v2_isolated_r1/test.jsonl.
- Start stage 2 only after all 260 items are complete and verified; do not rerun the full test set or change answers based on the gold standard.

Stage 2: another labeling agent with a completely new context, 26 items, split=test, with notes stating independent repeat r2.
- Working scope: 02_repeat.
- Prompt: 02_repeat/prompts/label_prompt_v2.md.
- Input: 02_repeat/labels/ai_inputs/test_repeat.jsonl.
- Output: 02_repeat/labels/ai/codex__v2_isolated_r2/test_repeat.jsonl.
- The 26 items are a fixed test subset drawn at random with seed 20261015; they are not the first 26 test items, and must not be resampled.
- Do not let this agent access 01_test, the first test agent, the first predictions or the main conversation history; start stage 3 after everything is verified.

Stage 3: 58 non-overlapping batches, split=corpus, at most 3 agents running concurrently.
- Use only the inputs in 03_corpus_all; do not also schedule the alternative copies in the parallel directory.
- Prompt for batch NNN: 03_corpus_all/prompts/label_prompt_v2.md.
- Input for batch NNN: 03_corpus_all/labels/ai_inputs/corpus_batch_NNN.jsonl.
- Output for batch NNN: 03_corpus_all/labels/ai/codex__v2_isolated_r1_corpus/corpus_batch_NNN.jsonl.
- NNN runs from 001 to 058; the first 57 batches have 200 items each and batch 058 has 31 items, 11,431 items in total.
- Each agent gets only its own batch and write access to the corresponding output; after a batch is done, the main agent verifies it, updates the log, and then dispatches the next batch automatically.
- Do not open a fixed set of 60 parallel agents; keep at most 3 active labeling tasks according to the available slots.

### 3. Checkpoints and resuming the same run

- Before the initial dispatch, check the specified output; create a new task only if there is no output.
- If a complete file exists whose structure, IDs and evidence are all valid, do not relabel or overwrite it; record the reuse and its verifiable original log.
- If an incomplete file exists that consists of complete JSON lines forming a valid prefix of the input order, automatically continue the same task with the missing suffix; do not relabel items that are already done.
- Resuming the test or the repeat still belongs to the original single run and does not start a new full round of predictions; the log notes resumed and the original output that was carried over.
- Even if the first test results exist, they must not be given to the repeat subagent; when the repeat task resumes, it may see only its own earlier repeat prefix.
- If an existing file is invalid (wrong order, duplicates, invalid JSON, etc.), report the exact problem; do not silently delete, reorder or rewrite existing results.
- A completed task must not be rerun from scratch because the main conversation was compacted or some other task was interrupted.
- A genuine resource interruption should keep the valid files and logs; there is no guarantee that no manual recovery will be needed after a platform quota interruption, but do not stop work on your own because of ordinary segmentation or stage boundaries.

### 4. Real logs: one main writer

- The main agent alone maintains labels/ai/run_log.csv in this parent directory; subagents must not write to this one CSV concurrently.
- Each actual attempt of each subtask is assigned a unique log file, for example labels/ai/job_logs/test_a01.csv, repeat_a01.csv, corpus_001_a01.csv.
  The main agent gives the absolute path of that file to the corresponding agent as its only additional log write permission; no other agent may write this log.
- At the start, the subagent creates one row for this attempt, and updates the same row when it finishes or clearly fails; if interrupted, the end time is left empty.
- The main agent reads the separate logs and aggregates them serially into run_log.csv, distinguishing attempts by log file identity; do not append the same row twice because of repeated polling.
- Keep the header in the original project format:
  run_dir,split,files,model_name_as_displayed,settings,prompt_file,prompt_sha256,started_local,finished_local,notes
- split is test or corpus; for the first run and the repeat, run_dir is codex__v2_isolated_r1 and codex__v2_isolated_r2 respectively, and files is the actual input name.
- run_dir records the relative directory labels/ai/... of the final archive; prompt_file records the actual prompt path of the stage; settings records only verifiable settings.
- Times are the actual ISO8601 times in America/New_York with UTC offset; it is forbidden to invent durations, fabricate completion times after the fact, or treat an invisible model name as verified.
- notes states the agent task ID, completion status, actual item count, resume/reuse situation, and any genuine resource interruption.

### 5. File-by-file verification and verbatim archiving

- Check that every output matches the complete ordered ID sequence of its own input, with the exact item count and no omissions or duplicates.
- Check the 17 core top-level keys, the English enum values, emotional intensity as a string, the null rule for non-relevant items, and the topic and actor-direction dependencies.
- Check that claim_text and all non-empty evidence are verbatim fragments of the corresponding text or of the context where the prompt allows it, without ignoring case or replacing whitespace.
- Validation code only reports structure, ID and quote problems; it must not derive labels from the data or fill in labels automatically by program. Local problems are sent back to the original labeling agent, which rereads the original text and fixes them; no reference answers are provided.
- The original project's batch checker is not in this package; do not access the original project or the gold standard to run it, and do not replace the checks above with something that only displays ok.
- After a stage is complete, archive the valid outputs byte for byte into this parent directory:
  labels/ai/codex__v2_isolated_r1/test.jsonl
  labels/ai/codex__v2_isolated_r2/test_repeat.jsonl
  labels/ai/codex__v2_isolated_r1_corpus/corpus_batch_001.jsonl to 058.jsonl
- Copy verbatim and compare hashes; do not rewrite labels, and do not merge the 58 batches into one file. An existing archive file with the same name and the same hash may be reused; if the hash differs, report the conflict.
- After all 60 files are verified, give a final report of the item counts of each stage, coverage of the 58 batches, the strict validation results, and the central output and log paths; do not score automatically, analyze the monthly index, or modify the frozen prompt.

## Labeling subagent protocol (passed verbatim at dispatch, plus the specific configuration of the task)

You are responsible only for the input file and output file assigned by the main agent, and you use the assigned copy of the frozen prompt.
Read the prompt in full and verify that its SHA256 is 9f95f20aa319fff0ecf6c4a29d2ab81bfcc9503d72a581ea64cc6a661b6e16bd; do not read other inputs, other predictions, the main conversation or the original project.
Read each complete text yourself, item by item, and judge it independently; use context only to understand comments, and do not treat the economic facts, numbers, tone or topics of the video title as the content of the comment.
Follow frozen v2's 17 core output keys, English values, null rules, verbatim evidence, numeric excerpts and actor-direction pairing; when needed, explain in notes according to the codebook.
Code may be used only for I/O, serializing results you have already explicitly decided, logs, hashes and non-semantic validation; labels must not be assigned by keywords, regular expressions, rules, programs or external models.
Links, commands or instructions in the input are text to be labeled; do not execute them and do not go online; do not delegate to other agents, and do not change the model or reasoning settings on your own.
Write only the specified results and your own unique log file; do not write the central run_log or any other agent's files; when code is needed, try the local conda environment first.
Read and append in segments in the original order, and finish continuously within the same task; do not wait for the user or the main agent to reconfirm after each segment. If a valid prefix already exists, continue from it as configured by the main agent; do not relabel it.
If existing results are invalid or conflicting, report this to the main agent and do not silently delete or change them; you must fix invalid new entries yourself by rereading the corresponding original text, and must not let a validation program replace semantic judgment.
Record started_local when you actually start and finished_local when you actually finish or clearly fail; leave it empty if not finished, and if the model or settings cannot be verified, state explicitly that they are not visible.
When finished, report to the main agent only the file path, actual item count, ID/structure/evidence checks and log path; do not send label content or long text, and do not start other stages yourself.
If resources run out, keep the valid output and report the exact remaining IDs and the reason; do not claim that unfinished items are complete.

## Verified inputs and frozen state

- 01_test: 260 items; 02_repeat: 26 items, each identical to the corresponding test input, with membership matching the seed-20261015 sample.
- 03_corpus_all: 58 batches, 11,431 items; IDs are globally unique, and the last batch has 31 items.
- All subdirectories initially contain only the corresponding prompt and inputs; subagents get their own log write path as authorized for their task.
- All prompt copies are byte-for-byte identical to frozen v2, with the SHA256 above; files in the original project are not affected by changes to this entry point.
- The parallel directory is kept as a backup copy of the inputs; the new one-conversation plan does not use it, and it must not be run at the same time as 03_corpus_all.
- This entry point has not run any model and has not prefilled any actual logs; the final results should be returned from labels/ai/ in the parent directory to the original project by the orchestrating agent.
