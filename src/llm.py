"""Thin Gemini wrapper: JSON-schema output, on-disk cache, free-tier rate limiting, retries.

Every call is cached by (model, prompt, schema) hash under cache/. The cache is committed,
so the evaluation can be reproduced without an API key and without spending quota.
"""
import hashlib
import json
import os
import re
import time

from pydantic import BaseModel

from src.config import CACHE

_MIN_INTERVAL = 60.0 / float(os.getenv("GEMINI_RPM", "9"))  # stay under free-tier RPM
_last_call = 0.0
_client = None


class CacheMiss(RuntimeError):
    """Raised instead of calling the API when LLM_CACHE_ONLY=1."""


def _get_client():
    global _client
    if _client is None:
        from google import genai

        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("Cache miss and no GEMINI_API_KEY set. Put it in .env (see .env.example).")
        _client = genai.Client(api_key=key)
    return _client


def _key(model: str, prompt: str, schema: type[BaseModel]) -> str:
    blob = json.dumps([model, prompt, schema.model_json_schema()], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


def generate_json(prompt: str, schema: type[BaseModel], model: str, namespace: str) -> BaseModel:
    """Return a validated `schema` instance; served from cache when possible."""
    global _last_call
    path = CACHE / namespace / f"{_key(model, prompt, schema)}.json"
    if path.exists():
        return schema.model_validate_json(path.read_text(encoding="utf-8"))
    if os.getenv("LLM_CACHE_ONLY") == "1":
        raise CacheMiss(f"{namespace}/{path.name}")

    from google.genai import types

    client = _get_client()  # outside the retry loop: a missing key is not a transient error

    config = types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
        response_schema=schema,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    for attempt in range(8):
        wait = _MIN_INTERVAL - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=config)
            out = schema.model_validate_json(resp.text)
            break
        except Exception as e:  # 429s, 503s and occasional malformed JSON
            msg = str(e)
            if "PerDay" in msg or "per day" in msg.lower():
                raise RuntimeError(f"Daily quota exhausted for {model}; rerun tomorrow, cached calls are kept.") from e
            m = re.search(r"retry in ([\d.]+)s", msg)
            delay = float(m.group(1)) + 1 if m else min(60, 2 ** attempt * 2)
            print(f"  [llm] {type(e).__name__}: {msg[:120]} -> retry in {delay:.0f}s")
            time.sleep(delay)
    else:
        raise RuntimeError("LLM call failed after retries")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out.model_dump_json(indent=1), encoding="utf-8")
    return out
