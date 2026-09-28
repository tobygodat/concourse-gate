import type { Venue } from "@concourse/web/src/types/venues";
/** Large touch buttons for choosing which venue this door admits into, with live fill. */
export function VenuePicker({
  venues,
  selected,
  onSelect,
}: {
  venues: Venue[];
  selected: string;
  onSelect: (venueId: string) => void;
}) {
  return (
    <div className="venue-grid" role="radiogroup" aria-label="Gate venue">
      {venues.map((venue) => {
        const full = venue.occupancy >= venue.capacity;
        const pct = Math.min(100, Math.round((venue.occupancy / venue.capacity) * 100));
        return (
          <button
            key={venue.id}
            role="radio"
            aria-checked={venue.id === selected}
            className={`venue${venue.id === selected ? " is-selected" : ""}${full ? " is-full" : ""}`}
            onClick={() => onSelect(venue.id)}
          >
            <span className="venue-name">{venue.name}</span>
            <span className="venue-zone">{venue.zone}</span>
            <span className="meter"><span style={{ width: `${pct}%` }} /></span>
            <span className="venue-count">
              {venue.occupancy} / {venue.capacity}
              {full ? " · FULL" : ""}
            </span>
          </button>
        );
      })}
    </div>
  );
}
