"""Turn raw TWCS tweets into (customer opening message -> brand first reply) pairs for one brand."""
import re

import pandas as pd

from src.config import BRAND, PROCESSED, RAW_CSV

MENTION = re.compile(r"@\w+")
URL = re.compile(r"https?://\S+")
SIGNOFF = re.compile(r"\s*/\s?[A-Z]{1,3}\s*$")  # Spotify agents sign with initials, e.g. "/NJ"


def clean(text: str) -> str:
    text = text.replace("�", "'")  # dataset mojibake: curly apostrophes became U+FFFD
    text = MENTION.sub("", text)
    text = URL.sub("<URL>", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_reply(text: str) -> str:
    text = clean(text)
    text = re.sub(r"(\s*<URL>)+$", "", text)  # trailing DM-button links
    return SIGNOFF.sub("", text).strip()


def build_pairs() -> pd.DataFrame:
    df = pd.read_csv(RAW_CSV, dtype={"response_tweet_id": str})
    df["created_at"] = pd.to_datetime(df["created_at"], format="%a %b %d %H:%M:%S %z %Y")
    by_id = df.set_index("tweet_id")

    replies = df[(df.author_id == BRAND) & df.in_response_to_tweet_id.notna()]
    replies = replies[replies.in_response_to_tweet_id.astype(int).isin(by_id.index)]
    cust = by_id.loc[replies.in_response_to_tweet_id.astype(int)].reset_index()
    pairs = pd.DataFrame({
        "tweet_id": cust.tweet_id.values,
        "customer_id": cust.author_id.values,
        "created_at": cust.created_at.values,
        "is_opening": cust.in_response_to_tweet_id.isna().values,
        "customer_raw": cust.text.values,
        "reply_raw": replies.text.values,
        "reply_created_at": replies.created_at.values,
    })
    pairs = pairs[cust.inbound.values]
    # Several brand replies can answer one customer tweet; keep the first.
    pairs = pairs.sort_values("reply_created_at").drop_duplicates("tweet_id")
    pairs["customer"] = pairs.customer_raw.map(clean)
    pairs["reply"] = pairs.reply_raw.map(clean_reply)
    pairs = pairs[pairs.customer.str.len() >= 10]
    return pairs.sort_values("created_at").reset_index(drop=True)


if __name__ == "__main__":
    PROCESSED.mkdir(parents=True, exist_ok=True)
    p = build_pairs()
    print(len(p), "pairs;", p.is_opening.mean().round(3), "opening;", p.created_at.min(), "->", p.created_at.max())
    print(p.created_at.dt.to_period("M").value_counts().sort_index())
    p.to_parquet(PROCESSED / f"{BRAND}_pairs.parquet")
