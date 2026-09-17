import type { Alert } from "@/types/operational";
import { formatTimestamp } from "@/lib/format";

export function EventTimeline({
  alerts,
  timeZone,
}: {
  alerts: Alert[];
  timeZone?: string;
}) {
  const events = [...alerts].sort(
    (a, b) => Date.parse(b.observedAt) - Date.parse(a.observedAt),
  );

  return (
    <section aria-labelledby="events-heading">
      <h2 id="events-heading" className="type-panel mb-2">
        Event stream
      </h2>
      <ol>
        {events.map((event) => (
          <li
            key={event.id}
            className="grid grid-cols-[6.5rem_2.5rem_minmax(0,1fr)] items-baseline gap-2 border-b border-subtle py-1.5 last:border-0"
          >
            <time className="type-timestamp" dateTime={event.observedAt}>
              {formatTimestamp(event.observedAt, timeZone)}
            </time>
            <span className="type-ident text-muted">{event.priority}</span>
            <p className="type-body">
              <span className="type-ident text-secondary">{event.asset} </span>
              {event.title}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}
