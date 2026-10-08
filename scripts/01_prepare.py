"""Build pairs for the brand and split by time.

kb.parquet         : every (customer -> first brand reply) pair BEFORE the cutoff. Retrieval corpus.
test_pool.parquet  : thread-opening customer tweets ON/AFTER the cutoff. Golden set is sampled from here.
A time split means the agent can never retrieve the very reply it is being graded against.
"""
import pandas as pd

from src.config import BRAND, PROCESSED
from src.data import build_pairs

CUTOFF = pd.Timestamp("2017-11-25")

pairs = build_pairs()
kb = pairs[pairs.created_at < CUTOFF].reset_index(drop=True)
pool = pairs[(pairs.created_at >= CUTOFF) & pairs.is_opening]
pool = pool.drop_duplicates("customer").reset_index(drop=True)
PROCESSED.mkdir(parents=True, exist_ok=True)
kb.to_parquet(PROCESSED / "kb.parquet")
pool.to_parquet(PROCESSED / "test_pool.parquet")
print(f"{BRAND}: {len(pairs)} pairs | kb={len(kb)} (< {CUTOFF.date()}) | test_pool={len(pool)} openings")
