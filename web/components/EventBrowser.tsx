"use client";

import { useEffect, useState } from "react";
import {
  CATEGORIES,
  getEvents,
  getWatchlist,
  refreshCategory,
  type CategoryEvents,
  type CategoryId,
  type EventItem,
  type WatchItem,
} from "@/lib/api";

// "2026-11-20" -> "Fri 20 Nov 2026". Dates are read as UTC so the day never shifts.
function formatDay(value: string) {
  return new Date(`${value}T00:00:00Z`).toLocaleDateString("en-MY", {
    weekday: "short", day: "numeric", month: "short", year: "numeric", timeZone: "UTC",
  });
}

function formatWhen(event: EventItem) {
  if (!event.start_date) return event.end_date ? `Until ${formatDay(event.end_date)}` : "";
  if (!event.end_date || event.end_date === event.start_date) return formatDay(event.start_date);
  return `${formatDay(event.start_date)} to ${formatDay(event.end_date)}`;
}

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString("en-MY", {
    day: "numeric", month: "short", hour: "numeric", minute: "2-digit", timeZone: "Asia/Kuala_Lumpur",
  });
}

export default function EventBrowser() {
  const [tab, setTab] = useState<CategoryId>("orchestra");
  const [data, setData] = useState<Partial<Record<CategoryId, CategoryEvents>>>({});
  const [watchlist, setWatchlist] = useState<WatchItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [messages, setMessages] = useState<string[]>([]);

  // Load every tab at once, so switching tabs is instant
  async function loadAll() {
    try {
      const results = await Promise.all(CATEGORIES.map((c) => getEvents(c.id)));
      setData(Object.fromEntries(results.map((r) => [r.category, r])));
      setWatchlist(await getWatchlist());
      setLoadError(null);
    } catch {
      setLoadError("Couldn't reach the API. Is it running on port 8000?");
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    setMessages([]);
    try {
      setMessages(await refreshCategory(tab));
      await loadAll();
    } catch (error) {
      setMessages([error instanceof Error ? error.message : String(error)]);
    } finally {
      setRefreshing(false);
    }
  }

  const current = data[tab];

  return (
    <section className="mt-8">
      <div className="flex flex-wrap gap-2" role="tablist">
        {CATEGORIES.map((c) => (
          <button
            key={c.id}
            role="tab"
            aria-selected={tab === c.id}
            onClick={() => { setTab(c.id); setMessages([]); }}
            className={`rounded-full border px-4 py-2 text-sm font-semibold ${
              tab === c.id ? "bg-neutral-900 text-white dark:bg-white dark:text-neutral-900" : "border-neutral-300 dark:border-neutral-700"
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {loadError && <p className="mt-6 rounded-lg bg-red-100 p-3 text-red-800">{loadError}</p>}

      {current && (
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <button
            onClick={handleRefresh}
            disabled={refreshing || current.next_refresh_at !== null}
            className="rounded-lg bg-orange-600 px-4 py-2 font-semibold text-white disabled:opacity-40"
          >
            {refreshing ? "Checking sources..." : "Refresh"}
          </button>
          <span className="text-sm text-neutral-500">
            {current.refreshed_at ? `Last refreshed ${formatTimestamp(current.refreshed_at)}` : "Never refreshed"}
            {current.next_refresh_at && ` · next refresh after ${formatTimestamp(current.next_refresh_at)}`}
          </span>
        </div>
      )}

      {messages.map((m) => (
        <p key={m} className="mt-3 rounded-lg bg-yellow-100 p-3 text-sm text-yellow-900">{m}</p>
      ))}

      {current && (
        <>
          <p className="mt-6 text-sm text-neutral-500">{current.events.length} events</p>
          <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {current.events.map((event) => (
              <article key={event.id} className="rounded-xl border border-neutral-200 p-4 dark:border-neutral-800">
                {event.is_new && <span className="text-xs font-bold text-orange-600">NEW</span>}
                <h3 className="font-semibold">{event.title}</h3>
                <p className="mt-1 text-sm">{formatWhen(event)}</p>
                {event.details && <p className="mt-1 text-sm text-neutral-500">{event.details}</p>}
                {event.location && <p className="mt-1 text-sm text-neutral-500">{event.location}</p>}
                <p className="mt-2 text-sm">
                  <span className="font-semibold">{event.source}</span>
                  {event.link && (
                    <> · <a href={event.link} target="_blank" rel="noopener noreferrer" className="underline">Open</a></>
                  )}
                </p>
              </article>
            ))}
          </div>
        </>
      )}

      {tab === "video_games" && watchlist.length > 0 && (
        <div className="mt-10">
          <h2 className="text-xl font-semibold">Watchlist</h2>
          <ul className="mt-3 grid gap-2">
            {watchlist.map((item) => (
              <li key={item.name} className="text-sm">
                <span className="font-semibold">{item.name}</span>
                {item.note && <span className="text-neutral-500"> · {item.note}</span>}
                {" · "}<a href={item.search} target="_blank" rel="noopener noreferrer" className="underline">Google it</a>
                {item.site && <> · <a href={item.site} target="_blank" rel="noopener noreferrer" className="underline">Official site</a></>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}