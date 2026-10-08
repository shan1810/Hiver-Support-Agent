"""Compare the main judge with a stronger judge (gemini-2.5-flash) on the items it had quota for.

Cache-only: never calls the API. Items with no cached stronger-judge result are skipped.
"""
import os

import pandas as pd

os.environ["JUDGE_MODEL"] = "gemini-2.5-flash"
os.environ["LLM_CACHE_ONLY"] = "1"  # never spend quota here
import src.judge as judge  # noqa: E402  (must import after setting the env vars)
from src.config import GOLDEN, RESULTS  # noqa: E402

gold = pd.read_csv(GOLDEN / "golden.csv").set_index("gid")
pred = pd.read_csv(RESULTS / "predictions.csv")
main = pd.read_csv(RESULTS / "judgments.csv").set_index(["gid", "system"])
rows = []
for gid, grp in pred[pred.system.isin(["agent", "simple", "trivial", "agent_noretrieval"])].groupby("gid"):
    replies = dict(zip(grp.system, grp.reply)) | {"historical": gold.loc[gid, "reply"]}
    try:
        strong = judge.judge_item(gid, gold.loc[gid, "customer"], replies)
    except judge.CacheMiss:
        continue
    for s, v in strong.items():
        m = main.loc[(gid, s)]
        rows.append(dict(gid=gid, system=s, strong_send_ready=v["send_ready"], main_send_ready=m.send_ready,
                         strong_helpful=v["helpful"], main_helpful=m.helpful))
d = pd.DataFrame(rows)
print(f"{d.gid.nunique()} items, {len(d)} replies judged by both")
print("send_ready agreement:", round((d.strong_send_ready == d.main_send_ready).mean(), 3))
print(d.groupby("system")[["strong_send_ready", "main_send_ready", "strong_helpful", "main_helpful"]].mean().round(2).to_string())
