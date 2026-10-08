# SpotifyCares support agent: Hiver Assignment

An AI first-line agent for **@SpotifyCares**, built from the [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) dataset. For each incoming tweet it:

1. **classifies** it into one of 8 intents derived from the data (`src/intents.py`),
2. **drafts a reply** grounded in how SpotifyCares answered the most similar past tweets (TF-IDF retrieval over 34k historical pairs + Gemini),
3. **decides auto-handle vs escalate** with a policy code (E1 account action, E2 security/PII, E3 high-risk tone, E4 non-English) and a one-line reason. Deterministic guardrails can force an escalation but never remove one.

📄 **Report:** [`report/REPORT.md`](report/REPORT.md) · **Decision log:** [`DECISIONS.md`](DECISIONS.md) · **Metrics:** [`results/metrics.md`](results/metrics.md)

## Reproduce the headline numbers (≈2 minutes, no API key needed)

Every LLM call is cached in `cache/` (keyed by model + prompt hash), and the processed data is committed. Re-running the pipeline therefore makes zero API calls. Set `LLM_CACHE_ONLY=1` to guarantee it:

```bash
pip install -r requirements.txt
python -m scripts.03_run_systems --ablate   # agent + baselines + ablations  -> results/predictions.csv
python -m scripts.04_judge                  # LLM-as-judge (cached)          -> results/judgments.csv
python -m scripts.05_metrics                # all metrics, CIs, agreement    -> results/metrics.md
python -m scripts.06_judge_crosscheck       # main judge vs stronger judge (cache-only)
```

Try the agent on any tweet. A new tweet is a cache miss, so this needs `GEMINI_API_KEY` in `.env`:

```bash
python -c "from src.agent import run_agent; print(run_agent('I got charged twice this month, help'))"
```

## Rebuild from raw data (≈5 min + LLM time)

```bash
cp .env.example .env              # add GEMINI_API_KEY (free tier is enough)
python -c "import kagglehub; print(kagglehub.dataset_download('thoughtvector/customer-support-on-twitter'))"
# copy twcs/twcs.csv to data/raw/twcs.csv (or set TWCS_CSV=path)
python -m scripts.00_profile_brands   # brand selection evidence
python -m scripts.01_prepare          # pairs + time split -> data/processed/{kb,test_pool}.parquet
python -m scripts.02_sample_golden    # golden candidates (150 random + 50 risk)
python -m scripts.label               # review / correct golden labels interactively
python -m scripts.03_run_systems --ablate
python -m scripts.04_judge
python -m scripts.rate                # blind human ratings for judge calibration
python -m scripts.05_metrics
```

On the free tier, uncached runs take ~25 min for the agent (400 calls incl. ablation) and ~45 min for the judge (200 calls). `GEMINI_RPM` controls throttling.

## Layout

```
src/
  config.py      paths, brand, model names
  data.py        raw tweets -> (opening customer tweet, first brand reply) pairs, cleaning
  intents.py     intent taxonomy, tie-break rules, escalation policy (shared by labels, agent, judge)
  retrieval.py   TF-IDF retriever over the pre-cutoff knowledge base
  agent.py       prompt, single structured LLM call, guardrails
  baselines.py   trivial + simple (rules + nearest-neighbour reply) baselines
  judge.py       blinded multi-candidate LLM judge + rubric
  llm.py         Gemini wrapper: JSON schema output, disk cache, rate limiting, retries
scripts/         numbered pipeline steps + label.py / rate.py (human-in-the-loop tools)
data/golden/     golden.csv (200 labelled tweets), human_ratings.csv, labelling notes
results/         predictions, judgments, metrics.md, failures.csv
cache/           committed LLM responses
```

## Golden set: how it was sampled and labelled

See [`data/golden/README.md`](data/golden/README.md).

## Borrowed / cited

- Dataset: Thought Vector, *Customer Support on Twitter* (Kaggle, CC BY-NC-SA 4.0).
- Libraries: scikit-learn (TF-IDF, KMeans, metrics), pandas, pydantic, google-genai.
- Rubric style (multi-dimension 1–5 + binary verdict, blinded candidates) follows common LLM-as-judge practice (e.g. Zheng et al., 2023, *Judging LLM-as-a-Judge with MT-Bench*). No code was copied.
- Built with an AI coding assistant (Claude Code). All design decisions are in `DECISIONS.md`, and I can explain and modify any part of the code.
