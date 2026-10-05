import { useState, useRef, useEffect } from "react";
import { T, X } from "./strings.js";
import { agent } from "./api.js";

const LANGS = [["en", "EN"], ["hi", "हि"], ["ta", "த"]];
const EXTRA = {
  en: { sub: "Indian family-law research assistant", consult: "Consultation", matter: "Matter summary", issues: "Routes available", seq: "Recommended sequence", auth: "Authorities", notice: "Notice", prepared: "Prepared", stamp: "Unverified. For review by an advocate.", st: { eligible: "Eligible", conditional: "Conditions open" } },
  hi: { sub: "भारतीय पारिवारिक कानून शोध सहायक", consult: "परामर्श", matter: "मामले का सार", issues: "उपलब्ध रास्ते", seq: "सुझाया गया क्रम", auth: "प्रमाण-निर्णय", notice: "सूचना", prepared: "तैयार", stamp: "असत्यापित। वकील द्वारा जाँच हेतु।" },
  ta: { sub: "இந்தியக் குடும்பச் சட்ட ஆய்வு உதவியாளர்", consult: "ஆலோசனை", matter: "வழக்குச் சுருக்கம்", issues: "கிடைக்கும் வழிகள்", seq: "பரிந்துரைக்கப்பட்ட வரிசை", auth: "முன்னுதாரணங்கள்", notice: "அறிவிப்பு", prepared: "தயாரிக்கப்பட்டது", stamp: "சரிபார்க்கப்படவில்லை. வழக்கறிஞர் பார்வைக்கு." },
};

