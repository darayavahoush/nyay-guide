"""India-only family-law forum & remedy engine (maintenance + divorce).

Pure stdlib, deterministic, every output carries its statutory provision.
NOT legal advice. All provisions are flagged verified=False until an advocate signs off.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional

LAWS = ("hindu", "muslim", "christian", "parsi", "special_marriage")  # hindu = Hindu/Buddhist/Jain/Sikh

# ---- static catalogue: id -> metadata (also the corpus for the retrieval baseline) ----
CATALOGUE: dict[str, dict] = {
    "hma_13": dict(title="Contested divorce (Hindu Marriage Act)", law="hindu",
        provision="HMA 1955 s.13(1)/(2); venue s.19; one-year bar s.14", forum="Family Court / District Court",
        authorities=["Shilpa Sailesh v. Varun Sreenivasan (2023): Art.142 irretrievable breakdown (Supreme Court only)"]),
    "hma_13b": dict(title="Mutual-consent divorce (Hindu Marriage Act)", law="hindu",
        provision="HMA s.13B; venue s.19", forum="Family Court / District Court",
        authorities=["Amardeep Singh v. Harveen Kaur (2017): 6-month cooling-off is waivable"]),
    "sma_27": dict(title="Contested divorce (Special Marriage Act)", law="special_marriage",
        provision="SMA 1954 s.27; venue s.31; one-year bar s.29", forum="Family Court / District Court", authorities=[]),
    "sma_28": dict(title="Mutual-consent divorce (Special Marriage Act)", law="special_marriage",
        provision="SMA s.28; venue s.31", forum="Family Court / District Court", authorities=[]),
    "ida_10": dict(title="Contested divorce (Indian Divorce Act, Christians)", law="christian",
        provision="Indian Divorce Act 1869 s.10", forum="District Court / Family Court", authorities=[]),
    "ida_10a": dict(title="Mutual-consent divorce (Indian Divorce Act, Christians)", law="christian",
        provision="Indian Divorce Act s.10A (2 years' separation)", forum="District Court / Family Court", authorities=[]),
    "parsi_32": dict(title="Contested divorce (Parsi Marriage and Divorce Act)", law="parsi",
        provision="PMDA 1936 s.32", forum="Parsi Matrimonial Court", authorities=[]),
    "parsi_32b": dict(title="Mutual-consent divorce (Parsi)", law="parsi",
        provision="PMDA s.32B", forum="Parsi Matrimonial Court", authorities=[]),
    "dmma_2": dict(title="Wife's judicial divorce (Muslim)", law="muslim",
        provision="Dissolution of Muslim Marriages Act 1939 s.2", forum="Family Court / Civil Court", authorities=[]),
    "muslim_khula_mubarat": dict(title="Divorce by mutual agreement (khula / mubarat)", law="muslim",
        provision="Muslim personal law; judicial recognition via Family Court", forum="Family Court (if disputed)", authorities=[]),
    "muslim_talaq": dict(title="Husband's talaq (validity and limits)", law="muslim",
        provision="Muslim personal law; talaq-e-biddat void and an offence under Muslim Women (Protection of Rights on Marriage) Act 2019",
        forum="No court needed to pronounce; validity tested in Family Court",
        authorities=["Shayara Bano v. Union of India (2017)"]),
    "crpc125": dict(title="Maintenance of wife / child / parent (all religions)", law="all",
        provision="CrPC s.125 = BNSS 2023 s.144; venue CrPC s.126 = BNSS s.145; Family Courts Act 1984 s.7(2)",
        forum="Family Court, else Magistrate First Class",
        authorities=["Rajnesh v. Neha (2020): disclosure affidavit, interim maintenance, set-off",
                     "Mohd. Abdul Samad v. State of Telangana (2024): s.125 available to Muslim women"]),
    "hma_24_25": dict(title="Interim and permanent alimony (Hindu Marriage Act)", law="hindu",
        provision="HMA s.24 (pendente lite), s.25 (permanent); either spouse", forum="Court hearing the main petition", authorities=[]),
    "sma_36_37": dict(title="Interim and permanent alimony (Special Marriage Act)", law="special_marriage",
        provision="SMA s.36, s.37", forum="Court hearing the main petition", authorities=[]),
    "ida_36_37": dict(title="Interim and permanent alimony (Indian Divorce Act)", law="christian",
        provision="Indian Divorce Act s.36, s.37", forum="Court hearing the main petition", authorities=[]),
    "parsi_39_40": dict(title="Interim and permanent alimony (Parsi)", law="parsi",
        provision="PMDA s.39, s.40", forum="Parsi Matrimonial Court", authorities=[]),
    "mwpra_1986": dict(title="Divorced Muslim woman's fair provision and maintenance", law="muslim",
        provision="Muslim Women (Protection of Rights on Divorce) Act 1986 s.3, s.4, option under s.5",
        forum="Family Court / Magistrate First Class",
        authorities=["Daniel Latifi v. Union of India (2001): provision covers her future, payable within iddat",
                     "Shah Bano (1985)"]),
    "hama_18": dict(title="Hindu wife's maintenance from husband", law="hindu",
        provision="Hindu Adoptions and Maintenance Act 1956 s.18", forum="Family Court / Civil Court", authorities=[]),
    "hama_20": dict(title="Hindu child's and aged parent's maintenance", law="hindu",
        provision="HAMA s.20", forum="Family Court / Civil Court", authorities=[]),
    "dv_act": dict(title="Protection and monetary relief for aggrieved woman", law="all",
        provision="Protection of Women from Domestic Violence Act 2005 s.12, s.19, s.20; venue s.27",
        forum="Magistrate (JMFC / MM)", authorities=[]),
    "senior_citizens": dict(title="Parent's maintenance from children/relatives", law="all",
        provision="Maintenance and Welfare of Parents and Senior Citizens Act 2007 s.4, s.5",
        forum="Maintenance Tribunal", authorities=[]),
}

RAJNESH_CHECKLIST = [
    "Affidavit of assets, liabilities, income and expenses (Rajnesh v. Neha format) filed by BOTH parties",
    "Disclose every other pending or decided maintenance proceeding (awards are set off)",
    "Ask for interim maintenance from the date of the application",
    "List dependants, their ages and needs (children, parents)",
]


@dataclass
class Facts:
    law: str
    claimant: str = "wife"                 # wife | husband | child | parent
    needs: list = field(default_factory=list)   # subset of: divorce, maintenance, protection
    mutual_consent: bool = False
    ground: Optional[str] = None           # contested-divorce ground, free label
    marriage_years: Optional[float] = None
    separated_months: Optional[float] = None
    marriage_place: Optional[str] = None
    last_cohabitation_place: Optional[str] = None
    petitioner_residence: Optional[str] = None
    respondent_residence: Optional[str] = None
    respondent_abroad: bool = False
    claimant_can_self_maintain: bool = False
    respondent_has_means: bool = True
    claimant_living_in_adultery: bool = False
    claimant_refuses_cohabitation_without_cause: bool = False
    separated_by_mutual_consent: bool = False
    domestic_violence: bool = False
    child_minor: bool = True
    child_disabled: bool = False
    divorce_pending_or_decreed: bool = False


def _venue(basis, place, note):
    return {"basis": basis, "place": place, "note": note}


def _marriage_venues(f: Facts, wife_note: str, abroad_note: str, sect: str):
    v = [_venue("marriage", f.marriage_place, f"{sect}: where marriage was solemnised"),
         _venue("respondent", f.respondent_residence, f"{sect}: where respondent resides at filing"),
         _venue("last_cohabitation", f.last_cohabitation_place, f"{sect}: where parties last resided together")]
    if f.claimant == "wife":
        v.append(_venue("petitioner", f.petitioner_residence, wife_note))
    elif f.respondent_abroad:
        v.append(_venue("petitioner", f.petitioner_residence, abroad_note))
    return v


def _mk(rid, venues, met=(), unmet=(), notes=()):
    m = CATALOGUE[rid]
    return {"id": rid, "title": m["title"], "provision": m["provision"], "forum": m["forum"],
            "venues": venues, "status": "conditional" if unmet else "eligible",
            "conditions_met": list(met), "conditions_open": list(unmet), "notes": list(notes),
            "authorities": m["authorities"], "verified": False}


def _divorce(f: Facts):
    out, un = [], []
    mc = f.mutual_consent
    sep = f.separated_months
    if f.law == "hindu":
        v = _marriage_venues(f, "s.19(iiia): wife's residence at filing", "s.19(iv): petitioner's residence, respondent outside India", "s.19")
        if mc:
            if sep is None or sep < 12: un.append("living separately for at least 1 year before the petition (s.13B(1))")
            out.append(_mk("hma_13b", v, unmet=un, notes=["6-month cooling-off may be waived by the court (Amardeep Singh)"]))
        else:
            if not f.ground: un.append("a s.13(1)/13(2) ground (cruelty, desertion, adultery, etc.)")
            if f.marriage_years is not None and f.marriage_years < 1: un.append("s.14: no petition within 1 year of marriage without leave for exceptional hardship")
            out.append(_mk("hma_13", v, unmet=un))
    elif f.law == "special_marriage":
        v = _marriage_venues(f, "s.31: wife's residence at filing", "s.31: petitioner's residence, respondent outside India", "s.31")
        if mc:
            if sep is None or sep < 12: un.append("living separately for at least 1 year (s.28)")
            out.append(_mk("sma_28", v, unmet=un))
        else:
            if not f.ground: un.append("a s.27 ground")
            if f.marriage_years is not None and f.marriage_years < 1: un.append("s.29: 1-year bar")
            out.append(_mk("sma_27", v, unmet=un))
    elif f.law == "christian":
        v = [_venue("respondent", f.respondent_residence, "Indian Divorce Act: where parties reside"),
             _venue("last_cohabitation", f.last_cohabitation_place, "Indian Divorce Act: where parties last resided together")]
        if mc:
            if sep is None or sep < 24: un.append("living separately for at least 2 years (s.10A)")
            out.append(_mk("ida_10a", v, unmet=un))
        else:
            if not f.ground: un.append("a s.10 ground")
            out.append(_mk("ida_10", v, unmet=un))
    elif f.law == "parsi":
        v = [_venue("parsi_court", None, "Parsi Matrimonial Court with local jurisdiction (Bombay, Calcutta, Madras or district court)")]
        if mc:
            if f.marriage_years is not None and f.marriage_years < 1: un.append("PMDA s.32B: not before 1 year of marriage")
            out.append(_mk("parsi_32b", v, unmet=un))
        else:
            if not f.ground: un.append("a s.32 ground")
            out.append(_mk("parsi_32", v, unmet=un))
    elif f.law == "muslim":
        if f.claimant == "husband":
            out.append(_mk("muslim_talaq", [], notes=["Instant triple talaq is void and criminal; other forms need prescribed procedure"]))
        elif mc:
            out.append(_mk("muslim_khula_mubarat", []))
        else:
            if not f.ground: un.append("a ground under DMMA s.2")
            v = [_venue("petitioner", f.petitioner_residence, "Family Court where wife resides (CPC s.20 / Family Courts Act)"),
                 _venue("respondent", f.respondent_residence, "where husband resides")]
            out.append(_mk("dmma_2", v, unmet=un))
    return out


def _s125(f: Facts):
    if f.claimant == "husband": return None
    un, met = [], []
    if not f.respondent_has_means: un.append("respondent must have sufficient means")
    else: met.append("respondent has sufficient means")
    if f.claimant == "wife":
        if f.claimant_can_self_maintain: un.append("wife must be unable to maintain herself")
        else: met.append("unable to maintain herself")
        if f.claimant_living_in_adultery: un.append("s.125(4): disqualified if living in adultery")
        if f.claimant_refuses_cohabitation_without_cause: un.append("s.125(4): disqualified if refusing to live with husband without sufficient reason")
        if f.separated_by_mutual_consent: un.append("s.125(4): disqualified if living separately by mutual consent")
    elif f.claimant == "child":
        if not (f.child_minor or f.child_disabled): un.append("adult child must have a physical/mental abnormality or injury")
    elif f.claimant == "parent":
        if f.claimant_can_self_maintain: un.append("parent must be unable to maintain themselves")
    v = [_venue("respondent", f.respondent_residence, "s.126 CrPC / s.145 BNSS: where respondent resides or is"),
         _venue("last_cohabitation", f.last_cohabitation_place, "s.126: where he last resided with his wife")]
    return _mk("crpc125", v, met, un, notes=["A divorced wife who has not remarried still counts as 'wife'"] if f.claimant == "wife" else [])


def advise(f: Facts) -> dict:
    if f.law not in LAWS: raise ValueError(f"law must be one of {LAWS}")
    out, warn = [], []
    needs = set(f.needs)
    if "divorce" in needs: out += _divorce(f)
    maint = []
    if "maintenance" in needs or f.claimant in ("child", "parent"):
        r = _s125(f)
        if r: maint.append(r)
        pending = f.divorce_pending_or_decreed or "divorce" in needs
        if f.claimant in ("wife", "husband"):
            alimony = {"hindu": "hma_24_25", "special_marriage": "sma_36_37", "christian": "ida_36_37", "parsi": "parsi_39_40"}.get(f.law)
            if alimony:
                un = [] if pending else ["a matrimonial petition must be pending or decided"]
                maint.append(_mk(alimony, [_venue("pending_court", None, "the court hearing/deciding the main petition")], unmet=un))
            if f.law == "hindu" and f.claimant == "wife":
                maint.append(_mk("hama_18", [_venue("respondent", f.respondent_residence, "CPC s.20: where defendant resides or cause arose")]))
            if f.law == "muslim" and f.claimant == "wife":
                un = [] if f.divorce_pending_or_decreed else ["she must be divorced"]
                maint.append(_mk("mwpra_1986", [_venue("petitioner", f.petitioner_residence, "Magistrate/Family Court of her residence")], unmet=un))
        if f.law == "hindu" and f.claimant in ("child", "parent"):
            maint.append(_mk("hama_20", [_venue("respondent", f.respondent_residence, "CPC s.20")]))
        if f.claimant == "parent":
            maint.append(_mk("senior_citizens", [_venue("petitioner", f.petitioner_residence, "Tribunal where senior citizen resides, or where child/relative resides")]))
    out += maint
    if f.claimant == "wife" and (f.domestic_violence or "protection" in needs):
        v = [_venue("petitioner", f.petitioner_residence, "s.27: where aggrieved person resides, even temporarily"),
             _venue("respondent", f.respondent_residence, "s.27: where respondent resides"),
             _venue("cause_of_action", None, "s.27: where the violence occurred")]
        out.append(_mk("dv_act", v, [] if f.domestic_violence else [], [] if f.domestic_violence else ["a domestic-violence allegation"]))
    if len(maint) > 1 or (maint and any(r["id"] == "dv_act" for r in out)):
        warn.append("Several maintenance routes overlap. You may file in parallel, but must disclose each and awards are set off (Rajnesh v. Neha).")
    if f.respondent_abroad:
        warn.append("Respondent abroad: venue uses the petitioner's residence; service and enforcement outside India are not modelled.")
    if f.law == "muslim" and f.claimant == "wife" and "maintenance" in needs:
        warn.append("A Muslim woman may use s.125 (Mohd. Abdul Samad, 2024) and/or the 1986 Act; the 1986 Act s.5 election matters.")
    return {"remedies": out, "warnings": warn,
            "disclosures": RAJNESH_CHECKLIST if maint else [],
            "disclaimer": "Decision support only, not legal advice. Provisions are unverified by an advocate."}
