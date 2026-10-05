"""FROZEN COPY of the v1 lexicon intake, kept only as an evaluation baseline (research/intake_eval.py).
Keyword lexicon, deliberately transparent. Replace with a legal NER model later (see README)."""
import re

LEX = {
 "law": {
  "special_marriage": ["special marriage", "स्पेशल मैरिज", "विशेष विवाह", "சிறப்பு திருமண"],
  "muslim": ["muslim", "मुस्लिम", "मुसलमान", "முஸ்லிம்", "இஸ்லா"],
  "christian": ["christian", "ईसाई", "क्रिश्चियन", "கிறிஸ்தவ", "கிறித்தவ"],
  "parsi": ["parsi", "पारसी", "பார்சி"],
  "hindu": ["hindu", "हिंदू", "हिन्दू", "இந்து", "sikh", "सिख", "jain", "जैन", "buddhist", "बौद्ध"],
 },
 "needs": {
  "divorce": [r"\bdivorce\b", "तलाक", "विवाह विच्छेद", "விவாகரத்து", "talaq", "तलाक़"],
  "maintenance": ["maintenance", "alimony", "monthly money", "monthly support", "support money", "गुजारा", "गुज़ारा", "भरण", "खर्च", "பராமரிப்பு", "ஜீவனாம்சம்", "ஜீவனாம்ச", "செலவுத்தொகை"],
  "protection": ["violence", "beat", "beaten", "abuse", "मारपीट", "हिंसा", "मारता", "வன்முறை", "அடி", "துன்புறுத்"],
 },
 "ground": {
  "cruelty": ["cruelty", "cruel", "क्रूरता", "प्रताड़ित", "கொடுமை"],
  "desertion": ["deserted", "desertion", "abandon", "छोड़", "परित्याग", "கைவிட்ட", "விட்டுச்"],
  "adultery": ["adultery", "affair", "व्यभिचार", "अवैध संबंध", "கள்ள உறவு", "கள்ளத்தொடர்பு"],
 },
 "mutual": ["mutual", "आपसी सहमति", "आपसी", "परस्पर", "பரஸ்பர", "இருவரும் சம்மத"],
 "abroad": ["abroad", "dubai", "overseas", "विदेश", "வெளிநாடு"],
 "dv": ["violence", "beat", "beaten", "मारपीट", "हिंसा", "வன்முறை", "அடி"],
}
WIFE_SPEAKER = ["my husband", "i am the wife", "i'm his wife", "मेरा पति", "मेरे पति", "मेरे पति ने", "मैं पत्नी", "என் கணவர்", "என் கணவ", "நான் மனைவி"]
HUSBAND_SPEAKER = ["my wife", "i am the husband", "मेरी पत्नी", "मेरी बीवी", "मैं पति", "என் மனைவி", "நான் கணவர்"]
PARENT_SPEAKER = ["my son", "my daughter", "मेरा बेटा", "मेरी बेटी", "என் மகன்", "என் மகள்"]
SEP = re.compile(r"(\d+(?:\.\d+)?)\s*(year|yr|साल|वर्ष|ஆண்டு|month|महीन|மாத)", re.I)


def _lang(t):
    dev = sum("\u0900" <= c <= "\u097f" for c in t); ta = sum("\u0b80" <= c <= "\u0bff" for c in t)
    return "hi" if dev > max(ta, 3) else "ta" if ta > 3 else "en"


def _has(t, words):
    return [w for w in words if (re.search(w, t) if w.startswith("\\b") else w in t)]


def extract(text: str) -> dict:
    t = text.lower(); matched, facts = {}, {}
    for law, ws in LEX["law"].items():
        h = _has(t, ws)
        if h: facts["law"] = law; matched["law"] = h; break
    done = re.search(r"\bdivorced\b|तलाकशुदा|तलाक़शुदा", t)
    if done: t = re.sub(r"\bdivorced\b|तलाकशुदा|तलाक़शुदा", " ", t); facts["divorce_pending_or_decreed"] = True
    needs = [n for n, ws in LEX["needs"].items() if _has(t, ws)]
    if needs: facts["needs"] = needs; matched["needs"] = needs
    for g, ws in LEX["ground"].items():
        if _has(t, ws): facts["ground"] = g; matched["ground"] = g; break
    if _has(t, LEX["mutual"]): facts["mutual_consent"] = True
    if _has(t, LEX["abroad"]): facts["respondent_abroad"] = True
    if _has(t, LEX["dv"]): facts["domestic_violence"] = True
    if _has(t, WIFE_SPEAKER): facts["claimant"] = "wife"; matched["claimant"] = "speaker is wife"
    elif _has(t, HUSBAND_SPEAKER): facts["claimant"] = "husband"; matched["claimant"] = "speaker is husband"
    elif _has(t, PARENT_SPEAKER): facts["claimant"] = "parent"; matched["claimant"] = "speaker is parent"
    m = SEP.search(t)
    if m and any(k in t for k in ["separat", "alag", "अलग", "பிரிந்"]):
        n = float(m.group(1)); facts["separated_months"] = n * 12 if m.group(2).lower() in ("year", "yr", "साल", "वर्ष", "ஆண்டு") else n
    missing = [k for k in ("law", "needs") if k not in facts]
    return {"language": _lang(text), "facts": facts, "matched": matched, "missing": missing,
            "note": "Keyword intake. Confirm every field in the form; places are never auto-filled."}
