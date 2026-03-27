# AIMO3 Status

## Current State

This repository contains the current local development state of the AIMO3 Kaggle pipeline.

The main progress so far is:

- extracted orchestration logic into small `src/` modules
- added attempt-level records, verifier-aware selection, retry/policy helpers, and regression helpers
- built a self-contained Kaggle evaluation notebook that no longer depends on local `src/` or `prompts/` folders
- ran a real reference-set evaluation on the 10 reference problems

## Current Evaluation Result

Reference evaluation summary:

- `num_questions = 10`
- `num_correct = 1`
- `accuracy = 0.1`
- `candidate_correct_exists = 1`
- `selection_failure = 0`
- `generation_failure = 9`
- `extraction_failure = 0`
- `retry_recoverable = 0`

Interpretation:

- the main bottleneck is not selection
- the main bottleneck is upstream attempt execution / candidate generation
- parser mostly falls back because strong final answers are rarely produced
- tool-assisted reasoning is not behaving reliably yet

## Most Important Files

- `src/`: modular local experimentation layer
- `notebooks/44-50-let-me-over-cook-postprocess-v1.ipynb`: working notebook copy used for staged integration
- `notebooks/aimo3-reference-eval-current-pipeline.ipynb`: self-contained Kaggle evaluation notebook
- `tests/`: local unit/regression tests

## Next Debug Focus

The next development step should be targeted debugging, not broader feature work.

Highest-priority debug targets:

- `_process_attempt(...)` exception visibility
- tool loop / python recipient handshake
- early answer scan during streaming
- raw output tracing to distinguish boxed answers vs last-integer fallback
