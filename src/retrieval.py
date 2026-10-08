"""Lexical retrieval over the brand's historical (customer -> reply) pairs.

TF-IDF over word 1-2grams: zero API calls, ~2s to build on 34k pairs, and good enough for
short tweets where the issue is usually named in plain words ("charged twice", "student").
"""
from functools import lru_cache

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from src.config import PROCESSED

# Replies that only move the chat to DM carry no resolution knowledge; they are kept in the
# index (they show *when* the brand escalates) but capped so they don't crowd out real answers.
PURE_HANDOFF = r"(?:replied to|sent (?:you )?a dm|sent a dm|over dm|carry on (?:chatting|helping))"


class Retriever:
    def __init__(self, kb: pd.DataFrame):
        self.kb = kb.reset_index(drop=True)
        self.vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english")
        self.X = self.vec.fit_transform(self.kb.customer)
        self.handoff = self.kb.reply.str.contains(PURE_HANDOFF, case=False, regex=True).values

    def search(self, text: str, k: int = 6, max_handoff: int = 1) -> pd.DataFrame:
        sims = linear_kernel(self.vec.transform([text]), self.X).ravel()
        out, seen, n_handoff = [], set(), 0
        for i in sims.argsort()[::-1]:
            reply = self.kb.reply[i]
            if reply in seen:
                continue
            if self.handoff[i]:
                if n_handoff >= max_handoff:
                    continue
                n_handoff += 1
            seen.add(reply)
            out.append(i)
            if len(out) == k:
                break
        res = self.kb.loc[out, ["tweet_id", "customer", "reply"]].copy()
        res["score"] = sims[out]
        return res


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    return Retriever(pd.read_parquet(PROCESSED / "kb.parquet"))
