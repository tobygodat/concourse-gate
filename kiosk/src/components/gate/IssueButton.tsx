import type { Alert } from "@concourse/web/src/types/alerts";
import type { Venue } from "@concourse/web/src/types/venues";
import { useGateIssue } from "../../hooks/gate";

const ISSUES: { label: string; title: string; severity: Alert["severity"] }[] = [
  { label: "Crowding", title: "Crowding at the door", severity: "warning" },
  { label: "Door problem", title: "Door or scanner problem", severity: "critical" },
];

/** One-tap buttons that raise a crowding or door-problem alert for the ops team. */
export function IssueButton({ venue }: { venue: Venue | undefined }) {
  const { sent, error, busy, report } = useGateIssue();
  return (
    <section className="panel">
      <h2>Report an issue</h2>
      <div className="issue-row">
        {ISSUES.map((issue) => (
          <button
            key={issue.label}
            className={`issue ${issue.severity}`}
            disabled={busy || !venue}
            onClick={() => void report(`${issue.title}: ${venue?.name}`, issue.severity)}
          >
            {issue.label}
          </button>
        ))}
      </div>
      {sent && <p className="muted">Sent: {sent.title}</p>}
      {error && <p className="error">{error}</p>}
    </section>
  );
}
