"use client";

import { useState, type MouseEvent, type ReactNode } from "react";
import {
  DndContext,
  DragOverlay,
  MouseSensor,
  TouchSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { AnimatePresence, motion } from "motion/react";
import type { EventItem, Plan, PlanStatus } from "@/lib/api";
import { formatDay } from "@/lib/dates";
import { usePlans } from "./PlansProvider";

type Props = {
  events: EventItem[]; // every event on the site, to open the details window
  today: string;
  onOpen: (event: EventItem) => void;
};

const COLUMNS: { id: PlanStatus; title: string; empty: string }[] = [
  { id: "want", title: "Want to go", empty: "Open any event and press Want, or drag one here." },
  { id: "going", title: "Going!", empty: "Drag a plan here once you've decided." },
];

const keyOf = (plan: Plan) => `${plan.source}|${plan.title_key}`;

type CardProps = { plan: Plan; event?: EventItem; today: string; onOpen?: (event: EventItem) => void; dragging?: boolean };

function PlanCard({ plan, event, today, onOpen, dragging = false }: CardProps) {
  const { setPlan } = usePlans();
  // The plan only remembers the start day; the event (if it's still listed) knows when it ends
  const lastDay = event?.end_date ?? plan.start_date;
  const past = lastDay !== null && lastDay < today;
  const onNow = !past && plan.start_date !== null && plan.start_date < today;
  const other: PlanStatus = plan.status === "want" ? "going" : "want";

  return (
    <div
      data-tab={plan.category ?? undefined}
      className={`relative rounded-2xl border-[1.5px] border-line bg-surface py-3 pl-5 pr-3 ${
        dragging ? "rotate-[-2deg] scale-[1.03] border-accent shadow-xl" : ""
      } ${past ? "opacity-60" : ""}`}
    >
      {/* a stripe in the event's tab colour */}
      <span className="absolute inset-y-3 left-2 w-1 rounded-full bg-accent" aria-hidden="true" />
      <p className="text-xs font-semibold uppercase tracking-[0.08em] text-accent">
        {onNow ? "On now" : plan.start_date ? formatDay(plan.start_date, today) : "No date"}
        {past && " · past"}
      </p>
      {dragging ? (
        <p className="mt-0.5 font-display font-semibold leading-tight">{plan.title}</p>
      ) : event && onOpen ? (
        <button type="button" onClick={() => onOpen(event)} className="mt-0.5 text-left font-display font-semibold leading-tight hover:underline">
          {plan.title}
        </button>
      ) : plan.link ? (
        <a href={plan.link} target="_blank" rel="noopener noreferrer" className="mt-0.5 block font-display font-semibold leading-tight hover:underline">
          {plan.title} ↗
        </a>
      ) : (
        <p className="mt-0.5 font-display font-semibold leading-tight">{plan.title}</p>
      )}
      <div className="mt-2 flex items-center gap-3 text-sm">
        <span className="text-muted">{plan.source}</span>
        <button
          type="button"
          onClick={(e) => setPlan(plan, other, other === "going" ? originFromEvent(e) : undefined)}
          className="ml-auto font-semibold text-accent hover:underline"
        >
          {other === "going" ? "Move to Going →" : "← Back to Want"}
        </button>
        <button
          type="button"
          onClick={() => setPlan(plan, null)}
          aria-label={`Remove ${plan.title}`}
          className="grid h-7 w-7 place-items-center rounded-full text-muted hover:bg-surface-2 hover:text-ink"
        >
          ×
        </button>
      </div>
    </div>
  );
}

function originFromEvent(e: MouseEvent) {
  return { x: e.clientX / window.innerWidth, y: e.clientY / window.innerHeight };
}

// One plan you can pick up and drop in the other column
function DraggablePlan({ plan, children }: { plan: Plan; children: ReactNode }) {
  const { setNodeRef, listeners, isDragging } = useDraggable({ id: keyOf(plan), data: plan });
  return (
    <motion.li
      ref={setNodeRef}
      {...listeners}
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: isDragging ? 0.35 : 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ type: "spring", stiffness: 420, damping: 32 }}
      className="cursor-grab touch-manipulation active:cursor-grabbing"
    >
      {children}
    </motion.li>
  );
}

function Column({ id, title, empty, children, count }: { id: PlanStatus; title: string; empty: string; children: ReactNode; count: number }) {
  const { setNodeRef, isOver } = useDroppable({ id });
  return (
    <section
      ref={setNodeRef}
      aria-label={title}
      className={`min-h-64 rounded-3xl border-2 border-dashed p-4 transition-colors ${
        isOver ? "border-ink bg-surface-2" : "border-line"
      }`}
    >
      <h3 className="flex items-center gap-2 font-display text-xl font-semibold">
        {title}
        <span className="rounded-full bg-surface-2 px-2 text-sm text-muted">{count}</span>
      </h3>
      {count === 0 && <p className="mt-3 text-sm text-muted">{empty}</p>}
      <ul className="mt-3 grid gap-3">{children}</ul>
    </section>
  );
}

// The Want / Going board on the "My plans" tab
export default function PlansBoard({ events, today, onOpen }: Props) {
  const { plans, setPlan } = usePlans();
  const [active, setActive] = useState<Plan | null>(null);

  // A mouse drag starts after moving 6px; a finger has to hold for 0.2s, so normal scrolling still works
  const sensors = useSensors(
    useSensor(MouseSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 200, tolerance: 6 } }),
  );

  const eventFor = (plan: Plan) => events.find((e) => e.source === plan.source && e.title_key === plan.title_key);

  function handleDragEnd({ active: dragged, over }: DragEndEvent) {
    setActive(null);
    const plan = dragged.data.current as Plan | undefined;
    const target = over?.id as PlanStatus | undefined;
    if (!plan || !target || target === plan.status) return;
    // burst the confetti from where the card was dropped
    const box = dragged.rect.current.translated;
    const origin = box
      ? { x: (box.left + box.width / 2) / window.innerWidth, y: (box.top + box.height / 2) / window.innerHeight }
      : undefined;
    setPlan(plan, target, origin);
  }

  return (
    <DndContext
      sensors={sensors}
      onDragStart={({ active: dragged }) => setActive(dragged.data.current as Plan)}
      onDragEnd={handleDragEnd}
      onDragCancel={() => setActive(null)}
    >
      <p className="mb-4 text-muted">Drag plans between the columns, or use the buttons. Only you can see this tab.</p>
      <div className="grid gap-5 md:grid-cols-2">
        {COLUMNS.map((column) => {
          const items = plans.filter((p) => p.status === column.id);
          return (
            <Column key={column.id} {...column} count={items.length}>
              <AnimatePresence initial={false}>
                {items.map((plan) => (
                  <DraggablePlan key={keyOf(plan)} plan={plan}>
                    <PlanCard plan={plan} event={eventFor(plan)} today={today} onOpen={onOpen} />
                  </DraggablePlan>
                ))}
              </AnimatePresence>
            </Column>
          );
        })}
      </div>

      {/* The copy that follows the pointer while dragging */}
      <DragOverlay dropAnimation={null}>{active ? <PlanCard plan={active} event={eventFor(active)} today={today} dragging /> : null}</DragOverlay>
    </DndContext>
  );
}