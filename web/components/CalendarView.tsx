"use client";

import { motion } from "motion/react";
import type { EventItem } from "@/lib/api";
import { displayDate } from "./EventCard";

type Props = {
  events: EventItem[];
  today: string;
  onOpen: (event: EventItem) => void;
};

const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];

const pad = (n: number) => String(n).padStart(2, "0");

// Up to three month grids, with each event shown on every day it runs
export default function CalendarView({ events, today, onOpen }: Props) {
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
                    <span className="font-semibold text-muted">{i + 1}</span>
                    {on.slice(0, 2).map((event) => (
                      <button
                        key={event.id}
                        type="button"
                        title={event.title}
                        onClick={() => onOpen(event)}
                        className="truncate rounded px-1 text-left text-[11px] leading-snug transition-colors hover:bg-accent hover:text-on-accent"
                        style={{ background: "color-mix(in srgb, var(--accent) 22%, var(--surface))" }}
                      >
                        {event.title}
                      </button>
                    ))}
                    {on.length > 2 && <span className="text-[11px] text-muted">+{on.length - 2} more</span>}
                  </div>
                );
              })}
            </div>
          </motion.section>
        );
      })}
    </div>
  );
}