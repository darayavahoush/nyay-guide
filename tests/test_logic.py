"""Engine, intake, agent and API behaviour added in the logic pass. Each test names the bug it guards."""
import pytest
from fastapi.testclient import TestClient
from app.india import Facts, advise, agent as A
from app.india.intake import extract
from app.main import app

def rem(**k): return {r["id"]: r for r in advise(Facts(**k))["remedies"]}

# ---- engine
def test_alimony_depends_on_case_status():
    base = dict(law="hindu", needs=["maintenance"])
    assert rem(**base, divorce_status="pending")["hma_24_25"]["status"] == "eligible"
    assert rem(**base)["hma_24_25"]["status"] == "conditional"                      # nothing filed, nothing planned
    d = rem(**base, divorce_status="decreed")["hma_24_25"]
    assert d["status"] == "eligible" and any("permanent" in n for n in d["notes"])
    assert rem(law="hindu", needs=["divorce", "maintenance"])["hma_24_25"]["status"] == "eligible"   # will be filed with the petition

def test_hama18_is_for_a_subsisting_marriage():
    assert "hama_18" not in rem(law="hindu", needs=["maintenance"], divorce_status="decreed")
    assert "hama_18" in rem(law="hindu", needs=["maintenance"], divorce_status="pending")

def test_hama18_unchaste_wife_disqualified():
    assert rem(law="hindu", needs=["maintenance"], claimant_living_in_adultery=True)["hama_18"]["status"] == "conditional"

def test_1986_act_needs_a_divorce():
    assert rem(law="muslim", needs=["maintenance"], divorce_status="pending")["mwpra_1986"]["status"] == "conditional"
    assert rem(law="muslim", needs=["maintenance"], divorce_status="decreed")["mwpra_1986"]["status"] == "eligible"

@pytest.mark.parametrize("law,rid", [("hindu", "hma_13"), ("special_marriage", "sma_27"), ("christian", "ida_10"), ("parsi", "parsi_32")])
def test_desertion_needs_two_continuous_years(law, rid):
    assert rem(law=law, needs=["divorce"], ground="desertion", separated_months=6)[rid]["status"] == "conditional"
    assert rem(law=law, needs=["divorce"], ground="desertion", separated_months=30)[rid]["status"] == "eligible"
    assert rem(law=law, needs=["divorce"], ground="cruelty", separated_months=6)[rid]["status"] == "eligible"

def test_decree_blocks_a_second_divorce_petition():
    a = advise(Facts(law="hindu", needs=["divorce", "maintenance"], divorce_status="decreed"))
    assert not any(r["id"].startswith(("hma_13", "sma_2")) for r in a["remedies"]) and any("decree already exists" in w for w in a["warnings"])

def test_divorce_is_not_offered_to_a_child_or_parent():
    a = advise(Facts(law="hindu", claimant="child", needs=["divorce", "maintenance"]))
    assert not any(r["id"] == "hma_13" for r in a["remedies"]) and any("Divorce is a remedy between spouses" in w for w in a["warnings"])

def test_dv_act_gap_is_disclosed_for_non_wives():
    a = advise(Facts(law="hindu", claimant="parent", needs=["maintenance", "protection"]))
    assert not any(r["id"] == "dv_act" for r in a["remedies"]) and any("Domestic Violence Act" in w for w in a["warnings"])

@pytest.mark.parametrize("bad", [dict(claimant="alien"), dict(needs=["custody"]), dict(marriage_years=-1), dict(marriage_years=float("nan")),
                                 dict(separated_months=99999), dict(mutual_consent="yes"), dict(marriage_place="x" * 200), dict(divorce_status="maybe"), dict(marriage_years=True)])
def test_facts_reject_garbage(bad):
    with pytest.raises(ValueError): Facts(law="hindu", **bad)

# ---- intake: each line is a bug the v1 lexicon had
def test_denied_violence_is_not_violence():
    f = extract("My husband never beat me, but he left. I am Hindu and want maintenance")["facts"]
    assert f["domestic_violence"] is False and "protection" not in f["needs"]

def test_does_not_stop_beating_is_violence():
    assert extract("he does not stop beating me")["facts"]["domestic_violence"] is True

def test_two_laws_is_a_conflict_not_a_guess():
    r = extract("I am Hindu, married a Christian man, want divorce")
    assert "law" not in r["facts"] and r["conflicts"]["law"] == ["christian", "hindu"]

def test_special_marriage_act_wins_when_named():
    assert extract("We are Hindu and Christian, married under the Special Marriage Act")["facts"]["law"] == "special_marriage"

