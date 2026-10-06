"""India family-law agent: multilingual slot-filling dialogue with information-gain question selection.
No LLM. Tools: intake (lexicon + optional small encoder, see slm.py), engine (rules), planner (checklists).
Policy: ask the unknown fact whose possible answers split the engine's outcome into the most distinct
cases (max Shannon entropy over outcomes, uniform prior over answers); stop when no unknown fact can
change the outcome. Pure stdlib."""
from __future__ import annotations
import math, time, uuid
from collections import Counter, OrderedDict
from dataclasses import fields
from .engine import Facts, advise, LAWS
from .intake import extract
from . import slm

DOMAIN = {  # slot -> candidate answers used to measure information gain (order = tie-break priority)
    "mutual_consent": [False, True], "ground": ["cruelty", "desertion", None], "separated_months": [0, 18, 30], "marriage_years": [0.5, 3],
    "domestic_violence": [False, True], "divorce_status": ["none", "pending", "decreed"],
    "respondent_has_means": [True, False], "claimant_can_self_maintain": [False, True],
    "claimant_living_in_adultery": [False, True], "claimant_refuses_cohabitation_without_cause": [False, True],
    "separated_by_mutual_consent": [False, True], "child_minor": [True, False], "child_disabled": [False, True],
    "respondent_abroad": [False, True],
}
OPTS = {"law": list(LAWS), "claimant": ["wife", "husband", "child", "parent"], "needs": ["divorce", "maintenance", "protection"],
        "ground": ["cruelty", "desertion", "adultery", "other", "none"], "separated_months": [6, 18, 30], "marriage_years": [0.5, 3],
        "divorce_status": ["none", "pending", "decreed"]}
