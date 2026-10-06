import { useState, useRef, useEffect } from "react";
import { T, X } from "./strings.js";
import { agent } from "./api.js";

const Scales = () => (<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 3v17M7 20h10M4 7h16M4 7l-2.5 6a3 3 0 0 0 5 0L4 7zM20 7l-2.5 6a3 3 0 0 0 5 0L20 7z"/></svg>);
const SLOT = {
  en: { law: "Personal law", claimant: "Claimant", ground: "Reason", mutual_consent: "Both agree to divorce", domestic_violence: "Violence at home", respondent_abroad: "Other person abroad",
        divorce_status: "Case status", claimant_can_self_maintain: "Claimant can self-support", respondent_has_means: "Other person can pay", needs: "Needs",
        separated_months: "Living apart", marriage_years: "Married" },
  hi: { law: "व्यक्तिगत कानून", claimant: "दावेदार", ground: "कारण", mutual_consent: "दोनों तलाक पर सहमत", domestic_violence: "घर में हिंसा", respondent_abroad: "दूसरा व्यक्ति विदेश में",
        divorce_status: "मामले की स्थिति", claimant_can_self_maintain: "दावेदार आत्मनिर्भर", respondent_has_means: "दूसरा व्यक्ति दे सकता है", needs: "ज़रूरत" },
  ta: { law: "தனிநபர் சட்டம்", claimant: "கோருபவர்", ground: "காரணம்", mutual_consent: "இருவரும் விவாகரத்துக்குச் சம்மதம்", domestic_violence: "வீட்டில் வன்முறை", respondent_abroad: "மற்றவர் வெளிநாட்டில்",
        divorce_status: "வழக்கு நிலை", claimant_can_self_maintain: "கோருபவர் தன்னைத் தானே பராமரிக்க முடியும்", respondent_has_means: "மற்றவர் கொடுக்க முடியும்", needs: "தேவைகள்" },
};
const VAL = {
  en: { ground: { cruelty: "Cruelty", desertion: "Desertion", adultery: "Adultery" }, divorce_status: { none: "No case filed", pending: "Case pending", decreed: "Decree passed", filed: "Filed or decided" }, yes: "Yes", no: "No" },
  hi: { ground: { cruelty: "क्रूरता", desertion: "परित्याग", adultery: "व्यभिचार" }, divorce_status: { none: "कोई मामला नहीं", pending: "मामला चल रहा", decreed: "फैसला हो चुका", filed: "दायर या तय" }, yes: "हाँ", no: "नहीं" },
  ta: { ground: { cruelty: "கொடுமை", desertion: "கைவிடுதல்", adultery: "கள்ள உறவு" }, divorce_status: { none: "வழக்கு இல்லை", pending: "வழக்கு நடைபெறுகிறது", decreed: "தீர்ப்பு வழங்கப்பட்டது", filed: "தாக்கல் / முடிந்தது" }, yes: "ஆம்", no: "இல்லை" },
};
const UI = {
  en: { weRead: "We read this from your words", yes: "Yes, that is right", no: "No, let me choose", src: { "keyword-hint": "keyword hint", slm: "small model", groq: "hosted model" }, conflict: "You mentioned more than one:", pick: "Please pick the one that governs the marriage.",
        understood: "Understood so far", suggested: "Needs your confirmation", confirmed: "Confirmed", conflictS: "Conflict", preselected: "Pre-selected from your words. Change if wrong.", start: "Begin", privacy: "Nothing is stored beyond this session. Sessions are deleted after 2 hours." },
  hi: { weRead: "हमने आपकी बातों से यह समझा", yes: "हाँ, सही है", no: "नहीं, मैं चुनूँगा", src: { "keyword-hint": "शब्द संकेत", slm: "छोटा मॉडल", groq: "होस्टेड मॉडल" }, conflict: "आपने एक से अधिक बताए:", pick: "कृपया वह चुनें जो विवाह पर लागू होता है।",
        understood: "अब तक समझा", suggested: "आपकी पुष्टि चाहिए", confirmed: "पुष्ट", conflictS: "विरोधाभास", preselected: "आपकी बातों से पहले से चुना गया। गलत हो तो बदलें।", start: "शुरू करें", privacy: "इस सत्र के बाद कुछ संग्रहित नहीं होता। सत्र 2 घंटे बाद हट जाते हैं।" },
  ta: { weRead: "உங்கள் வார்த்தைகளிலிருந்து இதைப் புரிந்துகொண்டோம்", yes: "ஆம், சரி", no: "இல்லை, நான் தேர்வு செய்கிறேன்", src: { "keyword-hint": "சொல் குறிப்பு", slm: "சிறிய மாடல்", groq: "ஹோஸ்ட் மாடல்" }, conflict: "நீங்கள் ஒன்றுக்கு மேல் குறிப்பிட்டீர்கள்:", pick: "திருமணத்துக்குப் பொருந்துவதைத் தேர்வு செய்யுங்கள்.",
        understood: "இதுவரை புரிந்தது", suggested: "உங்கள் உறுதிப்படுத்தல் தேவை", confirmed: "உறுதி", conflictS: "முரண்பாடு", preselected: "உங்கள் வார்த்தைகளிலிருந்து முன்தேர்வு. தவறெனில் மாற்றுங்கள்.", start: "தொடங்குங்கள்", privacy: "இந்த அமர்வுக்குப் பின் எதுவும் சேமிக்கப்படாது. அமர்வுகள் 2 மணி நேரத்தில் நீக்கப்படும்." },
};
const srcKey = (s) => (s || "").startsWith("slm") ? "slm" : (s || "").startsWith("groq") ? "groq" : "keyword-hint";
function fmt(t, lang, slot, v) {
  if (slot === "law") return t.laws[v] || v;
  if (slot === "claimant") return t.claimants[v] || v;
  if (slot === "needs") return (v || []).map((n) => t.needList[n] || n).join(", ");
  if (typeof v === "boolean") return v ? VAL[lang].yes : VAL[lang].no;
  if (slot === "separated_months") return v >= 12 ? (v / 12).toFixed(v % 12 ? 1 : 0) + " yr" : v + " mo";
  if (slot === "marriage_years") return v + " yr";
  return (VAL[lang][slot] && VAL[lang][slot][v]) || v;
}
const LANGS = [["en", "EN"], ["hi", "हि"], ["ta", "த"]];
const EXTRA = {
  en: { memo: "Memorandum of advice", steps: ["Facts", "Routes", "Documents"], ws: "Case workspace", open_n: "open", sub: "Indian family-law research assistant", consult: "Consultation", matter: "Matter summary", issues: "Routes available", seq: "Recommended sequence", auth: "Authorities", notice: "Notice", prepared: "Prepared", stamp: "Unverified. For review by an advocate.", st: { eligible: "Eligible", conditional: "Conditions open" } },
  hi: { memo: "सलाह ज्ञापन", steps: ["तथ्य", "रास्ते", "दस्तावेज़"], ws: "केस वर्कस्पेस", open_n: "शेष", sub: "भारतीय पारिवारिक कानून शोध सहायक", consult: "परामर्श", matter: "मामले का सार", issues: "उपलब्ध रास्ते", seq: "सुझाया गया क्रम", auth: "प्रमाण-निर्णय", notice: "सूचना", prepared: "तैयार", stamp: "असत्यापित। वकील द्वारा जाँच हेतु।" },
  ta: { memo: "ஆலோசனைக் குறிப்பு", steps: ["உண்மைகள்", "வழிகள்", "ஆவணங்கள்"], ws: "வழக்கு பணியிடம்", open_n: "நிலுவை", sub: "இந்தியக் குடும்பச் சட்ட ஆய்வு உதவியாளர்", consult: "ஆலோசனை", matter: "வழக்குச் சுருக்கம்", issues: "கிடைக்கும் வழிகள்", seq: "பரிந்துரைக்கப்பட்ட வரிசை", auth: "முன்னுதாரணங்கள்", notice: "அறிவிப்பு", prepared: "தயாரிக்கப்பட்டது", stamp: "சரிபார்க்கப்படவில்லை. வழக்கறிஞர் பார்வைக்கு." },
};

function Understood({ t, lang, turn, onSend, busy }) {
  const u = (turn && turn.understood) || []; const ui = UI[lang]; const sl = SLOT[lang] || SLOT.en;
  if (!u.length) return null;
  return (<section className="und" aria-label={ui.understood}><h3>{ui.understood}</h3>
    <ul>{u.map((r, i) => (
      <li key={r.slot + i} className={"u-" + r.status}>
        <span className="u-k">{sl[r.slot] || SLOT.en[r.slot] || r.slot}</span>
        <span className="u-v">{r.status === "conflict" ? r.value.map((v) => fmt(t, lang, r.slot, v)).join(" / ") : fmt(t, lang, r.slot, r.value)}</span>
        <span className="u-s">{r.status === "suggested" ? ui.suggested : r.status === "conflict" ? ui.conflictS : ui.confirmed}</span>
        {r.status === "suggested" && <button disabled={busy} aria-label={ui.yes} onClick={() => onSend({ answer: { slot: r.slot, value: r.value } }, (SLOT[lang][r.slot] || r.slot) + ": " + fmt(t, lang, r.slot, r.value))}>✓</button>}
      </li>))}</ul></section>);
}

function Workspace({ t, x, e, lang, turn, onSend, busy, places, setPlaces, onExample }) {
  const f = (turn && turn.facts) || {};
  const final = turn && turn.state === "advice";
  const A = turn && (turn.advice || turn.provisional);
  const chips = [];
  (f.needs || []).forEach((n) => chips.push(t.needList[n]));
  const stage = final ? 2 : A ? 1 : 0;
  return (
    <aside className="ws" aria-label={e.ws}>
      <div className="ws-head">
        <div><h2>{e.memo}</h2><p className="ref">{e.ws}{turn ? " · Ref. NG-" + turn.session_id.slice(0, 6).toUpperCase() : ""} · {new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}</p></div>
        {final && <button className="ghost" onClick={() => window.print()}>{x.print}</button>}
      </div>
      <ol className="steps">{e.steps.map((n, i) => <li key={i} className={i < stage ? "done" : i === stage ? "now" : ""}><span className="dot">{i < stage ? "✓" : i + 1}</span>{n}</li>)}</ol>
      {!A && <p className="lede quiet">{x.empty}</p>}
      {chips.length > 0 && <div className="tags">{chips.map((c, i) => <span key={i}>{c}</span>)}</div>}
      <Understood t={t} lang={lang} turn={turn} onSend={onSend} busy={busy} />
      {A && <>
        {!final && <p className="prov-note">{x.provisional}</p>}
        <div className="cards">
          {A.remedies.map((r, n) => (
            <details className={"card " + r.status} key={r.id} open={A.remedies.length < 3}>
              <summary>
                <span className="num" aria-hidden="true">{String(n + 1).padStart(2, "0")}</span>
                <span className="sec">{r.provision.split(";")[0]}</span>
                <h4>{r.title}</h4>
                <span className="forum">{r.forum}</span>
                <span className="foot"><span className={"status " + r.status}>{(e.st && e.st[r.status]) || t.status[r.status] || r.status}</span>
                  {r.conditions_open.length > 0 && <span className="openn">{r.conditions_open.length} {e.open_n}</span>}</span>
              </summary>
              <div className="body">
                {r.venues.length > 0 && <><h5>{t.venues}</h5><ul>{r.venues.map((v, j) => <li key={j}>{v.place && <b>{v.place}: </b>}{v.note}</li>)}</ul></>}
                {r.conditions_open.length > 0 && <><h5>{t.open}</h5><ul className="open">{r.conditions_open.map((c, j) => <li key={j}>{c}</li>)}</ul></>}
                {r.notes.length > 0 && <ul className="muted">{r.notes.map((n, j) => <li key={j}>{n}</li>)}</ul>}
                {r.authorities.length > 0 && <><h5>{e.auth}</h5><ul className="auth">{r.authorities.map((a, j) => <li key={j}>{a}</li>)}</ul></>}
              </div>
            </details>))}
        </div>
        {A.warnings.map((w, i) => <p className="warn" key={i}>{w}</p>)}
        {turn.plan && turn.plan.length > 0 && <>
          <h3>{e.seq}</h3>
          <ol className="line">{turn.plan.map((p) => <li key={p.id}><b>{p.title}</b><span>{t.docs}: {p.docs.slice(0, 3).join("; ")}{p.docs.length > 3 ? ` (+${p.docs.length - 3})` : ""}</span></li>)}</ol></>}
        {A.disclosures.length > 0 && <><h3>{t.disclose}</h3><ul className="plain">{A.disclosures.map((d, i) => <li key={i}>{d}</li>)}</ul></>}
        {final && turn.unchecked.length > 0 && <><h3>{t.unchecked}</h3>
          {turn.unchecked.map((u) => <div className="uc" key={u.slot}><span>{u.prompt}</span>
            <span className="yn"><button disabled={busy} onClick={() => onSend({ answer: { slot: u.slot, value: true } }, u.prompt + " ✓")}>✓</button>
              <button disabled={busy} onClick={() => onSend({ answer: { slot: u.slot, value: false } }, u.prompt + " ✗")}>✗</button></span></div>)}</>}
        {final && <details className="places"><summary>{t.places}</summary>
          {turn.place_fields.map((k) => <input key={k} value={places[k] || ""} onChange={(ev) => setPlaces({ ...places, [k]: ev.target.value })}
            placeholder={{ marriage_place: t.marriagePlace, last_cohabitation_place: t.lastPlace, petitioner_residence: t.myPlace, respondent_residence: t.theirPlace }[k]} />)}
          <button className="primary" disabled={busy} onClick={() => onSend({ answer: { slot: "places", value: places } }, null)}>{t.go}</button>
        </details>}
        <p className="notice"><b>{e.stamp}</b> {A.disclaimer}</p>
      </>}
    </aside>);
}

export default function App() {
  const [lang, setLang] = useState("en");
  const t = T[lang], x = X[lang], e = { ...EXTRA.en, ...EXTRA[lang] };
  const [sid, setSid] = useState(null);
  const [snap, setSnap] = useState(null);
  const [log, setLog] = useState([]);
  const [turn, setTurn] = useState(null);
  const [text, setText] = useState("");
  const [sel, setSel] = useState([]);
  const [places, setPlaces] = useState({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [view, setView] = useState("chat");
  const end = useRef(null);
  useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  useEffect(() => { end.current && end.current.scrollIntoView({ behavior: "smooth", block: "end" }); }, [log, turn, busy]);

  const send = async (body, shown) => {
    setBusy(true); setErr("");
    if (shown) setLog((l) => [...l, { who: "you", text: shown }]);
    try {
      const j = await agent({ session_id: sid, lang, snapshot: snap, ...body });
      setSnap(j.snapshot);
      setSid(j.session_id);
      setLog((l) => [...l, { who: "agent", text: j.reply }]);
      setTurn(j); setSel(j.question && j.question.selected ? j.question.selected : []);
      if (j.state === "advice") setView("case");
    } catch (er) { setErr(er.message); }
    setBusy(false);
  };
  const submit = () => { const v = text.trim(); if (v) { send({ text: v }, v); setText(""); } };
  const restart = () => { setSid(null); setSnap(null); setLog([]); setTurn(null); setPlaces({}); setSel([]); setErr(""); setView("chat"); };
  const q = turn && turn.state === "clarify" ? turn.question : null;

  const landing = !turn && log.length === 0 && !busy;
  if (landing) return (
    <main className="hero">
      <div className="hero-top">
        <div className="brand"><span className="mark"><Scales /></span><span className="name">{x.brand}</span></div>
        <div className="seg" role="group" aria-label="Language">{LANGS.map(([k, l]) => <button key={k} aria-pressed={k === lang} className={k === lang ? "on" : ""} onClick={() => setLang(k)}>{l}</button>)}</div>
      </div>
      <div className="hero-main">
        <p className="eyebrow">{e.sub}</p>
        <h1>{t.title}</h1>
        <div className="hero-in">
          <textarea rows={3} value={text} placeholder={x.placeholder} aria-label={x.placeholder} onChange={(ev) => setText(ev.target.value)}
            onKeyDown={(ev) => { if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); submit(); } }} />
          <button className="primary big" disabled={busy || !text.trim()} onClick={submit}>{UI[lang].start} →</button>
        </div>
        <div className="examples">{x.ex.map((s2, i) => <button key={i} onClick={() => send({ text: s2 }, s2)}>{s2}</button>)}</div>
      </div>
      <footer className="hero-foot"><p>{x.how}</p><p>{UI[lang].privacy}</p></footer>
      {err && <p className="err" role="alert">{err}</p>}
    </main>);

  return (
    <div className={"app view-" + view}>
      <section className="rail" aria-label={e.consult}>
        <div className="rail-top">
          <div className="brand"><span className="mark"><Scales /></span><span className="name">{x.brand}</span></div>
          <div className="seg" role="group" aria-label="Language">
            {LANGS.map(([k, l]) => <button key={k} aria-pressed={k === lang} className={k === lang ? "on" : ""} onClick={() => setLang(k)}>{l}</button>)}
          </div>
        </div>
        {log.length > 0 && <button className="restart" onClick={restart}>{x.restart}</button>}
        <div className="chat">
          <div className="log" aria-live="polite">
            {log.length === 0 && <div className="msg agent">{t.ask}</div>}
            {log.map((m, i) => <div key={i} className={"msg " + m.who}>{m.text}</div>)}
            {q && q.affects && q.affects.length > 0 && <p className="why"><b>{x.why}</b> {q.affects.slice(0, 3).join("; ")}</p>}
            {q && q.suggested && q.kind === "choice" && (
              <div className="sug" role="group" aria-label={UI[lang].weRead}>
                <p className="sug-h">{UI[lang].weRead}</p>
                <p className="sug-v">{fmt(t, lang, q.slot, q.suggested.value)}</p>
                <p className="sug-w">{q.suggested.why} <span className="tag">{UI[lang].src[srcKey(q.suggested.source)]}</span></p>
                <div className="sug-a"><button className="primary" disabled={busy} onClick={() => send({ answer: { slot: q.slot, value: q.suggested.value } }, fmt(t, lang, q.slot, q.suggested.value))}>{UI[lang].yes}</button>
                  <span className="sug-n">{UI[lang].no} ↓</span></div>
              </div>)}
            {q && q.conflict && (
              <div className="sug conflict" role="group"><p className="sug-h">{UI[lang].conflict}</p>
                <p className="sug-v">{q.conflict.map((v) => fmt(t, lang, q.slot, v)).join("  ·  ")}</p><p className="sug-w">{UI[lang].pick}</p></div>)}
            {q && q.kind === "multi" && q.selected && q.selected.length > 0 && turn.understood && <p className="why">{UI[lang].preselected}</p>}
            {q && <div className="answers">
              {q.kind === "choice" && q.options.map((o, i) => <button key={i} disabled={busy} onClick={() => send({ answer: { slot: q.slot, value: o.value } }, o.label)}>{o.label}</button>)}
              {q.kind === "multi" && <>
                {q.options.map((o, i) => { const on = sel.includes(o.value);
                  return <button key={i} className={"chip" + (on ? " on" : "")} aria-pressed={on} onClick={() => setSel(on ? sel.filter((v) => v !== o.value) : [...sel, o.value])}>{o.label}</button>; })}
                <button className="primary" disabled={busy || !sel.length} onClick={() => send({ answer: { slot: q.slot, value: sel } }, q.options.filter((o) => sel.includes(o.value)).map((o) => o.label).join(", "))}>{x.confirm}</button></>}
              {!["law", "claimant", "needs"].includes(q.slot) && <button className="skip" disabled={busy} onClick={() => send({ answer: { slot: "skip", value: null } }, t.skipq)}>{t.skipq}</button>}
            </div>}
            {busy && <div className="msg agent dots" aria-label={x.thinking}><i /><i /><i /></div>}
            {turn && turn.state === "advice" && <button className="primary see" onClick={() => setView("case")}>{e.ws}</button>}
            {err && <p className="err" role="alert">{err}</p>}
            <div ref={end} />
          </div>
          <div className="composer">
            {turn && turn.asked > 0 && <span className="asked">{turn.asked} {x.asked}</span>}
            <textarea rows={1} value={text} placeholder={x.placeholder} aria-label={x.placeholder} onChange={(ev) => setText(ev.target.value)}
              onKeyDown={(ev) => { if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); submit(); } }} />
            <button className="primary" disabled={busy || !text.trim()} onClick={submit}>{t.send}</button>
          </div>
        </div>
      </section>
      <Workspace lang={lang} onExample={(v) => send({ text: v }, v)} t={t} x={x} e={e} turn={turn} onSend={send} busy={busy} places={places} setPlaces={setPlaces} />
      <nav className="tabs" role="tablist">
        <button role="tab" aria-selected={view === "chat"} className={view === "chat" ? "on" : ""} onClick={() => setView("chat")}>{e.consult}</button>
        <button role="tab" aria-selected={view === "case"} className={view === "case" ? "on" : ""} onClick={() => setView("case")}>{e.ws}</button>
      </nav>
    </div>);
}
