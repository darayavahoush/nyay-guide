"""India family-law intake: free text -> facts. English, Hindi, Tamil, and common romanised Hinglish/Tanglish.

Layer 1 (this file) is a transparent lexicon with word boundaries, negation and conflict handling. It returns
  facts       confident facts the person stated. The agent locks these in.
  tentative   weaker hints (e.g. the word "nikah" suggests Muslim law). The agent only *suggests* them.
  conflicts   things stated two ways ("Hindu ... married a Christian"). Never guessed; the agent asks.
Layer 2 (slm.py, optional small multilingual encoder) adds more tentative hints. It can never add a confident fact.
Stdlib only.
"""
import re

R = lambda *alts: re.compile("|".join(alts))

LAW = {
    "special_marriage": R(r"\bspecial marriage", r"\bsma\b", "स्पेशल मैरिज", "विशेष विवाह", "சிறப்பு திருமண"),
    "muslim": R(r"\bmuslim", r"\bmusalman", r"\bislam", r"\bsharia", "मुस्लिम", "मुसलमान", "इस्लाम", "முஸ்லிம்", "இஸ்லா"),
    "christian": R(r"\bchristian", "ईसाई", "क्रिश्चियन", "கிறிஸ்தவ", "கிறித்தவ"),
    "parsi": R(r"\bparsi", r"\bzoroastrian", "पारसी", "பார்சி"),
    "hindu": R(r"\bhindu", r"\bsikh", r"\bjains?\b", r"\bjainism", r"\bbuddhist", "हिंदू", "हिन्दू", "सिख", "जैन", "बौद्ध", "இந்து"),
}
LAW_HINT = {  # weak cultural cues: suggested, never locked in
    "muslim": R(r"\bnikah", r"\bmahr\b|\bmehr\b|\bmeher\b", r"\biddat", r"\bkhula\b", "निकाह", "मेहर"),
    "hindu": R(r"\bmangalsutra", r"\bsaptapadi", r"\bpheras?\b", "मंगलसूत्र", "सात फेरे"),
    "christian": R(r"\bchurch\b", r"\bpastor\b", r"\bbaptis", "चर्च", "தேவாலய"),
    "special_marriage": R(r"\bcourt marriage", r"\bregistered marriage", r"\binter-?faith", r"\binter-?caste", "कोर्ट मैरिज"),
}
VIOLENCE = R(r"\bviolen", r"\bbeat(?:s|ing|en)?\b", r"\bhit(?:s|ting)? (?:me|her|him)\b", r"\bslap", r"\bassault",
             r"\bmaarpeet|\bmarpeet|\bmaar(?:ta|ti|te)\b|\bmarta hai\b|\bpeet(?:ta|ti)\b", "मारपीट", "हिंसा", "मारता", "मारती", "मारते", "पीटता", "पीटती", "पीटते",
             "வன்முறை", "அடிக்(?!கடி)", "அடித்", "அடிப்பார்", "அடிப்பதா")
NEED = {
    "divorce": R(r"\bdivorc(?:e|ing)\b", r"\btalaa?[qk]\b", "तलाक", "विवाह विच्छेद", "விவாகரத்து"),
    "maintenance": R(r"\bmaintenance\b", r"\balimony\b", r"\bmonthly (?:money|support|allowance|amount)", r"\bfinancial support",
                     r"\bsupport money", r"\bgujaa?ra\b", r"\bbharan", "गुजारा", "गुज़ारा", "भरण", "खर्च",
                     "பராமரிப்பு", "ஜீவனாம்ச", "செலவுத்தொகை"),
}
GROUND = {
    "cruelty": R(r"\bcruel", r"\btortur", r"\bharass", r"\bdowry", "क्रूरता", "प्रताड़", "दहेज", "கொடுமை", "வரதட்சணை"),
    "desertion": R(r"\bdesert", r"\babandon", r"\bleft me\b", r"\bleft (?:the )?(?:house|home)\b", r"\bwalked out\b", r"\bchhod",
                   "छोड़", "परित्याग", "கைவிட்ட", "விட்டுச்", "விட்டுப்"),
    "adultery": R(r"\badulter", r"\bextra-?marital", r"\b(?:has|had|having|in) an? affair\b", r"\baffair with\b",
                  "व्यभिचार", "अवैध संबंध", "கள்ள உறவு", "கள்ளத்தொடர்பு"),
}
MUTUAL_YES = R(r"\bmutual(?:ly)? (?:consent|divorce|agree|separation|understanding)", r"\bboth (?:of us )?(?:agree|want|are willing|consent)",
               r"\bwe (?:both )?(?:agree|have agreed)", "आपसी सहमति", "आपसी तलाक", "परस्पर", "பரஸ்பர", "இருவரும் சம்மத")
