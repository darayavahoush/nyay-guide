"""Compare intake engines on research/intake_cases.py (developer-authored, written after seeing the v1 failures, so v2 is favoured).
  PYTHONPATH=backend python -m research.intake_eval                       # v1, v2, v2+hash (and v2+onnx if model files exist)
  PYTHONPATH=backend python -m research.intake_eval --backend onnx --grid  # sweep thresholds for one backend
  PYTHONPATH=backend python -m research.intake_eval --backend onnx --grid --write   # save the chosen ones to backend/app/india/thresholds.json
Metrics (per engine):
  wrong_confident   confident facts that are wrong or not stated in the text. This is the number that must stay near 0.
  recall_confident  gold slots found as confident facts.
  recall_total      gold slots found confidently or as a correct suggestion.
  tent_correct / tent_wrong / tent_extra   suggestions: right, contradicting gold, or about a slot the gold does not list.
  conflicts         conflicts reported / conflicts expected."""
import argparse, itertools, json, sys
from pathlib import Path
from app.india import intake, slm
from .intake_cases import C
from . import intake_v1

def same(slot, a, b):
    if slot == "needs": return set(a) == set(b)
    return a == b

def score(fn):
    m = dict(wrong_confident=0, found_confident=0, gold_slots=0, found_total=0, tent_correct=0, tent_wrong=0, tent_extra=0, conflicts_found=0, conflicts_expected=0, wrong=[])
    for c in C:
        r = fn(c["text"]); g = c["gold"]; facts = r["facts"]; tent = r.get("tentative", {}); conf = r.get("conflicts", {})
        for s in c["conflict"]:
            m["conflicts_expected"] += 1; m["conflicts_found"] += s in conf
        gslots = {k for k in g}
        m["gold_slots"] += len(gslots)
        for k, v in facts.items():
            if k == "needs" and "needs" not in g: continue
            if k in g and same(k, v, g[k]): m["found_confident"] += 1; m["found_total"] += 1
            elif k in conf: continue
            else: m["wrong_confident"] += 1; m["wrong"].append((c["text"][:48], k, v))
        for k, t in tent.items():
            v = t["value"]
            if k in g and k not in facts and same(k, v, g[k]): m["tent_correct"] += 1; m["found_total"] += 1
            elif k in c["tent"] and same(k, v, c["tent"][k]): m["tent_correct"] += 1
            elif k in g and not same(k, v, g[k]) or k in c["tent"] and not same(k, v, c["tent"][k]): m["tent_wrong"] += 1; m["wrong"].append((c["text"][:48], "tent:" + k, v))
            else: m["tent_extra"] += 1
    return m

def show(name, m):
    print(f"{name:16s} wrong_confident={m['wrong_confident']:<3} recall_confident={m['found_confident']}/{m['gold_slots']:<3} recall_total={m['found_total']}/{m['gold_slots']:<3} "
          f"tent_correct={m['tent_correct']:<3} tent_wrong={m['tent_wrong']:<2} tent_extra={m['tent_extra']:<2} conflicts={m['conflicts_found']}/{m['conflicts_expected']}")

def with_slm(text):
    return slm.augment(text, intake.extract(text))

def v1(text):
    r = intake_v1.extract(text); r["facts"] = {k: v for k, v in r["facts"].items()}; return r

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--backend", choices=["hash", "onnx"]); ap.add_argument("--grid", action="store_true")
    ap.add_argument("--write", action="store_true"); ap.add_argument("--verbose", action="store_true"); a = ap.parse_args()
    print(f"{len(C)} cases (developer-authored; v2 was written after seeing v1's failures)")
    if not a.backend:
        show("v1 lexicon", score(v1)); show("v2 lexicon", score(intake.extract))
        for b in ("hash", "onnx"):
            st = slm.load(b)
            if st["ready"] and st["backend"].endswith(b): show(f"v2 + slm:{b}", score(with_slm))
            elif b == "onnx": print(f"v2 + slm:onnx    not run: {st['error']}")
        sys.exit()
    st = slm.load(a.backend)
    if not st["backend"].endswith(a.backend): sys.exit(f"{a.backend} not available: {st['error']}")
    idx = slm._INDEX
    if not a.grid: show(f"v2 + slm:{a.backend}", score(with_slm)); sys.exit()
    best = None; rows = []
    Ts = [round(x * 0.01, 2) for x in (range(40, 90, 3) if a.backend == "hash" else range(76, 96, 1))]
    for T, M in itertools.product(Ts, [0.0, 0.02, 0.03, 0.05, 0.08, 0.12]):
        idx.th = {"T": T, "M": M}; m = score(with_slm); rows.append((T, M, m))
        key = (m["tent_wrong"] == 0, m["tent_correct"], -m["tent_extra"], T)
        if best is None or key > best[0]: best = (key, T, M, m)
    for T, M, m in rows[::max(1, len(rows) // 12)]: print(f"T={T:.2f} M={M:.2f}  tent_correct={m['tent_correct']:<3} tent_wrong={m['tent_wrong']:<2} tent_extra={m['tent_extra']}")
    _, T, M, m = best; print(f"\nchosen (no wrong suggestions, then most correct, then fewest extra): T={T} M={M}"); show(f"v2 + slm:{a.backend}", m)
    if a.verbose: print(m["wrong"])
    if a.write:
        f = Path(slm.HERE / "thresholds.json"); cur = json.loads(f.read_text()) if f.exists() else {}
        cur[a.backend] = {"T": T, "M": M, "calibrated": True, "note": f"grid on {len(C)} developer-authored cases"}; f.write_text(json.dumps(cur, indent=1)); print("wrote", f)
