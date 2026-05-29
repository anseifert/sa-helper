import type { Dashboard } from "../api";

type Meeting = Dashboard["today_meetings"][number];

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function formatRange(start: string, end: string | null) {
  if (!end) return formatTime(start);
  return `${formatTime(start)} – ${formatTime(end)}`;
}

export default function TodayMeetingsWidget({
  meetings,
  error,
}: {
  meetings: Meeting[];
  error: string | null;
}) {
  return (
    <section className="bg-white border rounded-lg p-4 shadow-sm">
      <h2 className="text-xl font-semibold mb-1">Today&apos;s meetings</h2>
      <p className="text-sm text-gray-600 mb-3">
        Calendar events today with at least one attendee outside @redhat.com. Internal-only
        meetings are hidden.
      </p>

      {error && <p className="text-sm text-amber-700 mb-2">{error}</p>}

      {meetings.length === 0 && !error ? (
        <p className="text-sm text-gray-500">No external meetings on your calendar today.</p>
      ) : (
        <ul className="space-y-3">
          {meetings.map((m) => (
            <li
              key={m.event_id || m.start_at + m.title}
              className="border border-gray-100 rounded-lg p-3"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="font-medium">{m.title}</p>
                <span className="text-sm text-gray-600 shrink-0">
                  {formatRange(m.start_at, m.end_at)}
                </span>
              </div>
              <ul className="mt-2 text-xs text-gray-600 space-y-0.5">
                {m.external_emails.map((email) => (
                  <li key={email} className="font-mono truncate">
                    {email}
                  </li>
                ))}
              </ul>
              {m.html_link && (
                <a
                  href={m.html_link}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-block mt-2 text-xs text-rh-red hover:underline"
                >
                  Open in Google Calendar
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
