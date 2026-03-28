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
- built a self-contained Kaggle evaluation notebook:
  - `notebooks/aimo3-reference-eval-current-pipeline.ipynb`
- removed notebook dependence on local `src/` and `prompts/` folders for Kaggle evaluation packaging
- produced a first real reference-set evaluation baseline
- added a notebook-only repair/canonicalization pass for weak final answers
- hardened parser handling for malformed boxed answers and weak last-integer fallbacks
- added a clean-candidate-first selector guard so repaired `tier1`/`tier2` `ok` candidates are preferred over weak flagged candidates
- improved repair candidate selection so repair now samples stronger and more diverse weak attempts
- strengthened the repair prompt to force a single boxed integer instead of continuing draft reasoning
- added lightweight in-notebook exception visibility for `_process_attempt(...)` debugging

Current reference-set baseline:

- 10 questions
- 1 correct
- 9 generation failures
- 0 selection failures

This means the current main bottleneck is upstream solve execution / candidate generation rather than answer selection.

## Latest notebook results

Latest targeted notebook checks after the repair-pass work:

- 2-problem smoke test:
  - `92ba6a` -> correct
  - `0e644e` -> correct
- 5-problem mini-eval:
  - `0e644e` -> correct
  - `92ba6a` -> correct
  - `26de63` -> incorrect
  - `424e18` -> incorrect
  - `dd7f5e` -> incorrect
  - aggregate: `2 / 5 = 0.4`

Interpretation:

- The notebook is now materially better than the original 10-problem baseline.
- Repair/canonicalization can reliably rescue some problems where the raw attempts already contain the right reasoning but fail to emit a clean final answer.
- The current pipeline is still not stable enough for a confident submission.
- Remaining failures appear concentrated in hard problems where generation is weak and repair sometimes collapses to `0` or other small incorrect integers.
