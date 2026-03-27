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

Current reference-set baseline:

- 10 questions
- 1 correct
- 9 generation failures
- 0 selection failures

This means the current main bottleneck is upstream solve execution / candidate generation rather than answer selection.
