// Date helpers. Event dates come from the API as plain days like "2026-11-20" (Malaysia time).
import type { EventItem } from "./api";

// Today's date in Malaysia as "2026-11-20", whatever time zone the visitor's computer is in
export function todayInMalaysia(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kuala_Lumpur" }).format(new Date());
}

// Whole days from one date to another: daysBetween("2026-11-20", "2026-11-22") is 2
export function daysBetween(from: string, to: string): number {
  return Math.round((Date.parse(`${to}T00:00:00Z`) - Date.parse(`${from}T00:00:00Z`)) / 86_400_000);
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function dayAndMonth(value: string) {
  const d = new Date(`${value}T00:00:00Z`);
  return { day: d.getUTCDate(), month: MONTHS[d.getUTCMonth()] };
}

// "Fri 20 Nov", with the year added only when it isn't this year
export function formatDay(value: string, today: string) {
  const d = new Date(`${value}T00:00:00Z`);
  return d.toLocaleDateString("en-MY", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: value.slice(0, 4) === today.slice(0, 4) ? undefined : "numeric",
    timeZone: "UTC",
  });
}

export function formatWhen(event: EventItem, today: string) {
  const { start_date: start, end_date: end } = event;
  if (!start) return end ? `Until ${formatDay(end, today)}` : "";
  if (!end || end === start) return formatDay(start, today);
  return `${formatDay(start, today)} to ${formatDay(end, today)}`;
}

export function formatTimestamp(value: string) {
  return new Date(value).toLocaleString("en-MY", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "Asia/Kuala_Lumpur",
  });
}