# AIMO3 Local Development Project

This project supports a hybrid AIMO3 workflow:

- Local machine:
  - parser
  - modulus-aware parsing
  - boxed answer extraction
  - logging
  - evaluation harness
  - prompt templates
  - lightweight verify-fix
  - helper scripts

- Kaggle:
  - large model inference
  - vLLM serving
  - kernel pool / tool-integrated reasoning
  - real runtime behavior
  - submission flow

- Colab:
  - medium-scale prompt ablations
  - reflexion prototype tests
  - small-scale TIR experiments
  - alternative model experiments

## Data contracts

- reference.csv: id, problem, answer
- test.csv: id, problem
- sample_submission.csv: id, answer

## Project philosophy

- Use a proven notebook family as baseline.
- Add controlled upgrades incrementally.
- Prioritize logging, evaluation, and reproducibility.
- Avoid giant redesigns early.

## Current progress

Recent work completed in this repository:

- modularized orchestration helpers into `src/`
- added attempt-level tracing, verifier-aware selection, policy-driven retry helpers, and regression analysis
- built a self-contained Kaggle notebook flow for evaluation and submission packaging
- removed notebook dependence on local `src/` and `prompts/` folders for Kaggle evaluation packaging
- produced a first real reference-set evaluation baseline
- added a notebook-only repair/canonicalization pass for weak final answers
- hardened parser handling for malformed boxed answers and weak last-integer fallbacks
- added a clean-candidate-first selector guard so repaired `tier1`/`tier2` `ok` candidates are preferred over weak flagged candidates
- improved repair candidate selection so repair now samples stronger and more diverse weak attempts
- strengthened the repair prompt to force a single boxed integer instead of continuing draft reasoning
- added lightweight in-notebook exception visibility for `_process_attempt(...)` debugging
- fixed a hidden answer-scan crash path by making `_scan_for_answer(...)` tolerant when `postprocess_candidate` is absent
- fixed boxed-answer parsing for forms like `\\boxed{21\\,818}` and integer expressions embedded inside boxed text
- fixed submission packaging so the final notebook writes `submission.parquet` when Kaggle's local gateway input is absent during commit runs
- submitted the packaged notebook and reached a public score of `36 / 50`

Current main tracked notebook:

- `notebooks/aimo3-reference-eval-current-pipeline-submission3.ipynb`

## Latest notebook results

Latest tracked progression:

- early 10-problem notebook baseline:
  - `1 / 10`
- intermediate mini-eval after repair-pass work:
  - `2 / 5`
- late debug-stage reference runs:
  - targeted 5-problem run recovered to `5 / 5`
  - 10-problem reference eval reached `9 / 10`
  - the remaining miss was `86e8e5`, which looked like a generation failure rather than a selection/parsing failure
- final public Kaggle submission:
  - `36 / 50`

Interpretation:

- The repository now contains a real submission notebook, not just an evaluation/debug notebook.
- The biggest quality gains came from parser robustness, safer answer extraction, and stronger post-hoc repair behavior on weak final answers.
- Selection is no longer the dominant bottleneck on the tracked reference set.
- The remaining gap to stronger scores appears to be concentrated in hard-problem generation quality.