def test_not_muslim_is_not_muslim():
    assert extract("Not Muslim, I am Hindu")["facts"]["law"] == "hindu"
    assert "law" not in extract("I am not Hindu")["facts"]

def test_refusing_spouse_is_not_mutual_consent():
    assert extract("We have mutual friends but he does not agree to divorce")["facts"]["mutual_consent"] is False
    assert extract("both of us agree to the divorce")["facts"]["mutual_consent"] is True

def test_needs_negation_only_for_wishes():
    f = extract("I don't want a divorce, only maintenance")["facts"]; assert f["needs"] == ["maintenance"]
    f = extract("he doesn't give me maintenance")["facts"]; assert f["needs"] == ["maintenance"]       # a complaint, not a refusal of the need

def test_durations_attach_to_the_right_thing():
    f = extract("I was married 5 years ago and we have been separated for two years")["facts"]
    assert f["marriage_years"] == 5 and f["separated_months"] == 24
    f = extract("separated 8 months, married for 3 years")["facts"]
    assert f["marriage_years"] == 3 and f["separated_months"] == 8
    assert "separated_months" not in extract("married for 5 years")["facts"]

def test_word_boundaries():
    assert "ground" not in extract("I read about the affairs of state")["facts"]
    assert "law" not in extract("my friend Jainab called")["facts"]

def test_tamil_basis_is_not_beating():
    assert "domestic_violence" not in extract("நான் இந்து, அடிப்படையில் விவாகரத்து வேண்டும்")["facts"]

def test_hindi_and_tamil_denials():
    assert extract("मेरे पति मुझे मारपीट नहीं करते")["facts"]["domestic_violence"] is False
    assert extract("என் கணவர் என்னை அடிக்கவில்லை")["facts"]["domestic_violence"] is False

def test_romanised_hindi():
    f = extract("mera pati mujhe maarta hai, hum hindu hain, talaq chahiye")["facts"]
    assert f["law"] == "hindu" and f["claimant"] == "wife" and f["domestic_violence"] is True and "divorce" in f["needs"]

def test_cultural_hints_are_suggestions_only():
    r = extract("our nikah was in 2019")
    assert "law" not in r["facts"] and r["tentative"]["law"]["value"] == "muslim"

def test_case_status_words():
    assert extract("my divorce case is pending in court")["facts"]["divorce_status"] == "pending"
    assert extract("I am divorced")["facts"]["divorce_status"] == "decreed"
    assert extract("not divorced yet")["facts"]["divorce_status"] == "none"

# ---- agent
def test_suggestion_is_asked_not_locked():
    r = A.step(text="our nikah was in 2019, he beats me")
    assert r["question"]["slot"] == "law" and r["question"]["suggested"]["value"] == "muslim" and "law" not in r["facts"]
    assert any(u["status"] == "suggested" for u in r["understood"])

def test_conflict_is_asked():
    r = A.step(text="I am Hindu, married a Christian man, want divorce")
    assert r["question"]["slot"] == "law" and r["question"]["conflict"] == ["christian", "hindu"]

def test_confirming_clears_the_suggestion():
    r = A.step(text="our nikah was in 2019")
    r = A.step(r["session_id"], answer={"slot": "law", "value": "muslim"})
    assert r["facts"]["law"] == "muslim" and not any(u["slot"] == "law" and u["status"] == "suggested" for u in r["understood"])

@pytest.mark.parametrize("slot,value", [("law", "martian"), ("claimant", "x"), ("needs", "divorce"), ("needs", ["custody"]), ("mutual_consent", [1]),
                                        ("separated_months", True), ("separated_months", -3), ("ground", 5), ("nonsense", 1), ("places", "Trichy")])
def test_agent_rejects_invalid_answers(slot, value):
    r = A.step(text="Hindu wife, need divorce")
    with pytest.raises(ValueError): A.step(r["session_id"], answer={"slot": slot, "value": value})

def test_tick_cross_on_case_status_maps_to_filed_and_none():
    s = A._get(None); A._apply(s, "divorce_status", True); assert s.facts["divorce_status"] == "filed"
    A._apply(s, "divorce_status", False); assert s.facts["divorce_status"] == "none"

def test_unchecked_only_lists_tickable_slots():
    r = A.step(text="I am a Hindu wife, need maintenance")
    sid = r["session_id"]
    for _ in range(12):
        if r["state"] != "clarify": break
        q = r["question"]; r = A.step(sid, answer={"slot": "skip", "value": None} if q["slot"] not in ("law", "claimant", "needs") else {"slot": q["slot"], "value": q["options"][0]["value"] if q["kind"] == "choice" else q["selected"]})
    assert r["state"] == "advice" and not {"separated_months", "marriage_years", "ground"} & {u["slot"] for u in r["unchecked"]}

