import { useCallback, useState } from "react";
import { IssueButton } from "../components/gate/IssueButton";
import { NextSession } from "../components/gate/NextSession";
import { RecentScans } from "../components/gate/RecentScans";
import { ScanForm } from "../components/gate/ScanForm";
import { ScanResult } from "../components/gate/ScanResult";
import { VenuePicker } from "../components/gate/VenuePicker";
import { useAdmission, useGateVenues, useNextSession, useRecentScans } from "../hooks/gate";
/** Door-staff flow: pick a venue, scan a ticket, preview the holder, admit, repeat. */
export function GatePage() {
  const [venueId, setVenueId] = useState("");
  const venues = useGateVenues();
  const recent = useRecentScans(venueId);
  const next = useNextSession(venueId);
  const { reload: reloadVenues } = venues;
  const { reload: reloadScans } = recent;
  const refresh = useCallback(() => {
    void reloadVenues();
    void reloadScans();
  }, [reloadVenues, reloadScans]);
  const admission = useAdmission(venueId, refresh);
  const venue = venues.venues.find((item) => item.id === venueId);

  return (
    <main className="gate">
      <section className="panel">
        <h2>Gate venue</h2>
        {venues.error && <p className="error">{venues.error}</p>}
        <VenuePicker
          venues={venues.venues}
          selected={venueId}
          onSelect={(id) => {
            setVenueId(id);
            admission.clear();
          }}
        />
      </section>
      {venue ? (
        <>
          <section className="panel scan">
            <h2>Scanning into {venue.name}</h2>
            <ScanForm disabled={admission.busy} onScan={(id) => void admission.lookup(id)} />
            <ScanResult
              ticket={admission.ticket}
              admitted={admission.admitted}
              error={admission.error}
              busy={admission.busy}
              onAdmit={() => void admission.admit()}
              onClear={admission.clear}
            />
          </section>
          <div className="side">
            <NextSession session={next.session} error={next.error} />
            <RecentScans scans={recent.scans} error={recent.error} />
            <IssueButton venue={venue} />
          </div>
        </>
      ) : (
        <p className="muted pick-hint">Choose the venue this door admits into to start scanning.</p>
      )}
    </main>
  );
}
