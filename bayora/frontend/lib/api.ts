const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Ev = { idx: number; ts: string; subject: string; action: string; resource: string;
                   decision: "ALLOW" | "DENY"; note: string; prev_hash: string; hash: string };

async function j<T>(p: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + p, { headers: { "Content-Type": "application/json" }, ...init });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}
export const api = {
  create: () => j<{ id: string }>("/sessions", { method: "POST" }),
  act: (id: string, subject: string, action: string, resource: string, payload = "") =>
    j<{ decision: string; reason: string; output: string | null }>(`/sessions/${id}/actions`,
      { method: "POST", body: JSON.stringify({ subject, action, resource, payload }) }),
  events: (id: string) => j<Ev[]>(`/sessions/${id}/events`),
  verify: (id: string) => j<{ intact: boolean; first_broken_event: number | null }>(`/sessions/${id}/verify`),
  report: (id: string) => j<Record<string, unknown>>(`/sessions/${id}/report`),
  tamper: (id: string, idx: number) => j(`/dev/tamper/${id}/${idx}`, { method: "POST" }),
  close: (id: string) => j(`/sessions/${id}`, { method: "DELETE" }),
};
