import type { Checkin } from "@concourse/web/src/types/checkins";
import { clockTime } from "@concourse/web/src/components/layout/format";
/** Latest admissions at this door so staff can spot re-entries at a glance. */
export function RecentScans({ scans, error }: { scans: Checkin[]; error: string }) {
  return (
    <section className="panel">
      <h2>Recent scans</h2>
      {error && <p className="error">{error}</p>}
      {!scans.length && !error && <p className="muted">No admissions here yet.</p>}
      <ul className="scans">
        {scans.map((scan) => (
          <li key={scan.id}>
            <span>{scan.attendee_name}</span>
            <span className="muted">{scan.ticket_id} · {clockTime(scan.checked_in_at)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
