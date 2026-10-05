export async function agent(body) {
  const r = await fetch("/api/india/agent", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(r.status === 422 ? "Invalid input" : "Server error " + r.status);
  return r.json();
}
