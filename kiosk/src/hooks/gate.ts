import { useCallback, useEffect, useState } from "react";
import { admitTicket } from "@concourse/web/src/client/checkins";
import type { Alert } from "@concourse/web/src/types/alerts";
import type { Checkin } from "@concourse/web/src/types/checkins";
import type { Session } from "@concourse/web/src/types/schedules";
import type { Ticket } from "@concourse/web/src/types/tickets";
import type { Venue } from "@concourse/web/src/types/venues";
import {
  fetchGateVenues,
  fetchRecentCheckins,
  fetchUpcomingSessions,
  findTicket,
  reportGateIssue,
} from "../client/gate";

/** Turn any thrown value into a message door staff can read. */
function message(cause: unknown) {
  return cause instanceof Error
    ? cause.message
    : "Unable to reach the Concourse operations API.";
}

/** Load gate venues with occupancy and expose a refresh after each admission. */
export function useGateVenues() {
  const [venues, setVenues] = useState<Venue[]>([]);
  const [error, setError] = useState("");
  const reload = useCallback(async () => {
    setError("");
    try {
      setVenues(await fetchGateVenues());
    } catch (cause) {
      setError(message(cause));
    }
  }, []);
  useEffect(() => {
    void reload();
  }, [reload]);
  return { venues, error, reload };
}

/** Load the most recent admissions into one venue, newest first. */
export function useRecentScans(venueId: string, limit = 8) {
  const [scans, setScans] = useState<Checkin[]>([]);
  const [error, setError] = useState("");
  const reload = useCallback(async () => {
    if (!venueId) return setScans([]);
    setError("");
    try {
      const all = await fetchRecentCheckins();
      setScans(
        all
          .filter((item) => item.venue_id === venueId)
          .sort((a, b) => b.checked_in_at.localeCompare(a.checked_in_at))
          .slice(0, limit),
      );
    } catch (cause) {
      setError(message(cause));
    }
  }, [venueId, limit]);
  useEffect(() => {
    void reload();
  }, [reload]);
  return { scans, error, reload };
}

/** Find the live or next upcoming session in the selected room. */
export function useNextSession(venueId: string) {
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setSession(null);
    setError("");
    if (!venueId) return;
    fetchUpcomingSessions(venueId)
      .then((sessions) => active && setSession(sessions[0] ?? null))
      .catch((cause) => active && setError(message(cause)));
    return () => {
      active = false;
    };
  }, [venueId]);
  return { session, error };
}

/** Admission workflow: preview a scanned ticket, then admit it via Concourse. */
export function useAdmission(venueId: string, onAdmitted: () => void) {
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [admitted, setAdmitted] = useState<Checkin | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const lookup = useCallback(async (ticketId: string) => {
    setBusy(true);
    setError("");
    setAdmitted(null);
    setTicket(null);
    try {
      setTicket(await findTicket(ticketId));
    } catch (cause) {
      setError(message(cause));
    } finally {
      setBusy(false);
    }
  }, []);

  const admit = useCallback(async () => {
    if (!ticket || !venueId) return;
    setBusy(true);
    setError("");
    try {
      setAdmitted(await admitTicket({ ticket_id: ticket.id, venue_id: venueId }));
      setTicket({ ...ticket, status: "used" });
      onAdmitted();
    } catch (cause) {
      setError(message(cause));
    } finally {
      setBusy(false);
    }
  }, [ticket, venueId, onAdmitted]);

  const clear = useCallback(() => {
    setTicket(null);
    setAdmitted(null);
    setError("");
  }, []);

  return { ticket, admitted, error, busy, lookup, admit, clear };
}

/** Post a gate issue alert and remember the last one raised from this door. */
export function useGateIssue() {
  const [sent, setSent] = useState<Alert | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const report = useCallback(
    async (title: string, severity: Alert["severity"]) => {
      setBusy(true);
      setError("");
      try {
        setSent(await reportGateIssue(title, severity));
      } catch (cause) {
        setError(message(cause));
      } finally {
        setBusy(false);
      }
    },
    [],
  );
  return { sent, error, busy, report };
}
