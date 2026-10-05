import { useState, useRef, useEffect } from "react";
import { T, X } from "./strings.js";
import { agent } from "./api.js";

const LANGS = [["en", "EN"], ["hi", "हि"], ["ta", "த"]];

function Case({ t, x, turn, onSend, busy, places, setPlaces }) {
  const f = (turn && turn.facts) || {};
  const final = turn && turn.state === "advice";
  const A = turn && (turn.advice || turn.provisional);
  const adv = !!A;
  const chips = [];
  if (f.law) chips.push([t.law, t.laws[f.law]]);
  if (f.claimant) chips.push([t.claimant, t.claimants[f.claimant]]);
  (f.needs || []).forEach((n) => chips.push([t.needs, t.needList[n]]));
  return (
    <aside className="case" aria-label={x.caseTitle}>
      <div className="case-head">
        <h2>{x.caseTitle}</h2>
        {final && <button className="ghost" onClick={() => window.print()}>{x.print}</button>}
      </div>
      {chips.length === 0 && !adv && <p className="muted">{x.empty}</p>}
      {chips.length > 0 && (
        <dl className="facts">{chips.map(([k, v], i) => <div key={i}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
      )}
      {adv && <>
        <h3>{x.routes} <span className="count">{A.remedies.length}</span></h3>
        {!final && <p className="prov-note">{x.provisional}</p>}
        {A.remedies.map((r, i) => (
          <details className="remedy" key={r.id} open={i === 0}>
            <summary>
              <span className="r-title">{r.title}</span>
              <span className={"badge " + r.status}>{t.status[r.status] || r.status}</span>
            </summary>
            <p className="prov">{r.provision}<br />{r.forum}</p>
            {r.venues.length > 0 && <><h4>{t.venues}</h4><ul>{r.venues.map((v, j) => <li key={j}>{v.place && <strong>{v.place}: </strong>}{v.note}</li>)}</ul></>}
            {r.conditions_open.length > 0 && <><h4>{t.open}</h4><ul className="open">{r.conditions_open.map((c, j) => <li key={j}>{c}</li>)}</ul></>}
            {r.notes.length > 0 && <ul className="notes">{r.notes.map((n, j) => <li key={j}>{n}</li>)}</ul>}
            {r.authorities.length > 0 && <><h4>{t.authorities}</h4><ul className="auth">{r.authorities.map((a, j) => <li key={j}>{a}</li>)}</ul></>}
          </details>))}
        {A.warnings.map((w, i) => <p className="warn" key={i}>{w}</p>)}
        {turn.plan && turn.plan.length > 0 && <>
          <h3>{x.plan}</h3>
          <ol className="plan">{turn.plan.map((p) => (
            <li key={p.id}><strong>{p.title}</strong>
              <div className="docs">{t.docs}: {p.docs.join("; ")}</div></li>))}</ol>
        </>}
        {A.disclosures.length > 0 && <><h3>{t.disclose}</h3><ul>{A.disclosures.map((d, i) => <li key={i}>{d}</li>)}</ul></>}
        {final && turn.unchecked.length > 0 && <div className="unchecked">
          <h3>{t.unchecked}</h3>
          {turn.unchecked.map((u) => (
            <div className="uc" key={u.slot}><span>{u.prompt}</span>
              <span className="yn"><button disabled={busy} onClick={() => onSend({ answer: { slot: u.slot, value: true } }, u.prompt + " ✓")}>✓</button>
                <button disabled={busy} onClick={() => onSend({ answer: { slot: u.slot, value: false } }, u.prompt + " ✗")}>✗</button></span></div>))}
        </div>}
        {final && <details className="places"><summary>{t.places}</summary>
          {turn.place_fields.map((k) => (
            <input key={k} value={places[k] || ""} onChange={(e) => setPlaces({ ...places, [k]: e.target.value })}
              placeholder={{ marriage_place: t.marriagePlace, last_cohabitation_place: t.lastPlace, petitioner_residence: t.myPlace, respondent_residence: t.theirPlace }[k]} />))}
          <button className="primary" disabled={busy} onClick={() => onSend({ answer: { slot: "places", value: places } }, null)}>{t.go}</button>
        </details>}
        <p className="disc">{A.disclaimer}</p>
      </>}
    </aside>);
}

export default function App() {
  const [lang, setLang] = useState("en");
  const t = T[lang], x = X[lang];
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
      if (j.state === "advice" || j.provisional) setView((v) => (j.state === "advice" ? "case" : v));
    } catch (e) { setErr(e.message); }
    setBusy(false);
  };
  const submit = () => { const v = text.trim(); if (v) { send({ text: v }, v); setText(""); } };
  const restart = () => { setSid(null); setLog([]); setTurn(null); setPlaces({}); setSel([]); setErr(""); setView("chat"); };
  const q = turn && turn.state === "clarify" ? turn.question : null;
  const asked = turn ? turn.asked : 0;

  return (
    <div className="app">
      <header className="top">
        <div className="brand"><span className="mark" aria-hidden="true">न्या</span><span>{x.brand}</span></div>
        <div className="top-r">
          {log.length > 0 && <button className="ghost" onClick={restart}>{x.restart}</button>}
          <div className="seg" role="group" aria-label="Language">
            {LANGS.map(([k, l]) => <button key={k} aria-pressed={k === lang} className={k === lang ? "on" : ""} onClick={() => setLang(k)}>{l}</button>)}
          </div>
        </div>
      </header>

      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={view === "chat"} className={view === "chat" ? "on" : ""} onClick={() => setView("chat")}>{t.tabAgent}</button>
        <button role="tab" aria-selected={view === "case"} className={view === "case" ? "on" : ""} onClick={() => setView("case")}>{x.caseTitle}</button>
      </div>

      <main className={"grid view-" + view}>
        <section className="chat" aria-label={t.tabAgent}>
          {log.length === 0 ? (
            <div className="hero">
              <h1>{t.title}</h1>
              <p className="lede">{t.sub}</p>
              <p className="try">{x.tryA}</p>
              <div className="examples">{x.ex.map((e, i) => <button key={i} onClick={() => send({ text: e }, e)}>{e}</button>)}</div>
              <details className="how"><summary>{x.howTitle}</summary><p>{x.how}</p></details>
            </div>
          ) : (
            <div className="log" aria-live="polite">
              {log.map((m, i) => <div key={i} className={"msg " + m.who}>{m.text}</div>)}
              {q && q.affects && q.affects.length > 0 && <p className="why"><strong>{x.why}</strong> {q.affects.slice(0, 3).join("; ")}</p>}
              {q && (
                <div className="answers">
                  {q.kind === "choice" && q.options.map((o, i) => (
                    <button key={i} disabled={busy} onClick={() => send({ answer: { slot: q.slot, value: o.value } }, o.label)}>{o.label}</button>))}
                  {q.kind === "multi" && <>
                    {q.options.map((o, i) => {
                      const on = sel.includes(o.value);
                      return <button key={i} className={"chip" + (on ? " on" : "")} aria-pressed={on}
                        onClick={() => setSel(on ? sel.filter((v) => v !== o.value) : [...sel, o.value])}>{o.label}</button>;
                    })}
                    <button className="primary" disabled={busy || !sel.length}
                      onClick={() => send({ answer: { slot: q.slot, value: sel } }, q.options.filter((o) => sel.includes(o.value)).map((o) => o.label).join(", "))}>{x.confirm}</button>
                  </>}
                  {!["law", "claimant", "needs"].includes(q.slot) && <button className="skip" disabled={busy} onClick={() => send({ answer: { slot: "skip", value: null } }, t.skipq)}>{t.skipq}</button>}
                </div>)}
              {busy && <div className="msg agent dots" aria-label={x.thinking}><i /><i /><i /></div>}
              {turn && turn.state === "advice" && view === "chat" && <button className="primary see" onClick={() => setView("case")}>{x.routes} ({A.remedies.length})</button>}
              {err && <p className="err" role="alert">{err}</p>}
              <div ref={end} />
            </div>)}
          <div className="composer">
            {asked > 0 && <span className="asked">{asked} {x.asked}</span>}
            <textarea rows={1} value={text} placeholder={x.placeholder} aria-label={x.placeholder}
              onChange={(e) => setText(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }} />
            <button className="primary" disabled={busy || !text.trim()} onClick={submit}>{t.send}</button>
          </div>
        </section>
        <Case t={t} x={x} turn={turn} onSend={send} busy={busy} places={places} setPlaces={setPlaces} />
      </main>
    </div>);
}