MUTUAL_NO = R(r"\b(?:does|do|did|will|would)(?: not|n'?t) (?:agree|consent)", r"\bwon'?t (?:agree|give)", r"\brefus\w+ (?:to )?(?:give |agree|consent|divorce)",
              r"\bnot (?:ready|willing) (?:to|for)", "सहमत नहीं", "तैयार नहीं", "சம்மதிக்க மாட்ட", "ஒப்புக்கொள்ள மாட்ட")
ABROAD = R(r"\babroad\b", r"\boverseas\b", r"\bdubai\b", r"\bgulf\b", r"\bnri\b", r"\boutside india\b", r"\b(?:usa|canada|singapore|saudi|qatar|kuwait|australia|germany)\b",
           "विदेश", "खाड़ी", "வெளிநாடு")
DECREED = R(r"\bdivorced\b", r"\bdecree (?:was |has been )?(?:passed|granted|issued)", "तलाकशुदा", "तलाक़शुदा", "तलाक हो चुका", "விவாகரத்து பெற்ற")
PENDING = R(r"\b(?:case|petition|suit|matter)\b[^.,;]{0,25}\b(?:pending|filed|going on|ongoing|in court)", r"\bfiled (?:a |the |for )?(?:divorce|case|petition|suit)",
            "मामला चल रहा", "मामला दायर", "केस चल रहा", "केस दायर", "வழக்கு நடந்து", "வழக்கு தாக்கல்", "வழக்கு நிலுவை")
WIFE = R(r"\bmy (?:husband|hubby)\b", r"\bi(?: am|'m) (?:the |his )?wife\b", r"\bmera pati\b|\bmere pati\b", "मेरा पति", "मेरे पति", "मैं पत्नी", "என் கணவர்", "என் கணவ", "நான் மனைவி")
HUSBAND = R(r"\bmy wife\b", r"\bi(?: am|'m) (?:the |her )?husband\b", r"\bmeri patni\b|\bmeri bi(?:w|v)i\b", "मेरी पत्नी", "मेरी बीवी", "मैं पति", "என் மனைவி", "நான் கணவர்")
PARENT = R(r"\bmy (?:son|daughter)\b", r"\bmera beta\b|\bmeri beti\b", "मेरा बेटा", "मेरी बेटी", "என் மகன்", "என் மகள்")
INLAWS = R(r"\bin-?laws?\b", r"\bsasural\b", "ससुराल", "மாமியார்")

