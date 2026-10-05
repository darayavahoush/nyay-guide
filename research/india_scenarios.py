"""Benchmark scenarios. Gold = required remedy ids / required + forbidden venue bases.
AUTHORED BY THE DEVELOPER from statutes, NOT advocate-validated. Replace with advocate-labelled gold before publishing."""
S = []
def add(name, text, facts, req, key=None, vreq=(), vforb=()):
    S.append(dict(name=name, text=text, facts=facts, required=set(req), key=key, vreq=set(vreq), vforb=set(vforb)))

add("hindu_wife_contested", "Hindu wife left husband for cruelty, married in Chennai, he lives in Pune, she lives in Trichy, wants divorce and maintenance",
    dict(law="hindu", needs=["divorce", "maintenance"], ground="cruelty", marriage_place="Chennai", respondent_residence="Pune", petitioner_residence="Trichy"),
    ["hma_13", "crpc125", "hma_24_25", "hama_18"], "hma_13", ["marriage", "respondent", "petitioner"])
add("hindu_husband_contested", "Hindu husband wants divorce from wife on desertion, married in Jaipur, wife lives in Delhi",
    dict(law="hindu", claimant="husband", needs=["divorce"], ground="desertion", marriage_place="Jaipur", respondent_residence="Delhi", petitioner_residence="Jaipur"),
    ["hma_13"], "hma_13", ["marriage", "respondent"], ["petitioner"])
add("hindu_mutual", "Hindu couple agree to divorce by mutual consent, living apart eighteen months",
    dict(law="hindu", needs=["divorce"], mutual_consent=True, separated_months=18), ["hma_13b"], "hma_13b")
add("hindu_bar", "Hindu wife wants contested divorce for cruelty six months after marriage",
    dict(law="hindu", needs=["divorce"], ground="cruelty", marriage_years=0.5), ["hma_13"])
add("sma_wife", "Wife married under the Special Marriage Act wants contested divorce and maintenance",
    dict(law="special_marriage", needs=["divorce", "maintenance"], ground="adultery", petitioner_residence="Kolkata"),
    ["sma_27", "crpc125", "sma_36_37"], "sma_27", ["petitioner"])
add("sma_mutual", "Inter-faith couple married under Special Marriage Act, mutual divorce after two years apart",
    dict(law="special_marriage", needs=["divorce"], mutual_consent=True, separated_months=24), ["sma_28"])
add("christian_wife_maint", "Christian wife abandoned by husband, no income, needs monthly maintenance",
    dict(law="christian", needs=["maintenance"], respondent_residence="Kochi"), ["crpc125"], "crpc125", ["respondent"], ["petitioner"])
add("christian_mutual", "Christian couple separated three years want mutual divorce",
    dict(law="christian", needs=["divorce"], mutual_consent=True, separated_months=36), ["ida_10a"])
add("muslim_divorced_wife", "Divorced Muslim woman wants maintenance and her mahr, husband can pay",
    dict(law="muslim", needs=["maintenance"], divorce_pending_or_decreed=True), ["crpc125", "mwpra_1986"])
add("muslim_husband_talaq", "Muslim husband wants to divorce his wife by talaq",
    dict(law="muslim", claimant="husband", needs=["divorce"]), ["muslim_talaq"])
add("muslim_wife_divorce", "Muslim wife wants court to dissolve marriage for cruelty",
    dict(law="muslim", needs=["divorce"], ground="cruelty"), ["dmma_2"])
add("parsi_mutual", "Parsi couple married three years agree to separate by mutual consent",
    dict(law="parsi", needs=["divorce"], mutual_consent=True, marriage_years=3), ["parsi_32b"])
add("hindu_parent", "Elderly Hindu mother cannot support herself, son earns well and refuses",
    dict(law="hindu", claimant="parent", needs=["maintenance"], claimant_can_self_maintain=False), ["crpc125", "hama_20", "senior_citizens"])
add("muslim_parent", "Aged Muslim father neglected by son who is a doctor",
    dict(law="muslim", claimant="parent", needs=["maintenance"]), ["crpc125", "senior_citizens"])
add("hindu_child", "Hindu minor child needs maintenance, father refuses to pay",
    dict(law="hindu", claimant="child", needs=["maintenance"]), ["crpc125", "hama_20"])
add("christian_child_disabled", "Adult disabled Christian son, father stopped support",
    dict(law="christian", claimant="child", child_minor=False, child_disabled=True, needs=["maintenance"]), ["crpc125"])
add("dv_wife", "Hindu wife beaten by husband, ran to parents in Madurai, needs protection and monthly money",
    dict(law="hindu", needs=["maintenance", "protection"], domestic_violence=True, petitioner_residence="Madurai", respondent_residence="Salem"),
    ["dv_act", "crpc125", "hama_18"], "dv_act", ["petitioner", "respondent"])
add("wife_adultery", "Wife living with another man wants maintenance from husband",
    dict(law="hindu", needs=["maintenance"], claimant_living_in_adultery=True), ["crpc125"])
add("respondent_abroad", "Hindu wife whose husband works in Dubai wants divorce, she lives in Coimbatore",
    dict(law="hindu", needs=["divorce"], ground="desertion", respondent_abroad=True, petitioner_residence="Coimbatore"),
    ["hma_13"], "hma_13", ["petitioner"])
add("wife_self_supporting", "Wife earns well but wants maintenance anyway after separation by mutual consent",
    dict(law="christian", needs=["maintenance"], claimant_can_self_maintain=True, separated_by_mutual_consent=True), ["crpc125"])
