# Golden evaluation set

`golden.csv`: 200 SpotifyCares thread-opening customer tweets, each labelled with an **intent** (8 classes) and an **escalation decision with a policy code** (A = auto-handle, E1–E4 = escalate; see `src/intents.py`).

## Sampling

- **Pool:** every thread-opening customer tweet SpotifyCares answered on or after **2017-11-25** (4,205 tweets, deduplicated by text). The retrieval knowledge base contains only tweets before that date, so the agent can never retrieve the answer it's graded against.
- **150 uniform-random** tweets (`stratum=random`). These estimate real-traffic performance.
- **50 risk-oversampled** tweets (`stratum=risk`), drawn from the rest of the pool with a keyword filter (hack, refund, charged, cancel, fraud, "third time", …). Without them the set would have too few security/fraud cases to measure the escalation behaviour that matters most. The oversample raises the escalation share from 34% (random) to 70% (risk), so every metric is reported on both "all" and "random only".
- Seed 13 (`scripts/02_sample_golden.py`).

## Labelling

1. The taxonomy and escalation policy were written first, from clusters over 12k pre-cutoff tweets, *not* from the golden tweets.
2. A first-pass draft label was produced for each row with an AI assistant (Claude, a different model family from the Gemini agent under test, to avoid the agent grading itself). During this pass the policy was refined once (E4 narrowed, E3 widened; see DECISIONS.md #6).
3. Every row is then reviewed by hand with `python -m scripts.label`: accept with Enter or type a correction. `label_source` records the outcome per row (`ai_draft` → `human_confirmed` / `human_changed`), and the share of changed labels is reported as a measure of how much the draft anchored the labels.
4. The historical brand reply is shown during labelling, but labels follow the **policy**, not what Spotify actually did. Spotify sent many how-to questions to DM; the policy says those should be answered publicly.

Known label ambiguities: student-discount *charges* vs plan problems (tie-break: money → billing), "my library disappeared" (technical vs possible account issue → technical unless there are signs of another user), and continuation tweets that look like openings ("Still nothing") → `other`.

## Human ratings for judge calibration

`human_ratings.csv` (created by `python -m scripts.rate`): about 51 blind (tweet, reply) pairs across agent / simple / trivial / historical, rated on the judge's own rubric (grounded, helpful, action_ok, send_ready). Used in `05_metrics.py` to compute judge–human agreement (Cohen's κ, Spearman).