def test_sessions_expire_and_can_be_deleted(monkeypatch):
    r = A.step(text="Hindu wife"); sid = r["session_id"]
    assert A.forget(sid) and not A.forget(sid)
    r = A.step(text="Hindu wife"); sid = r["session_id"]
    A.STORE[sid].touched -= A.SESSION_TTL + 1
    assert A.step(sid, text="x")["session_id"] != sid

# ---- API
c = TestClient(app)

def test_api_health_reports_engine():
    j = c.get("/api/health").json(); assert j["ok"] is True and "backend" in j["slm"]

def test_api_bad_answer_is_422_not_500():
    sid = c.post("/api/india/agent", json={"text": "Hindu wife need divorce"}).json()["session_id"]
    assert c.post("/api/india/agent", json={"session_id": sid, "answer": {"slot": "law", "value": "martian"}}).status_code == 422
    assert c.post("/api/india/agent", json={"session_id": sid, "answer": {"slot": "needs", "value": "divorce"}}).status_code == 422

def test_api_advise_validates():
    assert c.post("/api/india/advise", json={"law": "martian"}).status_code == 422
    assert c.post("/api/india/advise", json={"law": "hindu", "claimant": "alien"}).status_code == 422
    assert c.post("/api/india/advise", json={"law": "hindu", "needs": ["divorce"], "ground": "cruelty"}).status_code == 200

def test_api_delete_session():
    sid = c.post("/api/india/agent", json={"text": "Hindu wife"}).json()["session_id"]
    assert c.delete(f"/api/india/session/{sid}").status_code == 204

# ---- optional Groq fallback (mocked; never calls the network)
def test_groq_output_is_validated(monkeypatch):
    from app.india import groq_assist as G
    assert G.clean({"law": "martian", "ground": "cruelty", "needs": ["divorce", "custody"], "domestic_violence": "yes", "mutual_consent": False, "x": 1}) \
        == {"ground": "cruelty", "mutual_consent": False}
    assert G.clean({"domestic_violence": False}) == {}                 # it may only ever add a positive violence claim
    assert G.clean({"needs": ["divorce", "protection"]}) == {"needs": ["divorce", "protection"]}

def test_groq_is_off_unless_enabled_and_keyed(monkeypatch):
    from app.india import groq_assist as G
    monkeypatch.delenv("GROQ_ENABLE", raising=False); monkeypatch.setenv("GROQ_API_KEY", "k")
    assert not G.enabled() and G.suggest("a long enough sentence about my husband and our troubles") == {}
    monkeypatch.setenv("GROQ_ENABLE", "1"); monkeypatch.delenv("GROQ_API_KEY"); assert not G.enabled()

def test_groq_only_runs_when_nothing_else_found_and_only_suggests(monkeypatch):
    from app.india import groq_assist as G
    monkeypatch.setattr(G, "suggest", lambda t: {"ground": {"value": "cruelty", "why": "w", "source": "groq:x"}})
    r = A.step(text="He taunts me daily and makes my life miserable every single day")
    assert "ground" not in r["facts"] and any(u["slot"] == "ground" and u["status"] == "suggested" for u in r["understood"])
    r = A.step(text="I am Hindu and he taunts me daily and makes my life miserable")      # lexicon found the law: Groq not consulted
    assert not any(u["slot"] == "ground" for u in r["understood"])

def test_groq_failure_is_silent(monkeypatch):
    import urllib.request
    from app.india import groq_assist as G
    monkeypatch.setenv("GROQ_ENABLE", "1"); monkeypatch.setenv("GROQ_API_KEY", "k")
    def boom(*a, **k): raise OSError("offline")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    assert G.suggest("a long enough sentence about my husband and our troubles") == {}

def test_tamil_adikkadi_means_often_not_beating():
    assert "domestic_violence" not in extract("கணவர் அடிக்கடி வெளியே செல்கிறார்")["facts"]
    assert extract("கணவர் என்னை அடிக்கிறார்")["facts"]["domestic_violence"] is True

def test_do_not_want_divorce_is_not_a_refusal_by_the_spouse():
    assert "mutual_consent" not in extract("I do not want divorce, I only need maintenance")["facts"]