SPLIT = re.compile(r"[.;!?\n]+|,| but | though | however | although | and yet | लेकिन | मगर | पर | ஆனால் ")
NEG_BEFORE = re.compile(r"\b(?:no|not|never|none|neither|nor|without|isn'?t|aren'?t|wasn'?t|weren'?t|don'?t|doesn'?t|didn'?t|won'?t|can'?t|cannot|hasn'?t|haven'?t|hadn'?t)\b")
NEG_AFTER = re.compile(r"नहीं|नही|(?<!\S)न(?!\S)|இல்லை|இல்ல|வில்லை|மாட்ட|\bnahi\b|\bnahin\b|\billai\b")
CANCEL = re.compile(r"\b(?:stop\w*|cease\w*|quit|refus\w*|fail\w*|only|just)\b")           # "does not stop beating" is not a denial
NEG_LAW = re.compile(r"(?:\bnot|\bnon|isn'?t|aren'?t|no longer)\s*-?\s*(?:a |an |the )?$")
NEG_LAW_AFTER = re.compile(r"^\s{0,2}(?:नहीं|नही|இல்லை|illai|nahi|nahin)")
NEG_NEED = re.compile(r"(?:don'?t|do not|doesn'?t|not|no longer|never)\s+(?:want|need|wish|seek|ask for|looking for|interested in)\b[^.,;]{0,20}$|\bno need (?:for|of)\b[^.,;]{0,10}$|\bwithout\b[^.,;]{0,6}$")
NEG_NEED_AFTER = re.compile(r"^[^.,;]{0,14}(?:नहीं चाहिए|नहीं चाहत|नही चाहिए|வேண்டாம்|nahi chahiye)")

NUMW = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
        "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
        "ஒரு": 1, "ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5}
YEAR = r"(?:years?|yrs?|साल|वर्ष|वर्षों|ஆண்டு|ஆண்டா|வருட|வருஷ|saal|varsh)"
MONTH = r"(?:months?|mths?|महीने|महीना|महीन|மாத|mahine|mahina)"
DUR = re.compile(r"(\d+(?:\.\d+)?|" + "|".join(sorted(NUMW, key=len, reverse=True)) + r")\s*-?\s*(" + YEAR + "|" + MONTH + ")")
K_MARRIAGE = R(r"\bmarri(?:ed|age)\b", r"\bwedding\b", "शादी", "विवाह", "திருமண")
K_SEP = R(r"\bseparat", r"\bapart\b", r"\bliving (?:away|separately)\b", r"\bleft\b", r"\bdeserted\b", r"\balag\b", "अलग", "छोड़", "பிரிந்", "விட்டு")


def _lang(t):
    dev = sum("\u0900" <= c <= "\u097f" for c in t); ta = sum("\u0b80" <= c <= "\u0bff" for c in t)
    return "hi" if dev > max(ta, 3) else "ta" if ta > 3 else "en"


def _neg(c, m, nb=28, na=24):
    """Is the match m in clause c denied? Negator shortly before it (English) or shortly after it (Hindi/Tamil/romanised)."""
    before = c[max(0, m.start() - nb):m.start()]
    nm = list(NEG_BEFORE.finditer(before))
    if nm and not CANCEL.search(before[nm[-1].end():]): return True
    return bool(NEG_AFTER.search(c[m.end():m.end() + na]))


def _need_neg(c, m):
    return bool(NEG_NEED.search(c[max(0, m.start() - 40):m.start()]) or NEG_NEED_AFTER.search(c[m.end():m.end() + 24]))


def _law_neg(c, m):
    return bool(NEG_LAW.search(c[max(0, m.start() - 14):m.start()]) or NEG_LAW_AFTER.search(c[m.end():m.end() + 16]))


def _months(num, unit):
    n = float(NUMW.get(num, num)); return n * 12 if re.fullmatch(YEAR, unit) else n


