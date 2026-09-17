import { formatDateTime } from "@/lib/format";
import { Badge } from "@/components/ui/badge";

export type AuditEvent = {
  id: string;
  at: string;
  actor: string;
  action: string;
  verified?: boolean;
};

export function AuditTimeline({
  events,
  timeZone,
}: {
  events: AuditEvent[];
  timeZone?: string;
}) {
  return (
    <ol className="flex flex-col">
      {events.map((event) => (
        <li key={event.id} className="grid grid-cols-[7rem_1fr] gap-3 border-b border-subtle py-2 last:border-0">
          <time className="type-timestamp text-audit-historical" dateTime={event.at}>
            {formatDateTime(event.at, timeZone)}
          </time>
          <div>
            <p className="type-body">{event.action}</p>
            <p className="type-meta text-audit-immutable">{event.actor}</p>
            {event.verified ? <Badge tone="normal">Verified</Badge> : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
