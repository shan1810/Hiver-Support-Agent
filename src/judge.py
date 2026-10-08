"""LLM-as-judge for reply quality. All candidate replies for one customer tweet are judged in a single
call, blinded (R1..Rn) and shuffled with a per-item seed, so the judge cannot tell which system wrote what
(the brand's real historical reply is one of the candidates, as a human reference point)."""
import random

from pydantic import BaseModel, Field

from src.config import JUDGE_MODEL
from src.intents import ESCALATION_POLICY
from src.llm import CacheMiss, generate_json  # noqa: F401  (CacheMiss re-exported)

RUBRIC = """Score each candidate reply independently against this rubric (do not rank them against each other).

grounded (1-5): 5 = every factual claim is generic/safe or clearly true for Spotify; 3 = vague but not wrong;
  1 = invents facts, dates, links, policies, or promises (e.g. "we've refunded you", "it's fixed", "out Friday").
helpful (1-5): 5 = directly addresses THIS customer's issue and gives a concrete next step or answer;
  3 = generic but relevant (e.g. a reasonable clarifying question); 1 = ignores or misreads the issue.
tone (1-5): 5 = sounds like SpotifyCares: warm, casual, concise, tweet-length, no corporate filler; 1 = rude, robotic, or too long.
action_ok (true/false): is the reply's ACTION right under the escalation policy? Account-specific, security,
  non-English or high-risk cases need a hand-off to DM (no personal data requested publicly); everything else should be
  answered or clarified publicly. A DM request for a simple how-to question is NOT ok. Answering a charge dispute publicly is NOT ok.
send_ready (true/false): would a SpotifyCares team lead send this reply as-is? Requires grounded>=4, helpful>=3, tone>=3 and action_ok.
"""


class ReplyScore(BaseModel):
    rid: str
    grounded: int = Field(ge=1, le=5)
    helpful: int = Field(ge=1, le=5)
    tone: int = Field(ge=1, le=5)
    action_ok: bool
    send_ready: bool
    note: str = Field(description="<= 15 words: the main problem, or 'ok'.")


class Judgment(BaseModel):
    scores: list[ReplyScore]


def judge_item(gid: str, message: str, replies: dict[str, str]) -> dict[str, dict]:
    """replies: system -> reply text. Returns system -> score dict."""
    systems = sorted(replies)
    random.Random(gid).shuffle(systems)
    rid_to_sys = {f"R{i}": s for i, s in enumerate(systems, 1)}
    cands = "\n".join(f"{rid}: {replies[s]}" for rid, s in rid_to_sys.items())
    prompt = f"""You are auditing replies drafted for Spotify's Twitter support account @SpotifyCares.

ESCALATION POLICY:
{ESCALATION_POLICY}

RUBRIC:
{RUBRIC}

CUSTOMER TWEET:
{message}

CANDIDATE REPLIES:
{cands}

Return JSON with one score object per candidate, using its rid."""
    out = generate_json(prompt, Judgment, JUDGE_MODEL, namespace="judge")
    res = {}
    for s in out.scores:
        if s.rid in rid_to_sys:
            res[rid_to_sys[s.rid]] = s.model_dump(exclude={"rid"})
    return res