PRIOR = {  # P(answer) in DOMAIN order; rare disqualifiers get low prior so they are not asked by default
    "claimant_living_in_adultery": [0.95, 0.05], "claimant_refuses_cohabitation_without_cause": [0.95, 0.05],
    "separated_by_mutual_consent": [0.93, 0.07], "respondent_abroad": [0.92, 0.08], "child_disabled": [0.9, 0.1],
    "domestic_violence": [0.7, 0.3], "divorce_status": [0.6, 0.25, 0.15], "respondent_has_means": [0.8, 0.2], "claimant_can_self_maintain": [0.7, 0.3], "mutual_consent": [0.7, 0.3],
}
THRESH = 0.45  # bits; below this a question is listed as "not checked" instead of asked
YN = {"en": ("Yes", "No"), "hi": ("हाँ", "नहीं"), "ta": ("ஆம்", "இல்லை")}
LBL = {
 "law": {"en": ["Hindu / Sikh / Jain / Buddhist", "Muslim", "Christian", "Parsi", "Special Marriage Act"],
         "hi": ["हिंदू / सिख / जैन / बौद्ध", "मुस्लिम", "ईसाई", "पारसी", "विशेष विवाह अधिनियम"],
         "ta": ["இந்து / சீக்கியர் / சமணர் / பௌத்தர்", "முஸ்லிம்", "கிறிஸ்தவர்", "பார்சி", "சிறப்புத் திருமணச் சட்டம்"]},
 "claimant": {"en": ["Wife", "Husband", "Child", "Parent"], "hi": ["पत्नी", "पति", "बच्चा", "माता-पिता"], "ta": ["மனைவி", "கணவர்", "குழந்தை", "பெற்றோர்"]},
 "needs": {"en": ["Divorce", "Maintenance", "Protection from violence"], "hi": ["तलाक", "गुजारा भत्ता", "हिंसा से सुरक्षा"], "ta": ["விவாகரத்து", "பராமரிப்பு", "வன்முறையிலிருந்து பாதுகாப்பு"]},
 "ground": {"en": ["Cruelty", "Desertion", "Adultery", "Other reason", "No specific reason"], "hi": ["क्रूरता", "परित्याग", "व्यभिचार", "अन्य कारण", "कोई विशेष कारण नहीं"],
            "ta": ["கொடுமை", "கைவிடுதல்", "கள்ள உறவு", "வேறு காரணம்", "குறிப்பிட்ட காரணம் இல்லை"]},
 "separated_months": {"en": ["Under 1 year", "1 to 2 years", "Over 2 years"], "hi": ["1 साल से कम", "1 से 2 साल", "2 साल से अधिक"], "ta": ["1 ஆண்டுக்குள்", "1–2 ஆண்டுகள்", "2 ஆண்டுகளுக்கு மேல்"]},
 "divorce_status": {"en": ["No case filed yet", "A case is pending", "A divorce decree has been passed"],
                    "hi": ["अभी कोई मामला दायर नहीं हुआ", "मामला चल रहा है", "तलाक का फैसला हो चुका है"],
                    "ta": ["இன்னும் வழக்கு தாக்கல் செய்யப்படவில்லை", "வழக்கு நடைபெறுகிறது", "விவாகரத்து தீர்ப்பு வழங்கப்பட்டுவிட்டது"]},
 "marriage_years": {"en": ["Under 1 year ago", "1 year or more ago"], "hi": ["1 साल से कम पहले", "1 साल या अधिक पहले"], "ta": ["1 ஆண்டுக்குள்", "1 ஆண்டு அல்லது அதற்கு மேல்"]},
}
Q = {  # yes = True for every boolean slot
 "law": ("Which personal law applies to the marriage?", "विवाह पर कौन सा व्यक्तिगत कानून लागू होता है?", "திருமணத்துக்கு எந்தத் தனிநபர் சட்டம் பொருந்தும்?"),
 "claimant": ("Who is making the claim?", "दावा कौन कर रहा है?", "யார் கோருகிறார்?"),
 "needs": ("What do you need? Pick all that apply.", "आपको क्या चाहिए? जो लागू हों सब चुनें।", "உங்களுக்கு என்ன வேண்டும்? பொருந்துவதை எல்லாம் தேர்வு செய்யுங்கள்."),
 "mutual_consent": ("Do both of you agree to the divorce?", "क्या आप दोनों तलाक के लिए सहमत हैं?", "இருவரும் விவாகரத்துக்குச் சம்மதிக்கிறீர்களா?"),
 "ground": ("What is the main reason for the divorce?", "तलाक का मुख्य कारण क्या है?", "விவாகரத்துக்கான முக்கிய காரணம் என்ன?"),
 "separated_months": ("How long have you been living apart?", "आप कितने समय से अलग रह रहे हैं?", "எவ்வளவு காலமாகப் பிரிந்து வாழ்கிறீர்கள்?"),
 "marriage_years": ("When did you marry?", "आपका विवाह कब हुआ?", "திருமணம் எப்போது நடந்தது?"),
 "domestic_violence": ("Has there been violence or abuse at home?", "क्या घर में हिंसा या दुर्व्यवहार हुआ है?", "வீட்டில் வன்முறை அல்லது துன்புறுத்தல் நடந்ததா?"),
 "divorce_status": ("Where does a divorce case stand?", "तलाक के मामले की क्या स्थिति है?", "விவாகரத்து வழக்கு எந்த நிலையில் உள்ளது?"),
 "respondent_has_means": ("Does the other person earn or own enough to pay?", "क्या दूसरे व्यक्ति के पास देने लायक आय या संपत्ति है?", "மற்றவருக்குக் கொடுக்கும் அளவு வருமானம் அல்லது சொத்து உள்ளதா?"),
 "claimant_can_self_maintain": ("Can the claimant meet their own living costs?", "क्या दावेदार अपना खर्च खुद उठा सकता है?", "கோருபவர் தன் செலவுகளைத் தானே சமாளிக்க முடியுமா?"),
 "claimant_living_in_adultery": ("Is the claimant living with another partner?", "क्या दावेदार किसी और साथी के साथ रह रहा है?", "கோருபவர் வேறொரு துணையுடன் வாழ்கிறாரா?"),
 "claimant_refuses_cohabitation_without_cause": ("Did the claimant refuse to live with the spouse without a valid reason?", "क्या दावेदार ने बिना उचित कारण जीवनसाथी के साथ रहने से मना किया?", "கோருபவர் தகுந்த காரணமின்றி துணையுடன் வாழ மறுத்தாரா?"),
 "separated_by_mutual_consent": ("Are you living apart by mutual agreement?", "क्या आप आपसी सहमति से अलग रह रहे हैं?", "பரஸ்பர ஒப்புதலுடன் பிரிந்து வாழ்கிறீர்களா?"),
 "child_minor": ("Is the child under 18?", "क्या बच्चे की उम्र 18 साल से कम है?", "குழந்தைக்கு 18 வயதுக்குள் ஆகிறதா?"),
 "child_disabled": ("Does the adult child have a physical or mental disability?", "क्या वयस्क बच्चे को शारीरिक या मानसिक विकलांगता है?", "வயது வந்த குழந்தைக்கு உடல் அல்லது மனநல குறைபாடு உள்ளதா?"),
 "respondent_abroad": ("Does the other person live outside India?", "क्या दूसरा व्यक्ति भारत से बाहर रहता है?", "மற்றவர் இந்தியாவுக்கு வெளியே வசிக்கிறாரா?"),
}
FRAME = {
 "advice": ("I found {n} possible route(s). Start with: {first}.", "मुझे {n} संभावित रास्ते मिले। शुरुआत करें: {first}।", "{n} சாத்தியமான வழிகள் உள்ளன. முதலில்: {first}."),
 "none": ("No matching route found yet. Tell me more about what you need.", "अभी कोई मेल खाता रास्ता नहीं मिला। बताइए आपको क्या चाहिए।", "பொருந்தும் வழி இன்னும் இல்லை. உங்களுக்கு என்ன வேண்டும் என்று சொல்லுங்கள்."),
}
YES_NO_Q = {"divorce_status": ("Is a divorce case already filed or decided?", "क्या तलाक का मामला पहले से दायर या तय हो चुका है?", "விவாகரத்து வழக்கு ஏற்கனவே தாக்கல் செய்யப்பட்டதா அல்லது முடிந்ததா?")}
NUMERIC = {"separated_months": (0, 1200), "marriage_years": (0, 100)}
BOOL_SLOTS = [sl for sl in DOMAIN if sl not in NUMERIC and sl not in ("ground", "divorce_status")]
SESSION_TTL = 2 * 3600  # seconds idle before a session (and the facts typed into it) is dropped
_L = {"en": 0, "hi": 1, "ta": 2}
DOCS = {
 "divorce": ["Marriage certificate or proof of marriage", "ID and address proof of both parties", "Details and birth dates of children", "Evidence for the ground (messages, medical or police records, witnesses)", "Dates of marriage, separation and last cohabitation"],
 "maintenance": ["Income proof (salary slips, ITR) of both sides, as far as available", "Bank statements for the last 2–3 years", "Monthly expense list including children's fees and medical costs", "Property and loan details for the Rajnesh v. Neha affidavit", "Proof of the other party's means (job, business, property)"],
 "dv": ["Written account of incidents with dates", "Medical reports and photographs", "Police complaint or DIR from the Protection Officer, if any", "Proof of shared household"],
 "parent": ["Proof of relationship (birth certificates, family records)", "Proof of age and inability to self-support", "Details of the child's or relative's income or property"],
 "talaq": ["Nikahnama", "Written record of the talaq procedure followed", "Notices exchanged between the parties"],
}


