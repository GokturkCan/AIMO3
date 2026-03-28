# AIMO3 Status

## Current State

This repository contains the current local development state of the AIMO3 Kaggle pipeline.

The main progress so far is:

- extracted orchestration logic into small `src/` modules
- added attempt-level records, verifier-aware selection, retry/policy helpers, and regression helpers
- built a self-contained Kaggle evaluation notebook that no longer depends on local `src/` or `prompts/` folders
- ran a real reference-set evaluation on the 10 reference problems
- added notebook-local parser and selector hardening for malformed boxed answers
- added a final-answer repair / canonicalization pass inside the Kaggle notebook flow
- added clean-candidate-first selection behavior for repaired `ok` candidates
- added temporary exception visibility in `_process_attempt(...)` to surface hidden runtime failures during notebook debugging

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

## Latest Notebook Debug Outcome

### What changed in the notebook

The current notebook state now includes these incremental changes inside `Cell 13`:

- weaker confidence for `last_integer` fallback after malformed boxed answers
- parse-tier downgrade for malformed boxed-answer cases
- extra suspicion penalty for malformed boxed / fallback-after-invalid-boxed candidates
- repair / canonicalization pass applied after normal attempts and retries
- stricter repair prompt that asks for exactly one boxed integer and explicitly says not to continue the draft
- improved repair-source selection across `self_refute`, `tool_guided`, and `baseline` attempt families
- clean-candidate-first guard in `select_best_attempt(...)`

### Targeted smoke-test result

The latest targeted smoke tests show real progress:

- `92ba6a`
  - raw attempts still often land in `tier3` / `flagged`
  - repair now produces multiple `50` candidates with `tier2` / `ok`
  - final selected answer is correct
- `0e644e`
  - raw attempts are also weak
  - repair produces multiple `336` candidates with `tier2` / `ok`
  - final selected answer is correct

Interpretation:

- the repair pass is not just cosmetic; it can convert weak-but-promising drafts into clean competitive candidates
- the clean-candidate-first guard is doing useful work once repair succeeds
- for at least two qualitatively different problems, the notebook now recovers the correct final answer from weak raw attempts

### 5-problem mini-eval result

Recent controlled mini-eval:

- `0e644e` -> correct (`336`)
- `26de63` -> incorrect (`0`, expected `32951`)
- `424e18` -> incorrect (`0`, expected `21818`)
- `92ba6a` -> correct (`50`)
- `dd7f5e` -> incorrect (`0`, expected `160`)

Aggregate:

- `num_questions = 5`
- `num_correct = 2`
- `accuracy = 0.4`

Interpretation:

- this is a meaningful improvement over the original 10-question baseline
- however, the notebook is still not submission-stable
- current failures are no longer explained only by selection
- remaining failure modes now look mixed:
  - some hard problems still fail during upstream generation
  - some repair outputs collapse to `0` or other small incorrect integers

## Current Assessment

Current repo state is best described as:

- a substantially improved notebook debug branch
- promising enough to preserve and build on
- not yet strong enough for a final submission run

## Next Likely Focus

If work resumes later, the highest-value next steps are:

- inspect why repair sometimes converges to `0`
- reduce over-trusting repaired small-number answers
- improve hard-problem generation quality before repair
- rerun a controlled medium-size eval before any submission attempt

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
