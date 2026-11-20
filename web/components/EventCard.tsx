"use client";

import { motion } from "motion/react";
import type { EventItem } from "@/lib/api";
import { dayAndMonth, daysBetween, formatWhen } from "@/lib/dates";
import { usePlans } from "./PlansProvider";

export type Sticker = { text: string; tone: "yellow" | "accent" | "grey" };

// The tilted label in the card's corner. Only one, in order of importance.
export function stickerFor(event: EventItem, today: string): Sticker | null {
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

// The day an event belongs to on the page: today for things already running, otherwise its start day
export function displayDate(event: EventItem, today: string): string | null {
  if (event.start_date && event.start_date < today) return today;
  return event.start_date ?? event.end_date;
}

type Props = {
  event: EventItem;
  today: string;
  onOpen: (event: EventItem) => void;
};

export default function EventCard({ event, today, onOpen }: Props) {
  const date = displayDate(event, today);
  const stamp = date ? dayAndMonth(date) : null;
  const sticker = stickerFor(event, today);
  const isPromo = event.category === "bookstore_promo";
  const plan = usePlans().statusOf(event); // only ever set when the plans are unlocked

  return (
    // layoutId lets this card grow smoothly into the details window when clicked
    <motion.article
      layoutId={`event-${event.id}`}
      className="card-hover relative grid h-full grid-cols-[auto_1fr] items-start gap-4 rounded-2xl border-[1.5px] border-line bg-surface p-4"
    >
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
        <h3 className="font-display text-lg font-semibold leading-tight">
          {/* The whole card is clickable: this button stretches over it (see the after: classes) */}
          <button
            type="button"
            id={`card-${event.id}`}
            onClick={() => onOpen(event)}
            className="text-left after:absolute after:inset-0 after:rounded-2xl after:content-['']"
          >
            {event.title}
          </button>
        </h3>
        <div className="mt-1.5 grid gap-0.5 text-sm text-muted">
          {/* Promos: dates, then the offer. Events: their details already include the day and time. */}
          {isPromo && <span>{formatWhen(event, today)}</span>}
          {event.details && <span className="line-clamp-2">{event.details}</span>}
          {event.location && <span className="line-clamp-1">{event.location}</span>}
          <span>
            {plan && <span className={`plan-chip plan-chip-${plan} mr-2`}>{plan === "going" ? "✓ Going" : "★ Want"}</span>}
            <span className="font-semibold text-ink">{event.source}</span>
            {event.topic && ` · ${event.topic}`}
            {event.link && (
              <>
                {" · "}
                {/* relative z-10 keeps this link clickable above the stretched button */}
                <a
                  href={event.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="relative z-10 font-semibold text-accent underline-offset-2 hover:underline"
                >
                  Open ↗
                </a>
              </>
            )}
          </span>
        </div>
      </div>
    </motion.article>
  );
}