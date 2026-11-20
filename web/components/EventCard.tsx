import type { EventItem } from "@/lib/api";
import { dayAndMonth, daysBetween, formatWhen } from "@/lib/dates";

type Sticker = { text: string; tone: "yellow" | "accent" | "grey" };

// The tilted label in the card's corner. Only one, in order of importance.
function stickerFor(event: EventItem, today: string): Sticker | null {
  const details = event.details ?? "";
  if (/sold out/i.test(details)) return { text: "Sold out", tone: "grey" };
  if (event.is_new) return { text: "NEW!", tone: "yellow" };

  if (event.category === "bookstore_promo") {
    if (!event.end_date) return null;
    const left = daysBetween(today, event.end_date);
    if (left === 0) return { text: "Ends today!", tone: "accent" };
    if (left === 1) return { text: "Ends tomorrow", tone: "accent" };
    if (left > 1 && left <= 3) return { text: `Ends in ${left} days`, tone: "accent" };
    return null;
  }

  if (event.start_date) {
    const until = daysBetween(today, event.start_date);
    if (until === 0) return { text: "Today!", tone: "accent" };
    if (until < 0) return { text: "On now", tone: "accent" };
    if (until === 1) return { text: "Tomorrow!", tone: "yellow" };
  }
  if (/\bfree\b/i.test(details)) return { text: "Free", tone: "yellow" };
  return null;
}

export default function EventCard({ event, today }: { event: EventItem; today: string }) {
  // The date stamp shows today for things already running, otherwise the start day
  const running = event.start_date !== null && event.start_date < today;
  const stampDate = running ? today : (event.start_date ?? event.end_date);
  const stamp = stampDate ? dayAndMonth(stampDate) : null;
  const sticker = stickerFor(event, today);
  const isPromo = event.category === "bookstore_promo";

  return (
    <article className="relative grid grid-cols-[auto_1fr] items-start gap-4 rounded-2xl border-[1.5px] border-line bg-surface p-4">
      {sticker && <span className={`sticker sticker-${sticker.tone}`}>{sticker.text}</span>}

      <div className="stamp">
        {stamp ? (
          <>
            <span className="stamp-day">{stamp.day}</span>
            <span className="stamp-month">{stamp.month}</span>
          </>
        ) : (
          <span className="stamp-month py-2">Now</span>
        )}
      </div>

      <div className="min-w-0">
        <h3 className="font-display text-lg font-semibold leading-tight">{event.title}</h3>
        <div className="mt-1.5 grid gap-0.5 text-sm text-muted">
          {/* Promos: dates, then the offer. Events: their details already include the day and time. */}
          {isPromo && <span>{formatWhen(event, today)}</span>}
          {event.details && <span>{event.details}</span>}
          {event.location && <span>{event.location}</span>}
          <span>
            <span className="font-semibold text-ink">{event.source}</span>
            {event.topic && ` · ${event.topic}`}
            {event.link && (
              <>
                {" · "}
                <a href={event.link} target="_blank" rel="noopener noreferrer" className="font-semibold text-accent underline-offset-2 hover:underline">
                  Open ↗
                </a>
              </>
            )}
          </span>
        </div>
      </div>
    </article>
  );
}