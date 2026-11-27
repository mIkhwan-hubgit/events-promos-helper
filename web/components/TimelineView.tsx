"use client";

import { motion } from "motion/react";
import type { EventItem } from "@/lib/api";
import { daysBetween, formatDay } from "@/lib/dates";
import { displayDate, stickerFor } from "./EventCard";
import { usePlans } from "./PlansProvider";

type Props = {
  events: EventItem[];
  today: string;
  onOpen: (event: EventItem) => void;
};

function relativeLabel(day: string, today: string) {
  const n = daysBetween(today, day);
  if (n === 0) return "Today";
  if (n === 1) return "Tomorrow";
  if (n > 1 && n < 7) return `In ${n} days`;
  return "";
}

// Events listed down a dotted line, grouped by day
export default function TimelineView({ events, today, onOpen }: Props) {
  const { statusOf } = usePlans();
  const groups = new Map<string, EventItem[]>();
  for (const event of events) {
    const day = displayDate(event, today) ?? today;
    groups.set(day, [...(groups.get(day) ?? []), event]);
  }
  const days = [...groups.keys()].sort();

  return (
    <div className="timeline relative grid grid-cols-1 gap-7 pl-8">
      {days.map((day) => (
        <motion.section
          key={day}
          className="timeline-day relative min-w-0"
          initial={{ opacity: 0, x: -16 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, amount: "some" }}
          transition={{ duration: 0.35 }}
        >
          <h3 className="font-display text-lg font-semibold">
            {formatDay(day, today)}
            <span className="ml-2 font-sans text-sm font-medium text-muted">{relativeLabel(day, today)}</span>
          </h3>
          <div className="mt-3 grid grid-cols-1 gap-2.5">
            {(groups.get(day) ?? []).map((event) => {
              const sticker = stickerFor(event, today);
              const plan = statusOf(event); // only set when signed in
              return (
                <button
                  key={event.id}
                  type="button"
                  onClick={() => onOpen(event)}
                  className="flex items-center justify-between gap-4 rounded-2xl border-[1.5px] border-line bg-surface px-4 py-3 text-left transition-[transform,border-color] hover:translate-x-1.5 hover:border-accent"
                >
                  <span className="min-w-0">
                    {/* The same stickers and Want / Going chips as on the cards */}
                    {(sticker || plan) && (
                      <span className="mb-1.5 flex flex-wrap items-center gap-1.5">
                        {sticker && <span className={`sticker sticker-mini sticker-${sticker.tone}`}>{sticker.text}</span>}
                        {plan && (
                          <span className={`plan-chip plan-chip-${plan}`}>{plan === "going" ? "✓ Going" : "★ Want"}</span>
                        )}
                      </span>
                    )}
                    <span className="block font-semibold">{event.title}</span>
                    <span className="block truncate text-sm text-muted">{event.location ?? event.details}</span>
                  </span>
                  <span className="shrink-0 text-sm font-semibold text-accent">{event.source}</span>
                </button>
              );
            })}
          </div>
        </motion.section>
      ))}
    </div>
  );
}