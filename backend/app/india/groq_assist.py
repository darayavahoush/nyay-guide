"""Optional, OFF-by-default fallback: ask a small hosted model (Groq) to propose TENTATIVE facts when the lexicon and the
local encoder found nothing in a long enough message.

Safety rules, same as slm.py: it can only suggest (the person is still asked), every value is validated against the
engine's own vocabulary, and anything else it says is discarded. The key is read from the environment and is never
stored, logged or returned.

Privacy: turning this on sends the person's text to a third party. Leave it off for real cases unless users are told.

Env: GROQ_API_KEY (required), GROQ_ENABLE=1 (required), GROQ_MODEL (default llama-3.1-8b-instant),
     GROQ_DAILY_CAP (default 200 calls per process per day), GROQ_TIMEOUT (seconds, default 6).
"""
from __future__ import annotations
import json, os, time, urllib.request, urllib.error

URL = "https://api.groq.com/openai/v1/chat/completions"
ALLOWED = {
    "law": ["hindu", "muslim", "christian", "parsi", "special_marriage"],
    "claimant": ["wife", "husband", "child", "parent"],
    "ground": ["cruelty", "desertion", "adultery"],
    "divorce_status": ["none", "pending", "decreed"],
    "mutual_consent": [True, False], "domestic_violence": [True], "respondent_abroad": [True],
    "claimant_can_self_maintain": [True, False], "respondent_has_means": [True, False],
}
NEEDS = ["divorce", "maintenance", "protection"]
SYSTEM = ("You extract facts from a person's description of an Indian family-law problem. Reply with ONE JSON object and nothing else. "
          "Only include a key if the text clearly supports it; omit anything uncertain. Allowed keys and values: "
          + json.dumps({**ALLOWED, "needs": NEEDS}) + ". Never invent places, dates or names. Do not give legal advice.")
_calls = {"day": None, "n": 0}


def enabled() -> bool:
    return os.environ.get("GROQ_ENABLE") == "1" and bool(os.environ.get("GROQ_API_KEY"))


def _budget() -> bool:
    today = time.strftime("%Y-%m-%d")
    if _calls["day"] != today: _calls.update(day=today, n=0)
    if _calls["n"] >= int(os.environ.get("GROQ_DAILY_CAP", "200")): return False
    _calls["n"] += 1; return True


def clean(obj) -> dict:
    """Keep only values the engine understands. Returns {slot: value}."""
    out = {}
    if not isinstance(obj, dict): return out
    for k, allowed in ALLOWED.items():
        if k in obj and any(obj[k] == a and type(obj[k]) is type(a) for a in allowed): out[k] = obj[k]
    n = obj.get("needs")
    if isinstance(n, list) and n and all(x in NEEDS for x in n): out["needs"] = sorted(set(n))
    return out


def suggest(text: str) -> dict:
    """{slot: {"value", "why", "source"}}; {} on any failure. Never raises."""
    if not enabled() or len(text.split()) < 6 or not _budget(): return {}
    model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": 200, "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text[:1500]}]}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["GROQ_API_KEY"]})
    try:
        with urllib.request.urlopen(req, timeout=float(os.environ.get("GROQ_TIMEOUT", "6"))) as r:
            content = json.loads(r.read())["choices"][0]["message"]["content"]
        vals = clean(json.loads(content))
    except Exception:       # network, quota, bad JSON: the lexicon answer stands
        return {}
    return {k: {"value": v, "why": "proposed by a hosted small model; please confirm", "source": f"groq:{model}"} for k, v in vals.items()}
