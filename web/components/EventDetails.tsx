"use client";

import { useEffect, useRef } from "react";
import { motion } from "motion/react";
import type { EventItem } from "@/lib/api";
import { formatWhen } from "@/lib/dates";
import { stickerFor } from "./EventCard";

type Props = {
  event: EventItem;
  today: string;
  onClose: () => void;
};

// The bigger card that opens when an event is clicked
export default function EventDetails({ event, today, onClose }: Props) {
  const closeButton = useRef<HTMLButtonElement>(null);
  const sticker = stickerFor(event, today);
  const isPromo = event.category === "bookstore_promo";

  useEffect(() => {
    closeButton.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden"; // stop the page behind from scrolling
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
      // put the keyboard focus back on the card that was opened
      document.getElementById(`card-${event.id}`)?.focus({ preventScroll: true });
    };
  }, [onClose, event.id]);

  return (
    <motion.div
      className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        layoutId={`event-${event.id}`}
        data-tab={event.category}
        role="dialog"
        aria-modal="true"
        aria-labelledby="event-details-title"
        onClick={(e) => e.stopPropagation()}
        className="relative max-h-full w-full max-w-lg overflow-y-auto rounded-3xl border-2 border-accent bg-surface p-6 sm:p-8"
      >
        <button
          ref={closeButton}
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute right-4 top-4 grid h-9 w-9 place-items-center rounded-full bg-surface-2 text-lg hover:bg-line"
        >
          ×
        </button>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }}>
          {sticker && <span className={`sticker sticker-inline sticker-${sticker.tone}`}>{sticker.text}</span>}
          <p className="text-xs font-semibold uppercase tracking-[0.1em] text-accent">{event.source}</p>
          <h2 id="event-details-title" className="mt-1 pr-10 font-display text-2xl font-semibold leading-tight sm:text-3xl">
            {event.title}
          </h2>

          <dl className="mt-5 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
            {/* Events already have the day and time in their details, so "When" is only needed for promos */}
            {(isPromo || !event.details) && (
              <>
                <dt className="text-muted">When</dt>
                <dd>{formatWhen(event, today) || "See the event page"}</dd>
              </>
            )}
            {event.details && (
              <>
                <dt className="text-muted">Details</dt>
                <dd>{event.details}</dd>
              </>
            )}
            {event.location && (
              <>
                <dt className="text-muted">Where</dt>
                <dd>{event.location}</dd>
              </>
            )}
            {event.topic && (
              <>
                <dt className="text-muted">Topic</dt>
                <dd>{event.topic}</dd>
              </>
            )}
          </dl>

          {event.link && (
            <a
              href={event.link}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-6 inline-flex items-center gap-2 rounded-xl bg-accent px-4 py-2.5 font-semibold text-on-accent transition-transform hover:-translate-y-0.5"
            >
              Open on {event.source} ↗
            </a>
          )}
        </motion.div>
      </motion.div>
    </motion.div>
  );
}