# ---- sessions survive a server restart (Render free restarts and spins down)
def test_session_survives_restart_via_snapshot():
    r = A.step(text="I am a Hindu wife. My husband left two years ago and I need maintenance")
    sid, snap = r["session_id"], r["snapshot"]
    while r["state"] == "clarify" and r["facts"].get("claimant") is None:
        q = r["question"]; r = A.step(sid, answer={"slot": q["slot"], "value": q["options"][0]["value"]}, snap=r["snapshot"])
    snap = r["snapshot"]; A.STORE.clear()                                    # the server restarts
    r2 = A.step(sid, answer={"slot": "places", "value": {"petitioner_residence": "Trichy"}}, snap=snap)
    assert r2["facts"]["law"] == "hindu" and r2["facts"]["petitioner_residence"] == "Trichy"
    assert not (r2["state"] == "clarify" and r2["question"]["slot"] == "law")      # does not start over

def test_without_snapshot_a_lost_session_starts_over():
    A.STORE.clear(); r = A.step("lost-id", answer={"slot": "places", "value": {"marriage_place": "x"}})
    assert r["state"] == "clarify" and r["question"]["slot"] == "law"

def test_hostile_snapshot_is_validated():
    snap = {"facts": {"law": "martian", "needs": ["custody"], "separated_months": -5, "marriage_place": "x" * 500, "evil": 1, "domestic_violence": "yes"},
            "known": ["law", "separated_months", "domestic_violence"], "asked": ["a" * 500, 5], "tentative": {"law": {"value": {"a": 1}}, "ground": {"value": "cruelty", "why": "w" * 999}},
            "conflicts": {"law": "nope"}, "lang": "xx"}
    r = A.step("hostile-1", text=None, answer=None, snap=snap)
    assert "law" not in r["facts"] and "evil" not in r["facts"] and r["state"] == "clarify" and r["language"] == "en"
    assert all(len(str(v)) <= 80 for k, v in r["facts"].items() if isinstance(v, str))
    assert len(r["snapshot"]["tentative"].get("ground", {}).get("why", "")) <= 120

def test_api_roundtrip_and_head_route():
    j = c.post("/api/india/agent", json={"text": "Hindu wife need maintenance"}).json()
    assert "snapshot" in j
    A.STORE.clear()
    assert c.post("/api/india/agent", json={"session_id": j["session_id"], "snapshot": j["snapshot"], "answer": {"slot": "places", "value": {"marriage_place": "Chennai"}}}).status_code == 200
    assert c.post("/api/india/agent", json={"snapshot": "not-a-dict"}).status_code == 422          # shape errors are 422 with a reason
    assert c.head("/api/health").status_code in (200, 405)


# ---- the 422 on odd durations, and venues for the claimant's own place
@pytest.mark.parametrize("text", ["my husband left 101 years ago. Hindu wife needs maintenance", "I am Hindu wife, married 150 years, need divorce",
                                  "Muslim wife left 2005 months ago and needs maintenance", "married 99999 saal, separated 5000 months, Hindu"])
def test_absurd_durations_are_dropped_not_422(text):
    r = A.step(text=text)
    for _ in range(14):
        if r["state"] != "clarify": break
        q = r["question"]; v = q.get("selected") if q["kind"] == "multi" else q["options"][0]["value"] if q["kind"] == "choice" else False
        r = A.step(r["session_id"], answer={"slot": q["slot"], "value": v}, snap=r["snapshot"])
    assert r["state"] == "advice" and r["facts"].get("separated_months", 0) <= 1200 and r["facts"].get("marriage_years", 0) <= 100

def test_s125_includes_the_wifes_own_residence():
    v = {x["basis"]: x["place"] for x in rem(law="hindu", claimant="wife", needs=["maintenance"], petitioner_residence="Trichy", respondent_residence="Madurai")["crpc125"]["venues"]}
    assert v["petitioner"] == "Trichy" and v["respondent"] == "Madurai"

def test_places_produce_visible_forums_for_every_route():
    r = A.step(text="I am a Hindu wife, he left, I need divorce and maintenance")
    for _ in range(14):
        if r["state"] != "clarify": break
        q = r["question"]; v = q.get("selected") if q["kind"] == "multi" else q["options"][0]["value"] if q["kind"] == "choice" else False
        r = A.step(r["session_id"], answer={"slot": q["slot"], "value": v}, snap=r["snapshot"])
    r = A.step(r["session_id"], answer={"slot": "places", "value": {"petitioner_residence": "Trichy", "respondent_residence": "Madurai", "marriage_place": "Chennai"}}, snap=r["snapshot"])
    placed = {rm["id"]: [v["place"] for v in rm["venues"] if v["place"]] for rm in r["advice"]["remedies"]}
    assert all(placed[k] for k in placed if k not in ("hma_24_25", "hama_18")), placed