def _facts(d):
    return Facts(**{k: v for k, v in d.items() if k in {f.name for f in fields(Facts)}})


def _sig(d):
    return frozenset((r["id"], r["status"], tuple(sorted(v["basis"] for v in r["venues"]))) for r in advise(_facts(d))["remedies"])


def gain(facts: dict, slot: str) -> float:
    pr = PRIOR.get(slot) or [1 / len(DOMAIN[slot])] * len(DOMAIN[slot]); mass = Counter()
    for v, p in zip(DOMAIN[slot], pr): mass[_sig({**facts, slot: v})] += p
    return -sum(p * math.log2(p) for p in mass.values() if p > 0)


def next_slot(facts: dict, known: set, rng=None, thresh=THRESH):
    if "law" not in facts or "law" not in known: return "law"
    if "claimant" not in known: return "claimant"
    if "needs" not in known and facts.get("claimant") in ("wife", "husband"): return "needs"
    scored = [(gain(facts, s), s) for s in DOMAIN if s not in known]
    scored = [x for x in scored if x[0] > max(thresh, 1e-9)]
    if not scored: return None
    if rng is not None: return rng.choice(scored)[1]          # ablation: random informative question
    best = max(g for g, _ in scored)
    return next(s for g, s in scored if g == best)             # ties: DOMAIN order


