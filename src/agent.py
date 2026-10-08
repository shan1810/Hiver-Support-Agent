"""The support agent: retrieve similar past cases -> one LLM call (intent + escalation + draft) -> guardrails."""
import re
from typing import Literal

from pydantic import BaseModel, Field

from src.config import AGENT_MODEL
from src.intents import ESCALATION_POLICY, INTENT_NAMES, INTENTS, TIE_BREAKS
from src.llm import generate_json
from src.retrieval import get_retriever

IntentT = Literal[tuple(INTENT_NAMES)]  # type: ignore[valid-type]


class AgentOutput(BaseModel):
    intent: IntentT
    confidence: Literal["low", "medium", "high"]
    escalate: bool
    escalation_code: Literal["none", "E1", "E2", "E3", "E4"]
    reason: str = Field(description="One sentence: why auto-handle or why escalate.")
    reply: str = Field(description="The public tweet reply, <= 260 characters.")


STYLE = """SpotifyCares voice (learned from their replies): open with "Hey <name>!"/"Hey there!"/"Hi there!",
friendly and casual, short (1-2 sentences, under 260 characters), music puns are fine ("backstage", "help's here").
Never invent facts: no release dates, no promises of refunds/credits, no claims an outage is fixed unless the
customer says so, no made-up links. If a link is needed write a placeholder like [link: Spotify Community ideas board].
If escalating, the reply is the public hand-off: ask them to DM (never ask for personal data in public) and,
if they posted personal data publicly, suggest deleting that tweet."""


def build_prompt(message: str, examples=None) -> str:
    intents = "\n".join(f"- {k}: {v}" for k, v in INTENTS.items())
    if examples is None:
        ex_block = "(no examples)"
    else:
        ex_block = "\n".join(
            f"[{i}] CUSTOMER: {r.customer}\n    SPOTIFYCARES: {r.reply}" for i, r in enumerate(examples.itertuples(), 1)
        )
    return f"""You are the first-line Twitter support agent for Spotify (@SpotifyCares).

INTENTS:
{intents}
Tie-breaks:
{TIE_BREAKS}

ESCALATION POLICY:
{ESCALATION_POLICY}

STYLE:
{STYLE}

How SpotifyCares answered the most similar past tweets (use these for facts and tone; they may be imperfect
or outdated, and many simply moved the customer to DM):
{ex_block}

NEW CUSTOMER TWEET:
{message}

Classify, decide escalation per the policy, and draft the reply. Return JSON."""


# Deterministic guardrails. They can only *add* escalations, never remove one.
PII = re.compile(r"__(?:email|credit_card|phone)\w*__|\b[\w.+-]+@[\w-]+\.\w+\b|\b(?:\d[ -]?){12,19}\b")
SECURITY = re.compile(r"hack|compromis|stolen account|someone (?:else )?(?:is )?(?:using|logged|in) my|not me|unauthori[sz]ed", re.I)
EN_WORDS = re.compile(r"\b(?:the|is|my|i|to|and|it|you|a|in|for|on|of|me|not|can|why|what|how|this|that|with|but)\b", re.I)


def guardrails(message: str) -> tuple[str, str] | None:
    if PII.search(message):
        return "E2", "Guardrail: customer posted personal data publicly."
    if SECURITY.search(message):
        return "E2", "Guardrail: possible account compromise."
    text = re.sub(r"#\w+|<URL>", " ", message)
    words = re.findall(r"[A-Za-z]+", text)
    if len(words) >= 6 and len(EN_WORDS.findall(text)) / len(words) < 0.08:
        return "E4", "Guardrail: message does not look like English."
    return None


def run_agent(message: str, use_retrieval: bool = True, use_guardrails: bool = True, k: int = 6) -> dict:
    examples = get_retriever().search(message, k=k) if use_retrieval else None
    ns = "agent" if use_retrieval else "agent_noretrieval"
    out = generate_json(build_prompt(message, examples), AgentOutput, AGENT_MODEL, namespace=ns)
    res = out.model_dump()
    res["guardrail"] = ""
    if use_guardrails and not res["escalate"]:
        hit = guardrails(message)
        if hit:
            res.update(escalate=True, escalation_code=hit[0], guardrail=hit[1])
            res["reason"] = hit[1] + " (LLM said: " + res["reason"] + ")"
            # The LLM wrote an auto-reply; swap in a safe hand-off.
            res["reply"] = "Hey there, help's here! For your account's security, could you send us a DM instead? We'll take a look backstage."
    res["retrieved_ids"] = [] if examples is None else examples.tweet_id.tolist()
    return res
