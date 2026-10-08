"""Sample golden-set candidates from the post-cutoff pool.

150 uniform-random openings  -> stratum='random' (estimates real-world metrics)
 50 risk-keyword oversample   -> stratum='risk'   (enough security/billing/angry cases to measure escalation)
Headline numbers are reported on 'random' and 'all' separately.
"""
import pandas as pd

from src.config import GOLDEN, PROCESSED, SEED

RISK = r"hack|stolen|someone (?:else )?(?:is )?us|refund|charged|charge me|cancel|scam|fraud|lawyer|sue\b|legal|worst|ridiculous|third time|3rd time|again and again|still no|no one"

pool = pd.read_parquet(PROCESSED / "test_pool.parquet")
rand = pool.sample(150, random_state=SEED).assign(stratum="random")
rest = pool.drop(rand.index)
risk = rest[rest.customer.str.contains(RISK, case=False, regex=True)].sample(50, random_state=SEED).assign(stratum="risk")
gold = pd.concat([rand, risk]).sample(frac=1, random_state=SEED).reset_index(drop=True)
gold.insert(0, "gid", [f"g{i:03d}" for i in range(len(gold))])
cols = ["gid", "stratum", "tweet_id", "created_at", "customer", "reply"]
GOLDEN.mkdir(parents=True, exist_ok=True)
gold[cols].to_csv(GOLDEN / "candidates.csv", index=False, encoding="utf-8")
print(gold.stratum.value_counts())
