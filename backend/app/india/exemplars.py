"""Labelled example sentences for the small-model layer (slm.py): (slot, value, text).
Written by the developer, not by an advocate. Hindi and Tamil lines need a native reader.
"_none" is the background class: ordinary sentences that must NOT trigger any fact.
Add examples here to teach the model a new phrasing; no retraining is involved."""

B = []
def add(slot, value, *texts): B.extend((slot, value, t) for t in texts)

add("domestic_violence", True,
    "he beats me regularly", "my husband hits me when he is angry", "I am physically abused at home", "he threatens to kill me",
    "there is violence in the house", "he locked me in a room and hurt me",
    "वह मुझे रोज़ मारता है", "घर में मारपीट होती है", "पति मुझे पीटते हैं", "मुझे धमकाया गया और मारा गया",
    "கணவர் என்னை அடிக்கிறார்", "வீட்டில் வன்முறை நடக்கிறது", "என்னை உடல்ரீதியாகத் துன்புறுத்துகிறார்",
    "mujhe roz maarta hai", "ghar mein maarpeet hoti hai", "wo mujhe peetta hai", "en kanavar ennai adikkiraar")

add("ground", "cruelty",
    "he and his family harass me for dowry", "constant mental torture and humiliation", "he insults me and treats me cruelly",
    "his parents torture me every day", "he humiliates me in front of everyone",
    "दहेज के लिए ससुराल वाले परेशान करते हैं", "मानसिक प्रताड़ना होती है", "वह मेरा अपमान करता है",
    "வரதட்சணைக்காக மாமியார் வீட்டார் துன்புறுத்துகிறார்கள்", "மனரீதியாக கொடுமைப்படுத்துகிறார்",
    "dahej ke liye pareshan karte hain", "varadhatchanaikaga kodumai paduthuranga")
add("ground", "desertion",
    "he left home and never came back", "she has been living away from me without any reason", "he walked out on the family",
    "she went to her parents house and refuses to return", "he abandoned me and the children",
    "वह घर छोड़कर चला गया और वापस नहीं आया", "पत्नी मायके चली गई और लौटने से मना करती है", "उसने मुझे और बच्चों को छोड़ दिया",
    "கணவர் வீட்டை விட்டுச் சென்றுவிட்டார், திரும்பி வரவில்லை", "மனைவி தாய் வீட்டுக்குச் சென்று திரும்ப மறுக்கிறார்",
    "wo ghar chhod kar chala gaya", "biwi maike chali gayi aur lautne se mana karti hai")
add("ground", "adultery",
    "my husband is having an affair with another woman", "she is seeing another man", "he is in a relationship with someone else",
    "I found out about his extramarital relationship",
    "पति का किसी दूसरी औरत से संबंध है", "पत्नी का किसी और से अवैध संबंध है",
    "கணவருக்கு வேறொரு பெண்ணுடன் தொடர்பு உள்ளது", "மனைவிக்கு வேறொருவருடன் கள்ள உறவு உள்ளது",
    "uska kisi aur aurat se chakkar hai")

add("mutual_consent", True,
    "we both want to separate peacefully", "we have decided together to end the marriage", "he is ready to sign the divorce papers",
    "both of us are okay with the divorce",
    "हम दोनों शांति से अलग होना चाहते हैं", "हम दोनों ने मिलकर तलाक का फैसला किया है",
    "நாங்கள் இருவரும் சேர்ந்து விவாகரத்து செய்ய முடிவு செய்தோம்", "hum dono milkar alag hona chahte hain")
add("mutual_consent", False,
    "he wants to fight the divorce in court", "she is not ready to give me a divorce", "he is contesting the case",
    "my spouse opposes the divorce", "she wants to stay married and will oppose it",
    "वह तलाक का विरोध कर रहा है", "पत्नी तलाक देने को तैयार नहीं है", "அவர் விவாகரத்தை எதிர்க்கிறார்", "wo talaq ka virodh kar raha hai")

add("respondent_abroad", True,
    "my husband works in Dubai", "he lives in the US and does not come to India", "she moved to Canada after marriage",
    "he is an NRI settled abroad",
    "पति दुबई में नौकरी करते हैं", "वह विदेश में रहता है", "वह अमेरिका में बस गया है",
    "கணவர் துபாயில் வேலை செய்கிறார்", "அவர் வெளிநாட்டில் வசிக்கிறார்", "pati videsh mein rehte hain")

add("claimant_can_self_maintain", True,
    "I earn a good salary and support myself", "I have my own business and income", "मैं खुद कमाती हूँ", "நான் சொந்தமாக சம்பாதிக்கிறேன்")
add("claimant_can_self_maintain", False,
    "I have no income and cannot support myself", "I am a housewife with no job or savings", "I depend on my parents for food and rent",
    "मेरी कोई आमदनी नहीं है, मैं घर संभालती हूँ", "எனக்கு வருமானம் இல்லை, நான் இல்லத்தரசி")
