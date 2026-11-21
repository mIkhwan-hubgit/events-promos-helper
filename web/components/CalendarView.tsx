"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import type { EventItem } from "@/lib/api";
import { formatDay } from "@/lib/dates";
import { displayDate } from "./EventCard";
import { usePlans } from "./PlansProvider";

type Props = {
  events: EventItem[];
  today: string;
  onOpen: (event: EventItem) => void;
};

const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];

const pad = (n: number) => String(n).padStart(2, "0");

// A small window listing everything on one day
function DayList({ day, events, today, onPick, onClose }: {
  day: string;
  events: EventItem[];
  today: string;
  onPick: (event: EventItem) => void;
  onClose: () => void;
}) {
  const closeButton = useRef<HTMLButtonElement>(null);
  const { statusOf } = usePlans();

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    closeButton.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      opener?.focus({ preventScroll: true });
    };
  }, [onClose]);

  return (
    <motion.div
      className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-labelledby="day-list-title"
        onClick={(e) => e.stopPropagation()}
        initial={{ scale: 0.94, y: 12 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.96, opacity: 0 }}
        transition={{ type: "spring", stiffness: 420, damping: 32 }}
        className="relative flex max-h-full w-full max-w-md flex-col rounded-3xl border-2 border-accent bg-surface p-5 sm:p-6"
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
        <h2 id="day-list-title" className="pr-10 font-display text-2xl font-semibold">
          {formatDay(day, today)}
        </h2>
        <p className="text-sm text-muted">
          {events.length} {events.length === 1 ? "event" : "events"}
        </p>
        <ul className="mt-4 grid gap-2 overflow-y-auto">
          {events.map((event) => (
            <li key={event.id}>
              <button
                type="button"
                onClick={() => onPick(event)}
                className="w-full rounded-2xl border-[1.5px] border-line bg-bg px-4 py-3 text-left transition-colors hover:border-accent"
              >
                <span className="block font-semibold leading-snug">{event.title}</span>
                <span className="text-sm font-semibold text-accent">{event.source}</span>
                {statusOf(event) && (
                  <span className={`plan-chip plan-chip-${statusOf(event)} ml-2`}>
                    {statusOf(event) === "going" ? "✓ Going" : "★ Want"}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </motion.div>
    </motion.div>
  );
}

// Up to three month grids, with each event shown on every day it runs
export default function CalendarView({ events, today, onOpen }: Props) {
  const { statusOf } = usePlans();
  const [openDay, setOpenDay] = useState<string | null>(null);
  const closeDay = useCallback(() => setOpenDay(null), []);

  // Which months have something on (from today onwards), earliest first, at most three
  const monthKeys = [...new Set(events.map((e) => (displayDate(e, today) ?? today).slice(0, 7)))].sort().slice(0, 3);

  // Events running on a given day ("2026-11-20")
  const eventsOn = (iso: string) =>
    events.filter((e) => {
      const start = e.start_date ?? today;
      const end = e.end_date ?? start;
      return start <= iso && iso <= end && iso >= today;
    });

  return (
    <>
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {monthKeys.map((key, index) => {
          const [year, month] = key.split("-").map(Number);
          const firstWeekday = (new Date(Date.UTC(year, month - 1, 1)).getUTCDay() + 6) % 7; // Monday = 0
          const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate();

          return (
            <motion.section
              key={key}
              className="min-w-0 rounded-2xl border-[1.5px] border-line bg-surface p-4"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.35, delay: index * 0.08 }}
            >
              <h3 className="mb-3 font-display text-lg font-semibold">
                {MONTH_NAMES[month - 1]} {year}
              </h3>
              <div className="grid grid-cols-7 gap-1">
                {WEEKDAYS.map((d) => (
                  <div key={d} className="text-center text-[11px] font-bold uppercase tracking-wide text-muted">
                    {d}
                  </div>
                ))}
                {Array.from({ length: firstWeekday }, (_, i) => (
                  <div key={`blank-${i}`} />
                ))}
                {Array.from({ length: daysInMonth }, (_, i) => {
                  const iso = `${year}-${pad(month)}-${pad(i + 1)}`;
                  const on = eventsOn(iso);
                  return (
                    <div
                      key={iso}
                      className={`flex min-h-14 min-w-0 flex-col gap-0.5 rounded-lg bg-surface-2 p-1 text-xs ${
                        iso === today ? "outline-2 outline-accent" : ""
                      } ${iso < today ? "opacity-40" : ""}`}
                    >
                      {/* Tap the day number to see everything on that day */}
                      {on.length > 0 ? (
                        <button
                          type="button"
                          onClick={() => setOpenDay(iso)}
                          aria-label={`All ${on.length} events on ${formatDay(iso, today)}`}
                          className="self-start rounded px-0.5 font-semibold text-ink hover:bg-accent hover:text-on-accent"
                        >
                          {i + 1}
                        </button>
                      ) : (
                        <span className="font-semibold text-muted">{i + 1}</span>
                      )}
                      {on.slice(0, 2).map((event) => (
                        <button
                          key={event.id}
                          type="button"
                          title={event.title}
                          onClick={() => onOpen(event)}
                          className="truncate rounded px-1 text-left text-[11px] leading-snug transition-colors hover:bg-accent hover:text-on-accent"
                          style={{ background: "color-mix(in srgb, var(--accent) 22%, var(--surface))" }}
                        >
                          {/* a star or tick in front of events you've planned */}
                          {statusOf(event) === "going" ? "✓ " : statusOf(event) === "want" ? "★ " : ""}
                          {event.title}
                        </button>
                      ))}
                      {on.length > 2 && (
                        <button
                          type="button"
                          onClick={() => setOpenDay(iso)}
                          className="rounded px-0.5 text-left text-[11px] font-semibold text-accent hover:underline"
                        >
                          +{on.length - 2} more
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </motion.section>
          );
        })}
      </div>

      <AnimatePresence>
        {openDay && (
          <DayList
            day={openDay}
            events={eventsOn(openDay)}
            today={today}
            onClose={closeDay}
            onPick={(event) => {
              setOpenDay(null);
              onOpen(event);
            }}
          />
        )}
      </AnimatePresence>
    </>
  );
}