def extract(text: str) -> dict:
    t = " ".join(text.lower().split())
    clauses = [c.strip() for c in SPLIT.split(t) if c and c.strip()]
    facts, tentative, conflicts, matched = {}, {}, {}, {}
    laws, denied_laws, needs, not_needs, grounds, speakers = {}, set(), set(), set(), [], set()
    mutual = viol = abroad = dstat = None

    for c in clauses:
        for law, rx in LAW.items():
            for m in rx.finditer(c):
                (denied_laws.add(law) if _law_neg(c, m) else laws.setdefault(law, m.group(0)))
        for need, rx in NEED.items():
            for m in rx.finditer(c):
                (not_needs if _need_neg(c, m) else needs).add(need)
        for m in VIOLENCE.finditer(c):
            if _need_neg(c, m): continue
            if _neg(c, m): viol = viol if viol is True else False; not_needs.add("protection")
            else: viol = True
        for g, rx in GROUND.items():
            for m in rx.finditer(c):
                if not _neg(c, m): grounds.append((t.find(m.group(0)), g))
        if MUTUAL_NO.search(c): mutual = False
        elif MUTUAL_YES.search(c) and mutual is None:
            m = MUTUAL_YES.search(c); mutual = not _neg(c, m)
        for m in ABROAD.finditer(c):
            if _neg(c, m): abroad = abroad if abroad is True else False
            else: abroad = True
        m = DECREED.search(c)
        if m: dstat = ("none" if dstat is None else dstat) if _neg(c, m) else "decreed"
        if PENDING.search(c) and dstat != "decreed": dstat = "pending"
        for nm, rx in (("wife", WIFE), ("husband", HUSBAND), ("parent", PARENT)):
            if rx.search(c): speakers.add(nm)

    # law: one stated -> confident; several -> conflict (Special Marriage Act wins if named, it is the statute of the marriage)
    live = {k: v for k, v in laws.items() if k not in denied_laws}
    if "special_marriage" in live: live = {"special_marriage": live["special_marriage"]}
    if len(live) == 1:
        (k, v), = live.items(); facts["law"] = k; matched["law"] = [v]
    elif len(live) > 1:
        conflicts["law"] = sorted(live); matched["law"] = list(live.values())
    else:
        hints = {k for k, rx in LAW_HINT.items() if rx.search(t) and k not in denied_laws}
        if len(hints) == 1:
            (k,) = hints; hit = LAW_HINT[k].search(t).group(0)
            tentative["law"] = {"value": k, "why": f"mentions '{hit}'", "source": "keyword-hint"}
    # claimant
    sp = speakers - {"parent"} if speakers - {"parent"} else speakers
    if len(sp) == 1:
        (k,) = sp; facts["claimant"] = k; matched["claimant"] = f"speaker is {k}"
    elif len(sp) > 1: conflicts["claimant"] = sorted(sp)
    elif INLAWS.search(t): tentative["claimant"] = {"value": "wife", "why": "mentions in-laws", "source": "keyword-hint"}
    # needs and facts
    if viol: needs.add("protection")
    needs -= not_needs
    if needs: facts["needs"] = sorted(needs); matched["needs"] = sorted(needs)
    if viol is not None: facts["domestic_violence"] = viol
    if grounds:
        grounds.sort(); facts["ground"] = grounds[0][1]; matched["ground"] = grounds[0][1]
        if len({g for _, g in grounds}) > 1: matched["other_grounds"] = sorted({g for _, g in grounds} - {grounds[0][1]})
    if mutual is not None: facts["mutual_consent"] = mutual
    if abroad is not None: facts["respondent_abroad"] = abroad
    if dstat: facts["divorce_status"] = dstat
    # durations: each number attaches to the nearest marriage / separation keyword in its clause
    for c in clauses:
        ks = [(m.start(), m.end(), "marriage") for m in K_MARRIAGE.finditer(c)] + [(m.start(), m.end(), "sep") for m in K_SEP.finditer(c)]
        if not ks: continue
        for d in DUR.finditer(c):
            gap = lambda k: max(k[0] - d.end(), d.start() - k[1], 0)
            near = min(ks, key=lambda k: (gap(k), k[2] != "sep"))
            mo = _months(d.group(1), d.group(2))
            if near[2] == "sep": facts["separated_months"] = mo
            else: facts["marriage_years"] = round(mo / 12, 2)
    missing = [k for k in ("law", "needs") if k not in facts]
    return {"language": _lang(text), "facts": facts, "tentative": tentative, "conflicts": conflicts, "not_needs": sorted(not_needs),
            "matched": matched, "missing": missing, "engine": "lexicon",
            "note": "Keyword intake. Confident facts are used; suggestions and conflicts are always put to the person. Places are never auto-filled."}
