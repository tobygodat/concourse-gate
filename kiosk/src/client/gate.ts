import { responseError } from "@concourse/web/src/client/errors";
import type { Alert } from "@concourse/web/src/types/alerts";
import type { Checkin } from "@concourse/web/src/types/checkins";
import type { Session } from "@concourse/web/src/types/schedules";
import type { Ticket } from "@concourse/web/src/types/tickets";
import type { Venue } from "@concourse/web/src/types/venues";
import { GATE_API } from "../config";

/** Load the venues a door can admit into, with live occupancy. */
export async function fetchGateVenues(): Promise<Venue[]> {
  const response = await fetch(`${GATE_API}/venues`);
  if (!response.ok) throw await responseError(response);
  return response.json();
}

/** Look up a scanned ticket ID so staff can preview the holder before admitting. */
export async function findTicket(id: string): Promise<Ticket> {
  const response = await fetch(`${GATE_API}/tickets`);
  if (!response.ok) throw await responseError(response);
  const tickets: Ticket[] = await response.json();
  const needle = id.trim().toLowerCase();
  const ticket = tickets.find((item) => item.id.toLowerCase() === needle);
  if (!ticket) throw new Error(`No ticket found for "${id.trim()}".`);
  return ticket;
}

/** List the live and upcoming sessions in one venue, soonest first. */
export async function fetchUpcomingSessions(venueId: string): Promise<Session[]> {
  const response = await fetch(`${GATE_API}/schedules`);
  if (!response.ok) throw await responseError(response);
  const sessions: Session[] = await response.json();
  return sessions
    .filter((item) => item.venue_id === venueId && item.status !== "completed")
    .sort((a, b) => a.starts_at.localeCompare(b.starts_at));
}

/** Raise a door-side problem (crowding, broken door) as a Concourse alert. */
export async function reportGateIssue(
  title: string,
  severity: Alert["severity"],
): Promise<Alert> {
  const response = await fetch(`${GATE_API}/alerts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, severity, source: "gate-kiosk" }),
  });
  if (!response.ok) throw await responseError(response);
  return response.json();
}

/** Read all admissions so the kiosk can show the latest scans at its door. */
export async function fetchRecentCheckins(): Promise<Checkin[]> {
  const response = await fetch(`${GATE_API}/checkins`);
  if (!response.ok) throw await responseError(response);
  return response.json();
}
