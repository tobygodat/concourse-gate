import type { Checkin } from "@concourse/web/src/types/checkins";
import type { Ticket } from "@concourse/web/src/types/tickets";
import { clockTime } from "@concourse/web/src/components/layout/format";
/** Ticket holder preview with an Admit action, plus the admission outcome or error. */
export function ScanResult({
  ticket,
  admitted,
  error,
  busy,
  onAdmit,
  onClear,
}: {
  ticket: Ticket | null;
  admitted: Checkin | null;
  error: string;
  busy: boolean;
  onAdmit: () => void;
  onClear: () => void;
}) {
  if (!ticket && !error) {
    return <div className="result idle">Waiting for a ticket scan…</div>;
  }
  const tone = admitted ? "ok" : error ? "bad" : ticket?.status === "valid" ? "ready" : "warn";
  return (
    <div className={`result ${tone}`} role="status">
      {ticket && (
        <div className="holder">
          <span className="holder-name">{ticket.attendee_name}</span>
          <span className="holder-meta">
            {ticket.id} · {ticket.tier.toUpperCase()} · {ticket.status}
          </span>
        </div>
      )}
      {admitted && (
        <p className="verdict">Admitted at {clockTime(admitted.checked_in_at)}</p>
      )}
      {error && <p className="verdict">{error}</p>}
      <div className="result-actions">
        {ticket && !admitted && (
          <button className="primary big" onClick={onAdmit} disabled={busy}>
            {busy ? "Admitting…" : "Admit"}
          </button>
        )}
        <button onClick={onClear} disabled={busy}>Next guest</button>
      </div>
    </div>
  );
}
