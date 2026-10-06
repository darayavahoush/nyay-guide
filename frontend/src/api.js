export async function agent(body) {
  const r = await fetch("/api/india/agent", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) {
    let d = ""; try { d = (await r.json()).detail; } catch (e) { /* not json */ }
    if (typeof d !== "string") d = "";
    throw new Error(r.status === 422 ? "Could not use that answer" + (d ? ": " + d : "") + ". Please try again or start over." : "Server error " + r.status + ". Please try again in a moment.");
  }
  return r.json();
}
