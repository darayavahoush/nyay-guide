"""Question-efficiency evaluation of the agent's information-gain policy.
PYTHONPATH=backend python -m research.agent_eval
Policies: ask_all (every slot), random_informative (random order, asks only slots that can change the outcome),
ig_all (max information gain, thresh=0), ig_thresh (default policy). Oracle answers come from the scenario.
Accuracy = final outcome signature (remedy, status, venue bases) equals the one with every fact known."""
import random, statistics as st
from app.india import agent as A
from app.india.intake import extract
from .india_scenarios import S

def true_facts(sc):
    f = dict(sc["facts"])
    for sl, dom in A.DOMAIN.items():
        if f.get(sl) is None: f[sl] = dom[0]
    f.setdefault("claimant", "wife"); f.setdefault("needs", [])
    return f

def run(sc, policy, rng, budget=20):
    truth = true_facts(sc); r = extract(sc["text"]); facts = {k: v for k, v in r["facts"].items()}; known = set(r["facts"]) - {"needs"}
    asked = 0
    if policy == "ask_all":
        for sl in ("law", "claimant", "needs"):
            if sl not in known and not (sl == "needs" and truth["claimant"] in ("child", "parent")): asked += 1
        facts.update(truth); asked += sum(1 for sl in A.DOMAIN if sl not in known); return asked, A._sig(facts) == A._sig(truth)
    while asked < budget:
        sl = A.next_slot(facts, known, rng=rng if policy == "random_informative" else None, thresh=0 if policy != "ig_thresh" else A.THRESH)
        if sl is None: break
        facts[sl] = truth.get(sl); known.add(sl); asked += 1
        if sl == "needs": facts["needs"] = truth["needs"]
    return asked, A._sig(facts) == A._sig(truth)

if __name__ == "__main__":
    print(f"{len(S)} scenarios (developer-authored)")
    print("accuracy under a question budget (policy ignores the stop rule, thresh=0):")
    for b in (2, 3, 4, 5):
        ig = st.mean(run(sc, "ig_all", random.Random(0), b)[1] for sc in S)
        rd = st.mean(run(sc, "random_informative", random.Random(i), b)[1] for i in range(30) for sc in S)
        print(f"  budget={b}: information-gain={ig:.2f}  random-informative={rd:.2f}")
    for pol in ("ask_all", "random_informative", "ig_all", "ig_thresh"):
        res = [run(sc, pol, random.Random(i)) for i in range(20 if pol == "random_informative" else 1) for sc in S]
        print(f"{pol:20s} questions={st.mean(a for a, _ in res):5.2f}  accuracy={st.mean(ok for _, ok in res):.2f}")
