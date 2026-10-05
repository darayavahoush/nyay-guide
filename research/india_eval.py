"""Evaluate rule engine vs two baselines on research/india_scenarios.py.
Run from repo root:  PYTHONPATH=backend python -m research.india_eval
Baseline B0: religion-blind (hma_13/13b for any divorce, crpc125 for any maintenance, respondent venue only).
Baseline B1: TF-IDF retrieval (top-3 remedies by cosine to the narrative, no venues). Stdlib only."""
import math, re, json, sys
from collections import Counter
from app.india import Facts, advise, CATALOGUE
from .india_scenarios import S

tok = lambda s: re.findall(r"[a-z]+", s.lower())
DOCS = {k: tok(v["title"] + " " + v["provision"] + " " + v["law"].replace("_", " ")) for k, v in CATALOGUE.items()}
DF = Counter(w for d in DOCS.values() for w in set(d))
N = len(DOCS)
def vec(ws):
    c = Counter(ws); return {w: (1 + math.log(n)) * math.log((N + 1) / (DF.get(w, 0) + 1) + 1) for w, n in c.items()}
def cos(a, b):
    num = sum(a[w] * b.get(w, 0) for w in a); d = math.sqrt(sum(x * x for x in a.values())) * math.sqrt(sum(x * x for x in b.values()))
    return num / d if d else 0
DV = {k: vec(d) for k, d in DOCS.items()}

def engine(s):
    r = advise(Facts(**s["facts"]))["remedies"]
    return {x["id"] for x in r}, {x["id"]: {v["basis"] for v in x["venues"]} for x in r}
def b0(s):
    f = s["facts"]; ids = set()
    if "divorce" in f.get("needs", []): ids.add("hma_13b" if f.get("mutual_consent") else "hma_13")
    if "maintenance" in f.get("needs", []) or f.get("claimant") in ("child", "parent"): ids.add("crpc125")
    return ids, {i: {"respondent"} for i in ids}
def b1(s):
    q = vec(tok(s["text"])); top = sorted(DV, key=lambda k: -cos(q, DV[k]))[:3]
    return set(top), {i: set() for i in top}

def score(fn):
    rec, forb, vrec, vviol, nv, nvf = [], 0, [], 0, 0, 0
    for s in S:
        ids, ven = fn(s); law = s["facts"]["law"]
        bad = {i for i in ids if CATALOGUE[i]["law"] not in (law, "all")}
        forb += bool(bad)
        rec.append(len(ids & s["required"]) / len(s["required"]))
        if s["key"]:
            got = ven.get(s["key"], set())
            vrec.append(len(got & s["vreq"]) / len(s["vreq"]) if s["vreq"] else 1.0)
            if s["vforb"]: nvf += 1; vviol += bool(got & s["vforb"])
    return dict(required_recall=round(sum(rec) / len(rec), 3), wrong_law_rate=round(forb / len(S), 3),
                venue_recall=round(sum(vrec) / len(vrec), 3) if vrec else 0, venue_violation_rate=round(vviol / nvf, 3) if nvf else 0)

if __name__ == "__main__":
    out = {n: score(f) for n, f in [("engine", engine), ("B0_religion_blind", b0), ("B1_tfidf_retrieval", b1)]}
    print(f"{len(S)} scenarios (developer-authored gold, not advocate-validated)")
    for k, v in out.items(): print(f"{k:22s}", v)
    json.dump(out, open("research/india_results.json", "w"), indent=1)
