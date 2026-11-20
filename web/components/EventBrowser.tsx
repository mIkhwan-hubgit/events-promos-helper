"use client";

import { useEffect, useState } from "react";
import {
  CATEGORIES,
  getEvents,
  getWatchlist,
  refreshCategory,
  type CategoryEvents,
  type CategoryId,
  type WatchItem,
} from "@/lib/api";
import { formatTimestamp, todayInMalaysia } from "@/lib/dates";
import { TabIcon } from "./Doodles";
import EventCard from "./EventCard";

type Loaded = {
  events: Partial<Record<CategoryId, CategoryEvents>>;
  watchlist: WatchItem[];
  today: string;
};

// Load every tab at once, so switching tabs is instant
async function loadEverything(): Promise<Loaded> {
  const [results, watchlist] = await Promise.all([
    Promise.all(CATEGORIES.map((c) => getEvents(c.id))),
    getWatchlist(),
  ]);
  return {
    events: Object.fromEntries(results.map((r) => [r.category, r])),
    watchlist,
    today: todayInMalaysia(),
  };
}

export default function EventBrowser() {
  const [tab, setTab] = useState<CategoryId>("orchestra");
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false; // ignore the answer if the page has gone away meanwhile
    loadEverything()
      .then((result) => {
        if (!cancelled) setLoaded(result);
      })
      .catch(() => {
        if (!cancelled) setLoadError("Couldn't reach the API. Is it running on port 8000?");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    setMessages([]);
    try {
      setMessages(await refreshCategory(tab));
      setLoaded(await loadEverything());
    } catch (error) {
      setMessages([error instanceof Error ? error.message : String(error)]);
    } finally {
      setRefreshing(false);
    }
  }

  const current = loaded?.events[tab];

  return (
    <section data-tab={tab} className="mt-10">
      <div role="tablist" aria-label="Event categories" className="flex gap-1 overflow-x-auto rounded-full border-[1.5px] border-line bg-surface p-1.5">
        {CATEGORIES.map((c) => (
          <button
            key={c.id}
            type="button"
            role="tab"
            data-tab={c.id}
            aria-selected={tab === c.id}
            onClick={() => {
              setTab(c.id);
              setMessages([]);
            }}
            className={`flex shrink-0 items-center gap-2 rounded-full px-4 py-2 font-display font-medium transition-colors ${
              tab === c.id ? "bg-accent text-on-accent" : "hover:bg-surface-2"
            }`}
          >
            <span className={tab === c.id ? "" : "text-accent"}>
              <TabIcon category={c.id} />
            </span>
            {c.label}
          </button>
        ))}
      </div>

      {loadError && <p className="mt-6 rounded-xl border-[1.5px] border-line bg-surface p-4">{loadError}</p>}

      {!loaded && !loadError && (
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-label="Loading events">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-36 animate-pulse rounded-2xl bg-surface-2" />
          ))}
        </div>
      )}

      {current && loaded && (
        <>
          <div className="mt-6 flex flex-wrap items-center gap-x-4 gap-y-2">
            <button
              type="button"
              onClick={handleRefresh}
              disabled={refreshing || current.next_refresh_at !== null}
              className="rounded-xl bg-accent px-4 py-2 font-semibold text-on-accent transition-opacity disabled:opacity-40"
            >
              {refreshing ? "Checking sources..." : "Refresh"}
            </button>
            <span className="text-sm text-muted">
              {current.refreshed_at ? `Last refreshed ${formatTimestamp(current.refreshed_at)}` : "Never refreshed"}
              {current.next_refresh_at && ` · next refresh after ${formatTimestamp(current.next_refresh_at)}`}
            </span>
            <span className="text-sm text-muted sm:ml-auto">
              {current.events.length} {current.events.length === 1 ? "event" : "events"}
            </span>
          </div>

          {messages.map((m) => (
            <p key={m} className="mt-3 rounded-xl bg-surface-2 p-3 text-sm">
              {m}
            </p>
          ))}

          {current.events.length === 0 ? (
            <p className="mt-8 text-muted">Nothing here right now.</p>
          ) : (
            <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {current.events.map((event) => (
                <EventCard key={event.id} event={event} today={loaded.today} />
              ))}
            </div>
          )}

          {tab === "video_games" && loaded.watchlist.length > 0 && (
            <div className="mt-12">
              <h2 className="font-display text-2xl font-semibold">Watchlist</h2>
              <p className="mt-1 text-muted">Big yearly gaming events to check yourself.</p>
              <ul className="mt-4 grid gap-3 sm:grid-cols-2">
                {loaded.watchlist.map((item) => (
                  <li key={item.name} className="rounded-2xl border-[1.5px] border-line bg-surface p-4">
                    <span className="font-display text-lg font-semibold">{item.name}</span>
                    {item.note && <p className="text-sm text-muted">{item.note}</p>}
                    <p className="mt-2 flex gap-4 text-sm font-semibold text-accent">
                      <a href={item.search} target="_blank" rel="noopener noreferrer" className="hover:underline">
                        Google it ↗
                      </a>
                      {item.site && (
                        <a href={item.site} target="_blank" rel="noopener noreferrer" className="hover:underline">
                          Official site ↗
                        </a>
                      )}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  );
}