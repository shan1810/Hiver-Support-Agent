"""Judge reply quality for every system + the brand's real historical reply -> results/judgments.csv."""
import pandas as pd

from src.config import GOLDEN, RESULTS
from src.judge import judge_item

JUDGED = ["agent", "simple", "trivial", "agent_noretrieval"]  # agent_noguard differs only on guardrail rows

gold = pd.read_csv(GOLDEN / "golden.csv").set_index("gid")
pred = pd.read_csv(RESULTS / "predictions.csv")
pred = pred[pred.system.isin(JUDGED)]
rows = []
for n, (gid, grp) in enumerate(pred.groupby("gid"), 1):
    replies = dict(zip(grp.system, grp.reply))
    replies["historical"] = gold.loc[gid, "reply"]
    for system, s in judge_item(gid, gold.loc[gid, "customer"], replies).items():
        rows.append({"gid": gid, "system": system, **s})
    if n % 20 == 0:
        print(f"{n}/{pred.gid.nunique()}")
pd.DataFrame(rows).to_csv(RESULTS / "judgments.csv", index=False, encoding="utf-8")
print("wrote results/judgments.csv")