def unchecked(facts: dict, known: set, lang="en"):
    if "law" not in facts: return []
    return [{"slot": sl, "prompt": Q[sl][_L[lang]] if sl != "divorce_status" else YES_NO_Q["divorce_status"][_L[lang]]}
            for sl in DOMAIN if sl not in known and (sl in BOOL_SLOTS or sl == "divorce_status") and 1e-9 < gain(facts, sl) <= THRESH]


def make_question(slot, lang, facts=None):
    i = _L[lang]
    if slot in OPTS:
        labels = LBL[slot][lang]
        opts = [{"value": v, "label": l} for v, l in zip(OPTS[slot], labels)]
        return {"slot": slot, "kind": "multi" if slot == "needs" else "choice", "prompt": Q[slot][i], "options": opts,
                "selected": (facts or {}).get("needs", []) if slot == "needs" else None}
    y, n = YN[lang]
    return {"slot": slot, "kind": "choice", "prompt": Q[slot][i], "options": [{"value": True, "label": y}, {"value": False, "label": n}]}


def why(facts, slot):
    """Titles of remedies whose status or existence changes depending on this unknown fact."""
    if "law" not in facts or slot not in DOMAIN: return []
    seen = {}
    for v in DOMAIN[slot]:
        try: a = advise(_facts({**facts, slot: v}))
        except Exception: return []
        for r in a["remedies"]: seen.setdefault(r["id"], {"t": r["title"], "st": set()})["st"].add(r["status"])
        for rid in list(seen):
            if rid not in {r["id"] for r in a["remedies"]}: seen[rid]["st"].add("absent")
    return [d["t"] for d in seen.values() if len(d["st"]) > 1]


def plan(advice, lang="en"):
    steps, rs = [], advice["remedies"]
    order = sorted(rs, key=lambda r: (r["id"] != "dv_act", r["id"] == "crpc125", r["id"].startswith(("hma_24", "sma_36", "ida_36", "parsi_39"))))
    for r in order:
        cat = "dv" if r["id"] == "dv_act" else "talaq" if r["id"].startswith("muslim") else "parent" if r["id"] == "senior_citizens" else \
              "divorce" if r["id"] in ("hma_13", "hma_13b", "sma_27", "sma_28", "ida_10", "ida_10a", "parsi_32", "parsi_32b", "dmma_2") else "maintenance"
        steps.append({"id": r["id"], "title": r["title"], "detail": f'{r["provision"]}. File at: {r["forum"]}.', "status": r["status"],
                      "open": r["conditions_open"], "docs": DOCS[cat]})
    return steps


class Session:
    def __init__(self):
        self.facts, self.known, self.asked, self.lang = {}, set(), [], "en"
        self.skipped, self.tentative, self.conflicts = [], {}, {}
        self.sid = uuid.uuid4().hex[:12]
        self.touched = time.time()


STORE: "OrderedDict[str, Session]" = OrderedDict()


def _get(sid, snap=None):
    now = time.time()
    for k in [k for k, v in STORE.items() if now - v.touched > SESSION_TTL]: del STORE[k]
    if sid and sid in STORE: STORE.move_to_end(sid); STORE[sid].touched = now; return STORE[sid]
    s = restore(sid, snap) if (sid and snap) else Session(); STORE[s.sid] = s
    while len(STORE) > 500: STORE.popitem(last=False)
    return s


PLACE_KEYS = ("marriage_place", "last_cohabitation_place", "petitioner_residence", "respondent_residence")


def snapshot(s: Session) -> dict:
    """Everything needed to rebuild a session after a server restart. Sent to the browser and sent back by it; nothing is stored server-side."""
    return {"facts": s.facts, "known": sorted(s.known), "asked": s.asked[-40:], "skipped": s.skipped[-40:], "lang": s.lang,
            "tentative": s.tentative, "conflicts": s.conflicts}


def _short(v):
    return isinstance(v, (str, bool, int, float)) and (not isinstance(v, str) or len(v) <= 120)


