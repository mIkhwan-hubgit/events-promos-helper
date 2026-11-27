"use client";

import { useCallback, useEffect, useState, useSyncExternalStore } from "react";
import { AnimatePresence, MotionConfig, motion } from "motion/react";
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
import { formatTimestamp, todayInMalaysia } from "@/lib/dates";
import { getSavedTab, getSavedView, setSavedTab, setSavedView, subscribe } from "@/lib/session";
import CalendarView from "./CalendarView";
import { StarDoodle, TabIcon } from "./Doodles";
import EventCard from "./EventCard";
import EventDetails from "./EventDetails";
import EventsizeWatchlist from "./EventsizeWatchlist";
import PlansBoard from "./PlansBoard";
import { usePlans } from "./PlansProvider";
import TimelineView from "./TimelineView";

type Loaded = {
  events: Partial<Record<CategoryId, CategoryEvents>>;
  watchlist: WatchItem[];
  today: string;
};

// The five categories, plus "My plans" once unlocked
type TabId = CategoryId | "plans";

type View = "cards" | "timeline" | "calendar";
const VIEWS: { id: View; label: string }[] = [
  { id: "cards", label: "Cards" },
  { id: "timeline", label: "Timeline" },
  { id: "calendar", label: "Calendar" },
];

const TAB_IDS: TabId[] = [...CATEGORIES.map((c) => c.id), "plans"];
// A springy feel for things that slide, like the tab pill
const spring = { type: "spring", stiffness: 380, damping: 32 } as const;

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
  // Remembered in this browser, so reloading the page keeps your tab and layout
  // (the server can't see browser storage, so it always draws the default first)
  const savedTab = useSyncExternalStore(subscribe, getSavedTab, () => null);
  const savedView = useSyncExternalStore(subscribe, getSavedView, () => null);
  const chosenTab: TabId = TAB_IDS.includes(savedTab as TabId) ? (savedTab as TabId) : "orchestra";
  const view: View = VIEWS.some((v) => v.id === savedView) ? (savedView as View) : "cards";
  const setTab = (id: TabId) => setSavedTab(id);
  const setView = (id: View) => setSavedView(id);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [messages, setMessages] = useState<string[]>([]);
  const [selected, setSelected] = useState<EventItem | null>(null);
  const { unlocked, token, isOwner } = usePlans();
  const [slow, setSlow] = useState(false);

  // After locking, the "My plans" tab disappears, so show Orchestra instead
  const tab: TabId = chosenTab === "plans" && !unlocked ? "orchestra" : chosenTab;
  const tabs: { id: TabId; label: string }[] = [...CATEGORIES, ...(unlocked ? [{ id: "plans" as const, label: "My plans" }] : [])];

  useEffect(() => {
    let cancelled = false; // ignore the answer if the page has gone away meanwhile
    loadEverything()
      .then((result) => {
        if (!cancelled) setLoaded(result);
      })
      .catch(() => {
        if (!cancelled) setLoadError("Couldn't load the events. Please reload the page in a minute.");
      });
    // The free server sleeps when nobody visits; say so if waking it up takes a while
    const timer = setTimeout(() => setSlow(true), 4000);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, []);

  async function handleRefresh() {
    if (tab === "plans") return;
    setRefreshing(true);
    setMessages([]);
    try {
      setMessages(await refreshCategory(tab, token));
      setLoaded(await loadEverything());
    } catch (error) {
      setMessages([error instanceof Error ? error.message : String(error)]);
    } finally {
      setRefreshing(false);
    }
  }

  // useCallback keeps the same function between redraws, so the details window doesn't re-run its setup
  const closeDetails = useCallback(() => setSelected(null), []);

  const current = tab === "plans" ? undefined : loaded?.events[tab];
  const allEvents = loaded ? Object.values(loaded.events).flatMap((c) => c?.events ?? []) : [];

  return (
    // reducedMotion="user": visitors who turned off animations in their system settings get a calm page
    <MotionConfig reducedMotion="user">
      <section data-tab={tab} className="mt-10">
        <div role="tablist" aria-label="Event categories" className="flex gap-1 overflow-x-auto rounded-full border-[1.5px] border-line bg-surface p-1.5">
          {tabs.map((c) => (
            <motion.button
              key={c.id}
              // the "My plans" tab pops in when you unlock
              initial={c.id === "plans" ? { opacity: 0, scale: 0.6 } : false}
              animate={{ opacity: 1, scale: 1 }}
              type="button"
              role="tab"
              data-tab={c.id}
              aria-selected={tab === c.id}
              onClick={() => {
                setTab(c.id);
                setMessages([]);
              }}
              className={`relative flex shrink-0 items-center gap-2 rounded-full px-4 py-2 font-display font-medium transition-colors ${
                tab === c.id ? "text-on-accent" : "hover:bg-surface-2"
              }`}
            >
              {/* One coloured pill that slides to whichever tab is chosen */}
              {tab === c.id && (
                <motion.span layoutId="tab-pill" transition={spring} className="absolute inset-0 rounded-full bg-accent" />
              )}
              <span className={`relative ${tab === c.id ? "" : "text-accent"}`}>
                {c.id === "plans" ? <StarDoodle size={18} /> : <TabIcon category={c.id} />}
              </span>
              <span className="relative">{c.label}</span>
            </motion.button>
          ))}
        </div>

        {loadError && <p className="mt-6 rounded-xl border-[1.5px] border-line bg-surface p-4">{loadError}</p>}

        {!loaded && !loadError && (
          <>
            {slow && (
              <p className="mt-6 text-muted" role="status">
                Waking up the free server... the first visit can take up to a minute.
              </p>
            )}
            <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-label="Loading events">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-36 animate-pulse rounded-2xl bg-surface-2" />
              ))}
            </div>
          </>
        )}

        {tab === "plans" && loaded && (
          <motion.div className="mt-6" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
            <PlansBoard events={allEvents} today={loaded.today} onOpen={setSelected} />
          </motion.div>
        )}

        {current && loaded && (
          <>
            <div className="mt-6 flex flex-wrap items-center gap-x-4 gap-y-3">
              {/* Everything refreshes by itself every morning; the button is only for you, the site owner */}
              {isOwner && (
                <button
                  type="button"
                  onClick={handleRefresh}
                  disabled={refreshing || current.next_refresh_at !== null}
                  className="rounded-xl bg-accent px-4 py-2 font-semibold text-on-accent transition-[opacity,transform] hover:-translate-y-0.5 disabled:translate-y-0 disabled:opacity-40"
                >
                  {refreshing ? "Checking sources..." : "Refresh"}
                </button>
              )}
              <span className="text-sm text-muted">
                {current.refreshed_at ? `Last refreshed ${formatTimestamp(current.refreshed_at)}` : "Never refreshed"}
                {isOwner
                  ? current.next_refresh_at && ` · next refresh after ${formatTimestamp(current.next_refresh_at)}`
                  : " · updates every morning"}
              </span>

              <div className="flex w-full flex-wrap items-center justify-between gap-3 sm:ml-auto sm:w-auto">
                <span className="whitespace-nowrap text-sm text-muted">
                  {current.events.length} {current.events.length === 1 ? "event" : "events"}
                </span>
                <div className="flex rounded-xl bg-surface-2 p-1" aria-label="Layout">
                  {VIEWS.map((v) => (
                    <button
                      key={v.id}
                      type="button"
                      aria-pressed={view === v.id}
                      onClick={() => setView(v.id)}
                      className={`relative rounded-lg px-2.5 py-1.5 text-sm font-semibold transition-colors sm:px-3 ${
                        view === v.id ? "text-ink" : "text-muted hover:text-ink"
                      }`}
                    >
                      {view === v.id && (
                        <motion.span layoutId="view-pill" transition={spring} className="absolute inset-0 rounded-lg bg-surface shadow-sm" />
                      )}
                      <span className="relative">{v.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {messages.map((m) => (
              <p key={m} className="mt-3 rounded-xl bg-surface-2 p-3 text-sm">
                {m}
              </p>
            ))}

            {/* When the tab or layout changes, the old content fades out and the new one slides in */}
            <AnimatePresence mode="wait">
              <motion.div
                key={`${tab}-${view}`}
                className="mt-6"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
              >
                {current.events.length === 0 ? (
                  <p className="text-muted">Nothing here right now.</p>
                ) : view === "timeline" ? (
                  <TimelineView events={current.events} today={loaded.today} onOpen={setSelected} />
                ) : view === "calendar" ? (
                  <CalendarView events={current.events} today={loaded.today} onOpen={setSelected} />
                ) : (
                  <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                    {current.events.map((event, index) => (
                      // Each card rises into place as it scrolls into view
                      <motion.div
                        key={event.id}
                        initial={{ opacity: 0, y: 24 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true, amount: 0.15 }}
                        transition={{ duration: 0.4, delay: Math.min(index % 3, 2) * 0.06 }}
                      >
                        <EventCard event={event} today={loaded.today} onOpen={setSelected} />
                      </motion.div>
                    ))}
                  </div>
                )}

                {tab === "video_games" && loaded.watchlist.length > 0 && (
                  <div className="mt-12">
                    <h2 className="font-display text-2xl font-semibold">Watchlist</h2>
                    <p className="mt-1 text-muted">Big yearly gaming events to check yourself.</p>
                    <ul className="mt-4 grid gap-3 sm:grid-cols-2">
                      {loaded.watchlist.map((item) => (
                        <li key={item.name} className="card-hover rounded-2xl border-[1.5px] border-line bg-surface p-4">
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
                {tab !== "plans" && <EventsizeWatchlist category={tab} />}
              </motion.div>
            </AnimatePresence>
          </>
        )}

        <AnimatePresence>
          {selected && loaded && <EventDetails key={selected.id} event={selected} today={loaded.today} onClose={closeDetails} />}
        </AnimatePresence>
      </section>
    </MotionConfig>
  );
}