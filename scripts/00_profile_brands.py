"""Profile brands in TWCS to pick one. Prints volume, reply length, and how often
the brand just deflects to DM (a proxy for 'how much resolution happens in public')."""
import re
import pandas as pd
from src.config import RAW_CSV

df = pd.read_csv(RAW_CSV, usecols=["tweet_id", "author_id", "inbound", "text", "in_response_to_tweet_id"])
brand = df[~df.inbound]
DM = re.compile(r"\b(dm|direct message|private message|send us a message|reach out via|pm)\b", re.I)
g = brand.groupby("author_id").agg(
    n_replies=("tweet_id", "size"),
    mean_len=("text", lambda s: s.str.len().mean()),
    dm_rate=("text", lambda s: s.str.contains(DM).mean()),
    has_url=("text", lambda s: s.str.contains("http").mean()),
)
print(g.sort_values("n_replies", ascending=False).head(25).round(3).to_string())