def restore(sid, snap) -> Session:
    """Rebuild a session from an untrusted snapshot. Every fact is re-validated through _apply; anything invalid is dropped."""
    s = Session()
    if isinstance(sid, str) and 0 < len(sid) <= 64: s.sid = sid
    if not isinstance(snap, dict): return s
    facts = snap.get("facts") if isinstance(snap.get("facts"), dict) else {}
    known = set(snap.get("known") or []) if isinstance(snap.get("known"), list) else set()
    for slot in ("law", "claimant", "needs", "ground", "divorce_status", *NUMERIC, *BOOL_SLOTS):
        if slot in facts and (slot in known or slot == "needs"):
            try: _apply(s, slot, facts[slot])
            except (ValueError, TypeError): pass
    places = {k: facts[k] for k in PLACE_KEYS if isinstance(facts.get(k), str)}
    if places: _apply(s, "places", places)
    if snap.get("lang") in _L: s.lang = snap["lang"]
    s.asked = [a for a in (snap.get("asked") or []) if isinstance(a, str) and len(a) <= 40][-40:] if isinstance(snap.get("asked"), list) else []
    s.skipped = [a for a in (snap.get("skipped") or []) if isinstance(a, str) and len(a) <= 40][-40:] if isinstance(snap.get("skipped"), list) else []
    s.known |= {k for k in s.skipped if k in DOMAIN}
    tent = snap.get("tentative") if isinstance(snap.get("tentative"), dict) else {}
    for k, t in tent.items():
        if (k in DOMAIN or k in ("law", "claimant", "needs")) and k not in s.known and isinstance(t, dict) and "value" in t:
            v = t["value"]
            if (isinstance(v, list) and all(_short(x) for x in v[:5])) or _short(v):
                s.tentative[k] = {"value": v, "why": str(t.get("why") or "")[:120], "source": str(t.get("source") or "")[:40]}
    conf = snap.get("conflicts") if isinstance(snap.get("conflicts"), dict) else {}
    for k, v in conf.items():
        if k in ("law", "claimant") and k not in s.known and isinstance(v, list) and all(isinstance(x, str) for x in v[:6]): s.conflicts[k] = v[:6]
    return s


def forget(sid) -> bool:
    """Delete a session and everything typed into it."""
    return STORE.pop(sid, None) is not None


def _bool(v):
    if isinstance(v, bool): return v
    if isinstance(v, str) and v.strip().lower() in ("true", "yes", "1", "false", "no", "0"): return v.strip().lower() in ("true", "yes", "1")
    raise ValueError("expected true or false")


def _apply(s: Session, slot, value):
    """Apply one answer. Raises ValueError on anything that is not a valid answer for that slot."""
    if slot == "places":
        if not isinstance(value, dict): raise ValueError("places must be an object")
        for k in ("marriage_place", "last_cohabitation_place", "petitioner_residence", "respondent_residence"):
            if value.get(k): s.facts[k] = str(value[k]).strip()[:80]
        return
    if slot == "skip":
        if s.asked and s.asked[-1] in DOMAIN: s.known.add(s.asked[-1]); s.skipped.append(s.asked[-1])
        return
    if slot == "law":
        if value not in LAWS: raise ValueError("unknown law")
        s.facts["law"] = value
    elif slot == "claimant":
        if value not in OPTS["claimant"]: raise ValueError("unknown claimant")
        s.facts["claimant"] = value
    elif slot == "needs":
        if not isinstance(value, list) or not set(value) <= set(OPTS["needs"]): raise ValueError("needs must be a list of known needs")
        s.facts["needs"] = list(dict.fromkeys(value))
    elif slot == "ground":
        if value not in OPTS["ground"]: raise ValueError("unknown ground")
        s.facts["ground"] = None if value == "none" else value
    elif slot == "divorce_status":
        if isinstance(value, bool): value = "filed" if value else "none"   # tick/cross from the 'not yet checked' list
        if value not in OPTS["divorce_status"] + ["filed"]: raise ValueError("unknown divorce status")
        s.facts["divorce_status"] = value
    elif slot in NUMERIC:
        lo, hi = NUMERIC[slot]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not lo <= value <= hi: raise ValueError(f"{slot} out of range")
        s.facts[slot] = float(value)
    elif slot in BOOL_SLOTS: s.facts[slot] = _bool(value)
    else: raise ValueError("unknown slot")
    s.known.add(slot); s.tentative.pop(slot, None); s.conflicts.pop(slot, None)


LAW_LABEL = {"hindu": "Hindu / Sikh / Jain / Buddhist", "muslim": "Muslim", "christian": "Christian", "parsi": "Parsi", "special_marriage": "Special Marriage Act"}


