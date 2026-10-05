"""Optional small-language-model layer. A multilingual sentence ENCODER (not a generative LLM) proposes TENTATIVE facts.

Why an encoder: Render's free instance has 512 MB RAM and a fraction of a CPU. A ~120M-parameter int8 encoder fits and
answers in well under a second. A generative model, even 0.5B parameters, does not.

How it is kept safe:
  * It can only suggest. The agent never locks a suggestion in; the person is still asked, with the suggestion pre-selected.
  * It abstains: a match needs a minimum similarity AND a margin over the runner-up value AND over the background class.
  * It never decides polarity on a negated clause ("he never beat me" produces no suggestion).
  * The lexicon in intake.py wins whenever it found the fact.

Backends (env SLM = auto | onnx | hash | off, default auto):
  onnx  multilingual-e5-small, int8, via onnxruntime + tokenizers. Files in SLM_DIR (the Dockerfile fetches them).
  hash  character n-gram hashing. No download. Handles romanised spelling variants; has little real semantics.
  off   lexicon only.
auto = onnx if its files load and pass a self-test (including a similarity sanity check), otherwise hash.
"""
from __future__ import annotations
import hashlib, json, os, re, sys, threading, zlib
from pathlib import Path

from .exemplars import B as EXEMPLARS
from .intake import SPLIT, NEG_BEFORE, NEG_AFTER, NEG_NEED

HERE = Path(__file__).resolve().parent
SLM_DIR = Path(os.environ.get("SLM_DIR", HERE.parents[1] / "models" / "multilingual-e5-small"))
DEFAULT_TH = {"onnx": {"T": 0.86, "M": 0.025, "calibrated": False}, "hash": {"T": 0.55, "M": 0.06, "calibrated": False}}
POLAR = {"domestic_violence", "respondent_abroad"}                                   # skipped on negated clauses
MULTI = {"needs"}                                                                    # several values can hold at once

STATE = {"backend": "lexicon", "ready": False, "error": None, "model": None, "loading": False}
_lock = threading.Lock()


def status() -> dict:
    return {"backend": STATE["backend"], "ready": STATE["ready"], "loading": STATE["loading"], "error": STATE["error"], "model": STATE["model"]}


def rss_mb():
    try:
        import resource
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return round(r / (1024 * 1024 if sys.platform == "darwin" else 1024), 1)    # peak, not current
    except Exception:
        return None


def thresholds(backend: str) -> dict:
    th = dict(DEFAULT_TH[backend])
    f = HERE / "thresholds.json"
    if f.exists():
        try: th.update(json.loads(f.read_text()).get(backend, {}))
        except Exception: pass
    return th


# ---------------------------------------------------------------- encoders
class HashEmbedder:
    name, dim = "hash", 4096

    def embed(self, texts):
        import numpy as np
        X = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            t = re.sub(r"[^\w\s]", " ", t.lower()); grams = []
            for w in t.split():
                w = f" {w} "; grams += [w[j:j + n] for n in (3, 4) for j in range(len(w) - n + 1)]
                grams.append("w:" + w)
            for g in grams: X[i, zlib.crc32(g.encode()) % self.dim] += 1.0
            X[i] = np.sqrt(X[i])
        n = np.linalg.norm(X, axis=1, keepdims=True); n[n == 0] = 1
        return X / n


