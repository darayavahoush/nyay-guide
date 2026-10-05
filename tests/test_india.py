from app.india import Facts, advise
ids = lambda **k: {r["id"] for r in advise(Facts(**k))["remedies"]}
def get(rid, **k): return next(r for r in advise(Facts(**k))["remedies"] if r["id"] == rid)
def test_hindu_wife_gets_s19_wife_venue():
    r = get("hma_13", law="hindu", needs=["divorce"], ground="cruelty", petitioner_residence="X")
    assert "petitioner" in {v["basis"] for v in r["venues"]}
def test_hindu_husband_no_petitioner_venue():
    r = get("hma_13", law="hindu", claimant="husband", needs=["divorce"], ground="x")
    assert "petitioner" not in {v["basis"] for v in r["venues"]}
def test_no_cross_law():
    assert not ids(law="muslim", needs=["divorce", "maintenance"], ground="g") & {"hma_13", "hma_24_25", "hama_18"}
def test_one_year_bar():
    assert get("hma_13", law="hindu", needs=["divorce"], ground="g", marriage_years=0.4)["status"] == "conditional"
def test_mutual_needs_year():
    assert get("hma_13b", law="hindu", needs=["divorce"], mutual_consent=True, separated_months=6)["status"] == "conditional"
    assert get("hma_13b", law="hindu", needs=["divorce"], mutual_consent=True, separated_months=14)["status"] == "eligible"
def test_s125_disqualifiers():
    assert get("crpc125", law="hindu", needs=["maintenance"], claimant_living_in_adultery=True)["status"] == "conditional"
def test_talaq_husband_only():
    assert "muslim_talaq" in ids(law="muslim", claimant="husband", needs=["divorce"])
def test_bad_law():
    try: advise(Facts(law="martian")); assert False
    except ValueError: pass
from app.india.intake import extract
def test_intake_hi():
    r = extract("मैं हिंदू हूँ, मेरे पति ने मुझे छोड़ दिया, मुझे तलाक और गुजारा चाहिए")
    f = r["facts"]; assert f["law"] == "hindu" and f["claimant"] == "wife" and set(f["needs"]) == {"divorce", "maintenance"} and r["language"] == "hi"
def test_intake_ta():
    r = extract("நான் இந்து, என் கணவர் என்னை கொடுமை செய்கிறார், விவாகரத்து வேண்டும்")
    f = r["facts"]; assert f["law"] == "hindu" and f["claimant"] == "wife" and f["ground"] == "cruelty" and "divorce" in f["needs"] and r["language"] == "ta"
def test_intake_en_husband_mutual():
    f = extract("I am Muslim, my wife and I want a mutual divorce, separated 2 years")["facts"]
    assert f["law"] == "muslim" and f["claimant"] == "husband" and f["mutual_consent"] and f["separated_months"] == 24
from app.india import agent as A
def _run(text, truth):
    r = A.step(text=text)
    while r["state"] == "clarify":
        q = r["question"]; r = A.step(r["session_id"], answer={"slot": q["slot"], "value": truth.get(q["slot"], [] if q["slot"] == "needs" else False)})
    return r
def test_agent_hindu_wife_flow():
    r = _run("I am Hindu, my husband deserted me, I need divorce and maintenance", {"needs": ["divorce", "maintenance"], "claimant": "wife", "marriage_years": 3})
    assert {"hma_13", "crpc125"} <= {p["id"] for p in r["plan"]} and r["asked"] <= 8
def test_agent_hindi_language():
    r = A.step(text="मैं हिंदू हूँ, मेरे पति ने मुझे छोड़ दिया, मुझे तलाक चाहिए")
    assert r["language"] == "hi" and any("\u0900" <= c <= "\u097f" for c in r["reply"])
def test_divorced_word_is_not_divorce_need():
    f = extract("Divorced Muslim woman wants maintenance")["facts"]
    assert f["needs"] == ["maintenance"] and f["divorce_pending_or_decreed"]
def test_unchecked_listed_not_asked():
    r = _run("I am Christian wife, need maintenance", {"needs": ["maintenance"], "claimant": "wife"})
    assert r["state"] == "advice" and isinstance(r["unchecked"], list)
def test_answer_places_updates_venue():
    r = _run("I am Hindu wife, need divorce, cruelty", {"needs": ["divorce"], "claimant": "wife"})
    r2 = A.step(r["session_id"], answer={"slot": "places", "value": {"petitioner_residence": "Trichy"}})
    assert any(v["place"] == "Trichy" for p in r2["advice"]["remedies"] for v in p["venues"])


def test_ui_language_override_and_static():
    from app.india.agent import step
    r = step(None, "Hindu wife, husband left, need maintenance", None, lang="hi")
    assert r["language"] == "hi"


def test_skip_does_not_repeat_question():
    from app.india.agent import step
    r = step(None, "Hindu wife, need maintenance", None)
    sid, seen = r["session_id"], []
    for _ in range(12):
        if r["state"] != "clarify": break
        q = r["question"]; seen.append(q["slot"])
        r = step(sid, None, {"slot": "skip", "value": None} if q["slot"] not in ("law", "claimant", "needs") else {"slot": q["slot"], "value": q["options"][0]["value"] if q["kind"] == "choice" else q["selected"]})
    assert len(seen) == len(set(seen)), seen
    assert r["state"] == "advice"


def test_provisional_advice_and_why():
    from app.india.agent import step
    r = step(None, "Hindu wife, need maintenance and divorce", {"slot": "claimant", "value": "wife"})
    if r["state"] == "clarify" and r["question"]["slot"] == "needs":
        r = step(r["session_id"], None, {"slot": "needs", "value": ["divorce", "maintenance"]})
    assert r["state"] == "clarify" and r["provisional"]["remedies"]
    assert isinstance(r["question"]["affects"], list)