add("respondent_has_means", True,
    "he has a good job and earns well", "he owns a business and property", "his salary is high",
    "उसकी अच्छी नौकरी है और अच्छी कमाई है", "उसका अपना कारोबार है", "அவருக்கு நல்ல வேலை, நல்ல சம்பளம்")
add("respondent_has_means", False,
    "he is unemployed and has no income", "he has no job or property", "वह बेरोज़गार है, कोई आमदनी नहीं", "அவர் வேலையில்லாமல் இருக்கிறார்")

add("divorce_status", "decreed",
    "the court has already granted our divorce", "we got divorced last year", "I am a divorced woman", "the divorce decree was passed in 2023",
    "तलाक की डिक्री हो चुकी है", "हमारा तलाक हो चुका है", "எங்களுக்கு விவாகரத்து ஆகிவிட்டது")
add("divorce_status", "pending",
    "my divorce case is going on in the family court", "he filed a divorce petition against me", "the hearing is next month",
    "our case is pending in court",
    "तलाक का केस फैमिली कोर्ट में चल रहा है", "पति ने मुझ पर तलाक का मुकदमा दायर किया है",
    "குடும்ப நீதிமன்றத்தில் விவாகரத்து வழக்கு நடந்து வருகிறது")
add("divorce_status", "none",
    "we are still married and no case is filed yet", "nothing has been filed in court so far", "अभी तक कोई मुकदमा दायर नहीं हुआ", "இன்னும் வழக்கு தாக்கல் செய்யவில்லை")

add("needs", "divorce",
    "I want to end my marriage legally", "I want to be free from this marriage", "मैं इस शादी को खत्म करना चाहती हूँ",
    "நான் இந்த திருமணத்தை முடித்துக்கொள்ள விரும்புகிறேன்", "mujhe is shaadi se azaadi chahiye")
add("needs", "maintenance",
    "I need money every month for my expenses and my child's school fees", "he does not pay anything for the household and children",
    "I want financial support from him", "मुझे और बच्चों के खर्च के लिए हर महीने पैसे चाहिए", "पति घर का खर्च नहीं देता",
    "எனக்கும் குழந்தைக்கும் மாதந்தோறும் செலவுக்குப் பணம் வேண்டும்", "mujhe har mahine kharcha chahiye")
add("needs", "protection",
    "I need a protection order from the court", "I want to be safe from my husband", "मुझे सुरक्षा चाहिए, मैं डरी हुई हूँ", "எனக்குப் பாதுகாப்பு வேண்டும்")

add("claimant", "wife",
    "my in-laws trouble me every day and I am the daughter-in-law", "पति से मेरी बिल्कुल नहीं बनती", "கணவருடன் எனக்குப் பிரச்சினை")
add("claimant", "husband",
    "I am a married man and my wife and I fight every day", "पत्नी से मेरी रोज़ लड़ाई होती है", "மனைவியுடன் எனக்கு தினமும் சண்டை")
add("claimant", "parent",
    "my son does not look after me in my old age", "I am an elderly father and my children neglect me",
    "बुढ़ापे में मेरा बेटा मेरी देखभाल नहीं करता", "முதுமையில் என் மகன் என்னைக் கவனிப்பதில்லை")
add("claimant", "child",
    "my father is not paying for my school fees and food", "मेरे पिता मेरी पढ़ाई का खर्च नहीं देते", "என் தந்தை என் படிப்புச் செலவைத் தருவதில்லை")

add("law", "hindu", "we are Hindus and our wedding was held with temple rituals", "हमारी शादी हिंदू रीति से हुई", "எங்கள் திருமணம் இந்து முறைப்படி நடந்தது")
add("law", "muslim", "our marriage was a nikah under Islamic law", "हमारा निकाह इस्लामी कानून से हुआ", "எங்கள் திருமணம் இஸ்லாமிய முறைப்படி நடந்தது")
add("law", "christian", "we were married in a church", "हमारी शादी चर्च में हुई", "எங்கள் திருமணம் தேவாலயத்தில் நடந்தது")
add("law", "parsi", "we are Zoroastrians and married in an agiary", "hum Zoroastrian hain")
add("law", "special_marriage", "we registered our marriage at the registrar's office under the special act", "हमारी शादी रजिस्ट्रार के दफ्तर में पंजीकृत हुई")

add("_none", None,
    "hello", "hi, I need some help", "please help me", "I don't know what to do", "I live in Chennai", "we have two children",
    "I am worried about my future", "what are my options", "how long will it take", "we got married in 2015", "my name is Priya",
    "can you explain the process", "I am very tired and confused", "thank you",
    "नमस्ते, मुझे मदद चाहिए", "मुझे नहीं पता क्या करूँ", "हमारे दो बच्चे हैं", "हम दिल्ली में रहते हैं", "धन्यवाद",
    "வணக்கம், எனக்கு உதவி வேண்டும்", "எங்களுக்கு இரண்டு குழந்தைகள்", "நான் சென்னையில் வசிக்கிறேன்", "நன்றி",
    "namaste mujhe madad chahiye", "mujhe samajh nahi aa raha kya karun", "enakku udhavi venum")