class OnnxEmbedder:
    name = "onnx"

    def __init__(self, d: Path):
        import numpy as np, onnxruntime as ort
        from tokenizers import Tokenizer
        model = next((d / n for n in ("model_quantized.onnx", "model_int8.onnx", "model.onnx") if (d / n).exists()), None)
        if model is None or not (d / "tokenizer.json").exists(): raise FileNotFoundError(f"model files not found in {d}")
        self.tok = Tokenizer.from_file(str(d / "tokenizer.json")); self.tok.enable_truncation(96); self.tok.enable_padding()
        so = ort.SessionOptions(); so.intra_op_num_threads = 1; so.inter_op_num_threads = 1; so.enable_cpu_mem_arena = False
        self.sess = ort.InferenceSession(str(model), so, providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.sess.get_inputs()}
        self.prefix = os.environ.get("SLM_PREFIX", "query: ")                         # e5 models expect a prefix
        self.model_file = model.name
        self.dim = int(self.embed(["test"]).shape[1])

    def embed(self, texts):
        import numpy as np
        enc = self.tok.encode_batch([self.prefix + t for t in texts])
        ids = np.array([e.ids for e in enc], dtype=np.int64); mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
        feed = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in self.inputs: feed["token_type_ids"] = np.zeros_like(ids)
        h = self.sess.run(None, feed)[0]
        v = (h * mask[..., None]).sum(1) / np.maximum(mask.sum(1, keepdims=True), 1)
        n = np.linalg.norm(v, axis=1, keepdims=True); n[n == 0] = 1
        return (v / n).astype(np.float32)


def _sane(emb) -> bool:
    """Catches a wrong model, wrong pooling or a broken export before it can influence anyone's case."""
    import numpy as np
    E = emb.embed(["he beats me", "he hits me", "I live in Chennai", "मैं चेन्नई में रहता हूँ"])
    ok = np.isfinite(E).all() and np.allclose(np.linalg.norm(E, axis=1), 1, atol=1e-3)
    return bool(ok and float(E[0] @ E[1]) > float(E[0] @ E[2]) + 0.02)


# ---------------------------------------------------------------- exemplar index
class Index:
    def __init__(self, emb):
        import numpy as np
        self.emb, self.rows = emb, EXEMPLARS
        self.X = self._matrix()
        self.slots = np.array([r[0] for r in self.rows]); self.vals = [r[1] for r in self.rows]
        self.th = thresholds(emb.name)

    def _matrix(self):
        import numpy as np
        key = hashlib.sha1((self.emb.name + getattr(self.emb, "model_file", "") + json.dumps(self.rows, ensure_ascii=False, default=str)).encode()).hexdigest()[:12]
        f = SLM_DIR / f"exemplars-{self.emb.name}-{key}.npy"
        if f.exists():
            try: return np.load(f)
            except Exception: pass
        X = self.emb.embed([r[2] for r in self.rows])
        try: SLM_DIR.mkdir(parents=True, exist_ok=True); np.save(f, X)
        except Exception: pass
        return X

    def suggest(self, text: str) -> dict:
        """{slot: {"value", "why", "source", "score"}} for the clauses of text. Abstains rather than guesses."""
        import numpy as np
        clauses = [c.strip() for c in SPLIT.split(" ".join(text.lower().split())) if c and len(c.strip()) > 3]
        if not clauses: return {}
        S = self.emb.embed(clauses) @ self.X.T
        T, M = self.th["T"], self.th["M"]
        best: dict = {}
        bg_cols = np.where(self.slots == "_none")[0]
        for ci, c in enumerate(clauses):
            row = S[ci]; bg = float(row[bg_cols].max()) if len(bg_cols) else 0.0
            negated = bool(NEG_BEFORE.search(c) or NEG_AFTER.search(c))
            for slot in sorted(set(self.slots) - {"_none"}):
                cols = np.where(self.slots == slot)[0]
                per = {}
                for k in cols: per[self.vals[k]] = max(per.get(self.vals[k], -1), float(row[k]))
                if slot in POLAR and negated: continue
                if slot in MULTI:
                    if NEG_NEED.search(c): continue
                    for v, s in per.items():
                        if s >= T and s - bg >= M: _keep(best, slot, v, s, c, multi=True)
                    continue
                ranked = sorted(per.items(), key=lambda kv: -kv[1]); (v1, s1) = ranked[0]
                s2 = ranked[1][1] if len(ranked) > 1 else -1
                if s1 >= T and s1 - max(s2, bg) >= M: _keep(best, slot, v1, s1, c)
        src = f"slm:{self.emb.name}"
        out = {}
        for slot, b in best.items():
            if slot in MULTI: out[slot] = {"value": sorted(b), "why": "reads like a request for " + ", ".join(sorted(b)), "source": src}
            else: out[slot] = {"value": b[0], "score": round(b[1], 3), "why": f"close in meaning to “{b[2][:60]}”", "source": src}
        return out