function Brief({ t, x, e, lang, turn, onSend, busy, places, setPlaces }) {
  const f = (turn && turn.facts) || {};
  const final = turn && turn.state === "advice";
  const A = turn && (turn.advice || turn.provisional);
  const rows = [];
  if (f.law) rows.push([t.law, t.laws[f.law]]);
  if (f.claimant) rows.push([t.claimant, t.claimants[f.claimant]]);
  if ((f.needs || []).length) rows.push([t.needs, f.needs.map((n) => t.needList[n]).join(", ")]);
  const date = new Date().toLocaleDateString(lang === "en" ? "en-IN" : lang === "hi" ? "hi-IN" : "ta-IN", { day: "numeric", month: "long", year: "numeric" });
  return (
    <aside className="paper" aria-label={x.caseTitle}>
      <header className="p-head">
        <div><h2>{x.caseTitle}</h2><p className="meta">{e.prepared} {date}</p></div>
        {final && <button className="ghost" onClick={() => window.print()}>{x.print}</button>}
      </header>
      <p className="stamp">{e.stamp}</p>
      <section>
        <h3>{e.matter}</h3>
        {rows.length === 0 ? <p className="muted">{x.empty}</p> :
          <table className="matter"><tbody>{rows.map(([k, v], i) => <tr key={i}><th scope="row">{k}</th><td>{v}</td></tr>)}</tbody></table>}
      </section>
      {A && <>
        <section>
          <h3>{e.issues}{!final && <span className="prov-note">{x.provisional}</span>}</h3>
          {A.remedies.map((r, i) => (
            <article className="route" key={r.id}>
              <div className="r-top"><h4>{r.title}</h4>
                <span className={"status " + r.status}>{(e.st && e.st[r.status]) || t.status[r.status] || r.status}</span></div>
              <p className="cite">{r.provision}. {r.forum}.</p>
              {r.venues.length > 0 && <><h5>{t.venues}</h5><ul>{r.venues.map((v, j) => <li key={j}>{v.place && <b>{v.place}: </b>}{v.note}</li>)}</ul></>}
              {r.conditions_open.length > 0 && <><h5>{t.open}</h5><ul className="open">{r.conditions_open.map((c, j) => <li key={j}>{c}</li>)}</ul></>}
              {r.notes.length > 0 && <ul className="muted">{r.notes.map((n, j) => <li key={j}>{n}</li>)}</ul>}
              {r.authorities.length > 0 && <><h5>{e.auth}</h5><ul className="auth">{r.authorities.map((a, j) => <li key={j}>{a}</li>)}</ul></>}
            </article>))}
          {A.warnings.map((w, i) => <p className="warn" key={i}>{w}</p>)}
        </section>
        {turn.plan && turn.plan.length > 0 && <section>
          <h3>{e.seq}</h3>
          <ol className="seq">{turn.plan.map((p) => <li key={p.id}><b>{p.title}</b><span className="docs">{t.docs}: {p.docs.join("; ")}</span></li>)}</ol>
        </section>}
        {A.disclosures.length > 0 && <section><h3>{t.disclose}</h3><ul>{A.disclosures.map((d, i) => <li key={i}>{d}</li>)}</ul></section>}
        {final && turn.unchecked.length > 0 && <section><h3>{t.unchecked}</h3>
          {turn.unchecked.map((u) => <div className="uc" key={u.slot}><span>{u.prompt}</span>
            <span className="yn"><button disabled={busy} onClick={() => onSend({ answer: { slot: u.slot, value: true } }, u.prompt + " ✓")}>✓</button>
              <button disabled={busy} onClick={() => onSend({ answer: { slot: u.slot, value: false } }, u.prompt + " ✗")}>✗</button></span></div>)}
        </section>}
        {final && <details className="places"><summary>{t.places}</summary>
          {turn.place_fields.map((k) => <input key={k} value={places[k] || ""} onChange={(ev) => setPlaces({ ...places, [k]: ev.target.value })}
            placeholder={{ marriage_place: t.marriagePlace, last_cohabitation_place: t.lastPlace, petitioner_residence: t.myPlace, respondent_residence: t.theirPlace }[k]} />)}
          <button className="primary" disabled={busy} onClick={() => onSend({ answer: { slot: "places", value: places } }, null)}>{t.go}</button>
        </details>}
        <footer className="notice"><b>{e.notice}. </b>{A.disclaimer}</footer>
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
    <div className="app">
      <header className="top"><div className="top-in">
        <div className="brand"><span className="mark" aria-hidden="true">§</span>
          <div><div className="name">{x.brand}</div><div className="tag">{e.sub}</div></div></div>
        <div className="top-r">
          {log.length > 0 && <button className="ghost on-dark" onClick={restart}>{x.restart}</button>}
          <div className="seg" role="group" aria-label="Language">
            {LANGS.map(([k, l]) => <button key={k} aria-pressed={k === lang} className={k === lang ? "on" : ""} onClick={() => setLang(k)}>{l}</button>)}
          </div>
        </div>
      </div></header>
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={view === "chat"} className={view === "chat" ? "on" : ""} onClick={() => setView("chat")}>{e.consult}</button>
        <button role="tab" aria-selected={view === "case"} className={view === "case" ? "on" : ""} onClick={() => setView("case")}>{x.caseTitle}</button>
      </div>
      <main className={"grid view-" + view}>
        <section className="chat" aria-label={e.consult}>
          {log.length === 0 ? (
            <div className="hero">
              <h1>{t.title}</h1>
              <p className="lede">{t.sub}</p>
              <p className="try">{x.tryA}</p>
              <div className="examples">{x.ex.map((s, i) => <button key={i} onClick={() => send({ text: s }, s)}>{s}</button>)}</div>
              <details className="how"><summary>{x.howTitle}</summary><p>{x.how}</p></details>
            </div>
          ) : (
            <div className="log" aria-live="polite">
              {log.map((m, i) => <div key={i} className={"msg " + m.who}><span className="who">{m.who === "you" ? x.you : x.brand}</span>{m.text}</div>)}
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
              {turn && turn.state === "advice" && view === "chat" && <button className="primary see" onClick={() => setView("case")}>{x.caseTitle}</button>}
              {err && <p className="err" role="alert">{err}</p>}
              <div ref={end} />
            </div>)}
          <div className="composer">
            {turn && turn.asked > 0 && <span className="asked">{turn.asked} {x.asked}</span>}
            <textarea rows={1} value={text} placeholder={x.placeholder} aria-label={x.placeholder} onChange={(ev) => setText(ev.target.value)}
              onKeyDown={(ev) => { if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); submit(); } }} />
            <button className="primary" disabled={busy || !text.trim()} onClick={submit}>{t.send}</button>
          </div>
        </section>
        <Brief t={t} x={x} e={e} lang={lang} turn={turn} onSend={send} busy={busy} places={places} setPlaces={setPlaces} />
      </main>
    </div>);
}
