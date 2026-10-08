"""Two baselines with no LLM.

trivial : predict the most common intent, escalate everything, send the brand's most common DM hand-off reply.
simple  : keyword rules for intent, rule-based escalation, reply = verbatim reply of the nearest past tweet (TF-IDF).
"""
import re
from functools import lru_cache

import pandas as pd

from src.agent import PII, SECURITY
from src.config import PROCESSED
from src.retrieval import get_retriever


@lru_cache(maxsize=1)
def most_common_reply() -> str:
    """The brand's most frequent hand-off reply (one that asks the customer to DM)."""
    replies = pd.read_parquet(PROCESSED / "kb.parquet").reply
    return replies[replies.str.contains(r"\bDM\b")].value_counts().index[0]


def trivial(message: str, majority_intent: str) -> dict:
    return dict(intent=majority_intent, escalate=True, escalation_code="E1",
                reason="Always escalate.", reply=most_common_reply())


# Ordered: first match wins. Security before access, money before plans.
RULES = [
    ("account_security", r"hack|compromis|someone (?:else )?(?:is )?us|stolen|not me|my account back"),
    ("billing_payment", r"charg|refund|bill|pay|paid|cancel|subscription|price|\$|£|€|offer|promo|deal|card"),
    ("plan_student_family", r"student|family|famil|invite|invitation|address|hulu"),
    ("account_access", r"log ?in|log ?out|logged|password|sign ?in|email|username|facebook|account"),
    ("content_availability", r"album|song|track|artist|available|release|podcast|remove|missing|reputation"),
    ("playback_technical", r"app|play|work|down|crash|error|bug|shuffle|download|offline|iphone|android|desktop|web|update|connect|lag|stuck|load"),
    ("feature_feedback", r"feature|please add|add a|would be|wish|should|idea|suggest|bring back|love|hate|playlist|ads?\b"),
]
ESCALATE_INTENTS = {"billing_payment", "account_security", "plan_student_family", "account_access"}


def rule_intent(message: str) -> str:
    for name, pat in RULES:
        if re.search(pat, message, re.I):
            return name
    return "other"


def simple(message: str) -> dict:
    intent = rule_intent(message)
    escalate = intent in ESCALATE_INTENTS or bool(PII.search(message)) or bool(SECURITY.search(message))
    nn = get_retriever().search(message, k=1, max_handoff=1).iloc[0]
    return dict(intent=intent, escalate=escalate, escalation_code="E1" if escalate else "none",
                reason=f"Rule: intent={intent}", reply=nn.reply)
