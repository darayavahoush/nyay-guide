import { useState, useRef, useEffect } from "react";
import { T, X } from "./strings.js";
import { agent } from "./api.js";

const LANGS = [["en", "EN"], ["hi", "हि"], ["ta", "த"]];
const EXTRA = {
  en: { steps: ["Facts", "Routes", "Documents"], ws: "Case workspace", open_n: "open", sub: "Indian family-law research assistant", consult: "Consultation", matter: "Matter summary", issues: "Routes available", seq: "Recommended sequence", auth: "Authorities", notice: "Notice", prepared: "Prepared", stamp: "Unverified. For review by an advocate.", st: { eligible: "Eligible", conditional: "Conditions open" } },
  hi: { steps: ["तथ्य", "रास्ते", "दस्तावेज़"], ws: "केस वर्कस्पेस", open_n: "शेष", sub: "भारतीय पारिवारिक कानून शोध सहायक", consult: "परामर्श", matter: "मामले का सार", issues: "उपलब्ध रास्ते", seq: "सुझाया गया क्रम", auth: "प्रमाण-निर्णय", notice: "सूचना", prepared: "तैयार", stamp: "असत्यापित। वकील द्वारा जाँच हेतु।" },
  ta: { steps: ["உண்மைகள்", "வழிகள்", "ஆவணங்கள்"], ws: "வழக்கு பணியிடம்", open_n: "நிலுவை", sub: "இந்தியக் குடும்பச் சட்ட ஆய்வு உதவியாளர்", consult: "ஆலோசனை", matter: "வழக்குச் சுருக்கம்", issues: "கிடைக்கும் வழிகள்", seq: "பரிந்துரைக்கப்பட்ட வரிசை", auth: "முன்னுதாரணங்கள்", notice: "அறிவிப்பு", prepared: "தயாரிக்கப்பட்டது", stamp: "சரிபார்க்கப்படவில்லை. வழக்கறிஞர் பார்வைக்கு." },
};

function Workspace({ t, x, e, turn, onSend, busy, places, setPlaces, onExample }) {
  const f = (turn && turn.facts) || {};
  const final = turn && turn.state === "advice";
  const A = turn && (turn.advice || turn.provisional);
  const chips = [];
  if (f.law) chips.push(t.laws[f.law]);
  if (f.claimant) chips.push(t.claimants[f.claimant]);
  (f.needs || []).forEach((n) => chips.push(t.needList[n]));
  const stage = final ? 2 : A ? 1 : 0;
  return (
    <aside className="ws" aria-label={e.ws}>
      <div className="ws-head">
        <h2>{e.ws}</h2>
        {final && <button className="ghost" onClick={() => window.print()}>{x.print}</button>}
      </div>
      <ol className="steps">{e.steps.map((n, i) => <li key={i} className={i < stage ? "done" : i === stage ? "now" : ""}><span className="dot">{i < stage ? "✓" : i + 1}</span>{n}</li>)}</ol>
      {!A && (
        <div className="start">
          <h1>{t.title}</h1><p className="lede">{t.sub}</p>
          <p className="try">{x.tryA}</p>
          <div className="examples">{x.ex.map((s, i) => <button key={i} onClick={() => onExample(s)}>{s}</button>)}</div>
          <p className="how"><b>{x.howTitle}.</b> {x.how}</p>
        </div>)}
      {chips.length > 0 && <div className="tags">{chips.map((c, i) => <span key={i}>{c}</span>)}</div>}
      {A && <>
        {!final && <p className="prov-note">{x.provisional}</p>}
        <div className="cards">
          {A.remedies.map((r) => (
            <details className={"card " + r.status} key={r.id} open={A.remedies.length < 3}>
              <summary>
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
  const [log, setLog] = useState([]);
  const [turn, setTurn] = useState(null);
  const [text, setText] = useState("");
  const [sel, setSel] = useState([]);
  const [places, setPlaces] = useState({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [view, setView] = useState("chat");
  const end = useRef(null);
  useEffect(() => { end.current && end.current.scrollIntoView({ behavior: "smooth", block: "end" }); }, [log, turn, busy]);

  const send = async (body, shown) => {
    setBusy(true); setErr("");
    if (shown) setLog((l) => [...l, { who: "you", text: shown }]);
    try {
      const j = await agent({ session_id: sid, lang, ...body });
      setSid(j.session_id);
      setLog((l) => [...l, { who: "agent", text: j.reply }]);
      setTurn(j); setSel(j.question && j.question.selected ? j.question.selected : []);
      if (j.state === "advice") setView("case");
    } catch (er) { setErr(er.message); }
    setBusy(false);
  };
  const submit = () => { const v = text.trim(); if (v) { send({ text: v }, v); setText(""); } };
  const restart = () => { setSid(null); setLog([]); setTurn(null); setPlaces({}); setSel([]); setErr(""); setView("chat"); };
  const q = turn && turn.state === "clarify" ? turn.question : null;

  return (
    <div className={"app view-" + view}>
      <section className="rail" aria-label={e.consult}>
        <div className="rail-top">
          <div className="brand"><span className="mark" aria-hidden="true">§</span><span className="name">{x.brand}</span></div>
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
      <Workspace onExample={(v) => send({ text: v }, v)} t={t} x={x} e={e} turn={turn} onSend={send} busy={busy} places={places} setPlaces={setPlaces} />
      <nav className="tabs" role="tablist">
        <button role="tab" aria-selected={view === "chat"} className={view === "chat" ? "on" : ""} onClick={() => setView("chat")}>{e.consult}</button>
        <button role="tab" aria-selected={view === "case"} className={view === "case" ? "on" : ""} onClick={() => setView("case")}>{e.ws}</button>
      </nav>
    </div>);
}
