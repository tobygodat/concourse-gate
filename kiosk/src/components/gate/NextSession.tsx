import type { Session } from "@concourse/web/src/types/schedules";
import { clockTime } from "@concourse/web/src/components/layout/format";
/** The live or next session in this room, so staff can answer "what's on next?". */
export function NextSession({ session, error }: { session: Session | null; error: string }) {
  return (
    <section className="panel">
      <h2>{session?.status === "live" ? "Now in this room" : "Next in this room"}</h2>
      {error && <p className="error">{error}</p>}
      {!session && !error && <p className="muted">Nothing else scheduled here.</p>}
      {session && (
        <div className="session">
          <strong>{session.title}</strong>
          <span className="muted">
            {session.speaker} · {clockTime(session.starts_at)} · {session.duration_minutes} min
          </span>
        </div>
      )}
    </section>
  );
}