def _ok_fact(k, v) -> bool:
    """Is v an acceptable value for slot k? Intake output is checked with the same rules as a typed answer, so odd text can never become a 422."""
    if k in NUMERIC: lo, hi = NUMERIC[k]; return isinstance(v, (int, float)) and not isinstance(v, bool) and lo <= v <= hi
    if k == "law": return v in LAWS
    if k == "claimant": return v in OPTS["claimant"]
    if k == "ground": return v is None or v in OPTS["ground"]
    if k == "divorce_status": return v in OPTS["divorce_status"]
    if k in BOOL_SLOTS: return isinstance(v, bool)
    return False


def _absorb(s: Session, r: dict):
    """Merge one intake result. Confident facts lock in; tentative suggestions never do (the user is still asked)."""
    for k, v in r["facts"].items():
        if k == "needs": s.facts["needs"] = sorted(set(s.facts.get("needs", [])) | (set(v) & set(OPTS["needs"])))
        elif not _ok_fact(k, v): continue            # e.g. "left 101 years ago": drop it and ask instead of failing
        else: s.facts[k] = v; s.known.add(k); s.tentative.pop(k, None); s.conflicts.pop(k, None)
    for k in r.get("not_needs", []):
        s.facts["needs"] = [n for n in s.facts.get("needs", []) if n != k]
    for k, v in r.get("tentative", {}).items():
        if k not in s.known and k != "needs": s.tentative[k] = v
        elif k == "needs": s.tentative["needs"] = v
    for k, v in r.get("conflicts", {}).items():
        if k not in s.known: s.conflicts[k] = v


def understood(s: Session) -> list:
    """What the agent thinks it knows, with how it knows. For the UI to show and let the person correct."""
    out = [{"slot": k, "value": v, "status": "confirmed" if k in s.known else "stated"} for k, v in s.facts.items() if k != "needs" and k in s.known]
    out += [{"slot": k, "value": t["value"], "status": "suggested", "why": t.get("why"), "source": t.get("source")} for k, t in s.tentative.items()]
    out += [{"slot": k, "value": v, "status": "conflict"} for k, v in s.conflicts.items()]
    return out


def step(session_id=None, text=None, answer=None, max_questions=10, lang=None, snap=None):
    r = _step(session_id, text, answer, max_questions, lang, snap)
    r["snapshot"] = snapshot(STORE[r["session_id"]])
    return r


def _step(session_id, text, answer, max_questions, lang, snap):
    s = _get(session_id, snap)
    if text:
        r = slm.augment(text, extract(text)); s.lang = r["language"]; _absorb(s, r)
    if lang in _L: s.lang = lang  # UI language wins over detected language
    if answer: _apply(s, answer.get("slot"), answer.get("value"))
    slot = None if len(s.asked) >= max_questions else next_slot(s.facts, s.known)
    base = {"session_id": s.sid, "language": s.lang, "facts": s.facts, "asked": len(s.asked),
            "understood": understood(s), "conflicts": s.conflicts, "engine": slm.status()["backend"]}
    if slot:
        s.asked.append(slot)
        q = make_question(slot, s.lang, s.facts); q["affects"] = why(s.facts, slot)
        sug = s.tentative.get(slot)
        if slot == "needs" and sug: q["selected"] = sorted(set(q.get("selected") or []) | set(sug["value"]))
        elif sug: q["suggested"] = sug
        if slot == "law" and "law" in s.conflicts: q["conflict"] = s.conflicts["law"]
        prov = None
        if "law" in s.facts and "law" in s.known and s.facts.get("needs"):
            try: prov = advise(_facts(s.facts))
            except Exception: prov = None
        return {**base, "state": "clarify", "reply": Q[slot][_L[s.lang]], "question": q,
                "provisional": prov, "plan": plan(prov, s.lang) if prov else [], "skipped": s.skipped}
    if "law" not in s.facts:
        return {**base, "state": "clarify", "reply": Q["law"][_L[s.lang]], "question": make_question("law", s.lang)}
    adv = advise(_facts(s.facts)); n = len(adv["remedies"])
    reply = FRAME["none"][_L[s.lang]] if not n else FRAME["advice"][_L[s.lang]].format(n=n, first=adv["remedies"][0]["title"])
    return {**base, "state": "advice", "reply": reply, "advice": adv, "plan": plan(adv, s.lang),
            "unchecked": unchecked(s.facts, s.known, s.lang), "skipped": s.skipped,
            "place_fields": ["marriage_place", "last_cohabitation_place", "petitioner_residence", "respondent_residence"]}
