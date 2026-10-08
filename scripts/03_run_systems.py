"""Run every system over the golden set -> results/predictions.csv (one row per gid x system).

Systems: trivial, simple, agent (retrieval + LLM + guardrails), and two free ablations:
agent_noguard (same LLM output, guardrails off) and, with --ablate, agent_noretrieval (extra LLM calls).
"""
import argparse

import pandas as pd

from src.agent import run_agent
from src.baselines import simple, trivial
from src.config import GOLDEN, RESULTS

ap = argparse.ArgumentParser()
ap.add_argument("--ablate", action="store_true", help="also run the no-retrieval agent (200 more LLM calls)")
ap.add_argument("--limit", type=int, default=None)
args = ap.parse_args()

gold = pd.read_csv(GOLDEN / "golden.csv")
if args.limit:
    gold = gold.head(args.limit)
majority = gold.intent.mode()[0]
rows = []
for n, r in enumerate(gold.itertuples(), 1):
    outs = {
        "trivial": trivial(r.customer, majority),
        "simple": simple(r.customer),
        "agent": run_agent(r.customer),
        "agent_noguard": run_agent(r.customer, use_guardrails=False),
    }
    if args.ablate:
        outs["agent_noretrieval"] = run_agent(r.customer, use_retrieval=False)
    for system, o in outs.items():
        rows.append({"gid": r.gid, "system": system, **{k: o.get(k) for k in
                     ["intent", "escalate", "escalation_code", "reason", "reply", "confidence", "guardrail"]}})
    if n % 20 == 0:
        print(f"{n}/{len(gold)}")

RESULTS.mkdir(exist_ok=True)
pd.DataFrame(rows).to_csv(RESULTS / "predictions.csv", index=False, encoding="utf-8")
print("wrote results/predictions.csv")
