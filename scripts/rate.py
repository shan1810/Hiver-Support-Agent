"""Human ratings for judge calibration. Run: python -m scripts.rate

Samples 60 (tweet, reply) pairs spread across systems, shown BLIND (you don't see which system wrote it),
and asks for the same rubric the LLM judge uses. Saved after each item to data/golden/human_ratings.csv.
"""
import pandas as pd

from src.config import GOLDEN, RESULTS, SEED
from src.judge import RUBRIC

OUT = GOLDEN / "human_ratings.csv"
N_PER_SYSTEM = 15


def ask(prompt, valid):
    while True:
        a = input(prompt).strip().lower()
        if a == "q" or a in valid:
            return a


def main():
    gold = pd.read_csv(GOLDEN / "golden.csv").set_index("gid")
    pred = pd.read_csv(RESULTS / "predictions.csv")
    hist = gold.reset_index()[["gid", "reply"]].assign(system="historical")
    pool = pd.concat([pred[pred.system.isin(["agent", "simple", "trivial"])][["gid", "system", "reply"]], hist])
    # trivial always sends the same reply; fewer of those are needed
    sample = pd.concat([g.sample(min(len(g), 6 if s == "trivial" else N_PER_SYSTEM), random_state=SEED)
                        for s, g in pool.groupby("system")]).sample(frac=1, random_state=SEED)
    done = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame(columns=["gid", "system"])
    done_keys = set(zip(done.gid, done.system))
    rows = done.to_dict("records")
    print(RUBRIC)
    todo = [r for r in sample.itertuples() if (r.gid, r.system) not in done_keys]
    print(f"{len(todo)} items left (q to quit, progress is saved)\n")
    for r in todo:
        print("-" * 100)
        print("CUSTOMER:", gold.loc[r.gid, "customer"])
        print("REPLY   :", r.reply)
        a = ask("  grounded 1-5 > ", set("12345"))
        if a == "q":
            break
        h = ask("  helpful 1-5 > ", set("12345"))
        if h == "q":
            break
        act = ask("  action_ok y/n > ", {"y", "n"})
        if act == "q":
            break
        sr = ask("  send_ready y/n > ", {"y", "n"})
        if sr == "q":
            break
        rows.append(dict(gid=r.gid, system=r.system, grounded=int(a), helpful=int(h),
                         action_ok=act == "y", send_ready=sr == "y"))
        pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"{len(rows)} ratings saved to {OUT}")


if __name__ == "__main__":
    main()