def _keep(best, slot, v, s, c, multi=False):
    if multi: best.setdefault(slot, set()).add(v)
    elif slot not in best or s > best[slot][1]: best[slot] = (v, s, c)


# ---------------------------------------------------------------- lifecycle
_INDEX: Index | None = None


def load(mode: str | None = None) -> dict:
    """Load the encoder. Safe to call from a thread; never raises."""
    global _INDEX
    mode = (mode or os.environ.get("SLM", "auto")).lower()
    with _lock:
        STATE.update(loading=True, error=None)
        if mode == "off":
            STATE.update(backend="lexicon", ready=False, loading=False); return status()
        errors, emb = [], None
        try: import numpy  # noqa: F401
        except Exception as e: STATE.update(backend="lexicon", ready=False, loading=False, error=f"numpy missing: {e}"); return status()
        if mode in ("auto", "onnx"):
            try:
                cand = OnnxEmbedder(SLM_DIR)
                if _sane(cand): emb = cand
                else: errors.append("onnx model failed the sanity check")
            except Exception as e: errors.append(f"onnx: {type(e).__name__}: {e}")
        if emb is None and mode in ("auto", "hash"):
            emb = HashEmbedder()
        if emb is None:
            STATE.update(backend="lexicon", ready=False, loading=False, error="; ".join(errors)); return status()
        try:
            _INDEX = Index(emb)
            rss, cap = rss_mb(), float(os.environ.get("SLM_MAX_RSS_MB", "430"))        # Render free = 512 MB hard limit
            if emb.name == "onnx" and rss and rss > cap and mode == "auto":
                errors.append(f"onnx used {rss} MB (cap {cap}); fell back to hash"); emb = HashEmbedder(); _INDEX = Index(emb)
        except Exception as e:
            STATE.update(backend="lexicon", ready=False, loading=False, error=f"index: {e}"); return status()
        STATE.update(backend=f"lexicon+slm:{emb.name}", ready=True, loading=False, model=getattr(emb, "model_file", None),
                     error="; ".join(errors) or None)
        return status()


def start():
    """Load in the background so the web server can bind its port immediately."""
    threading.Thread(target=load, daemon=True, name="slm-load").start()


def augment(text: str, r: dict) -> dict:
    """Add tentative suggestions from the encoder (and, only if enabled and nothing else was found, Groq) to an intake result.
    Never overrides a fact or a lexicon hint."""
    sug = {}
    if STATE["ready"] and _INDEX:
        try: sug = _INDEX.suggest(text)
        except Exception as e: STATE["error"] = f"suggest: {type(e).__name__}: {e}"
    if not sug and not r["facts"] and not r["tentative"] and not r["conflicts"]:
        from . import groq_assist
        sug = groq_assist.suggest(text)
        if sug: r["engine"] = "groq"
    if not sug: return r
    for slot, s in sug.items():
        if slot in r["facts"] and slot != "needs": continue
        if slot in r["conflicts"] or slot in r["tentative"]: continue
        if slot == "needs":
            new = [n for n in s["value"] if n not in r["facts"].get("needs", []) and n not in r.get("not_needs", [])]
            if not new: continue
            s = {**s, "value": new}
        r["tentative"][slot] = s
    r["engine"] = r["engine"] if r.get("engine") == "groq" else STATE["backend"]
    return r


if __name__ == "__main__":     # python -m app.india.slm --build   (used by the Dockerfile to precompute the exemplar index)
    if "--build" in sys.argv:
        st = load(); print(json.dumps(st, ensure_ascii=False)); sys.exit(0 if st["ready"] else 1)
