"use client";

import { createContext, useContext, useEffect, useState, useSyncExternalStore, type ReactNode } from "react";
import { AnimatePresence, motion } from "motion/react";
import { AuthError, getPlans, savePlan, type Plan, type PlanStatus, type Plannable } from "@/lib/api";
import { celebrate, playSound, type Origin } from "@/lib/fun";
import { getSoundOn, getToken, setSoundOn, setToken, subscribe } from "@/lib/session";
import UnlockDialog from "./UnlockDialog";

type PlansContextValue = {
  unlocked: boolean;
  token: string | null;
  plans: Plan[];
  statusOf: (item: Plannable) => PlanStatus | null;
  setPlan: (item: Plannable, status: PlanStatus | null, origin?: Origin) => void;
  openUnlock: () => void;
  lock: () => void;
  soundOn: boolean;
  toggleSound: () => void;
};

const PlansContext = createContext<PlansContextValue | null>(null);

export function usePlans() {
  const value = useContext(PlansContext);
  if (!value) throw new Error("usePlans must be used inside <PlansProvider>");
  return value;
}

const keyOf = (item: Plannable) => `${item.source}|${item.title_key}`;
const EMPTY = new Map<string, Plan>();

// Holds "am I unlocked?" and the Want/Going plans for the whole page
export default function PlansProvider({ children }: { children: ReactNode }) {
  // The server can't see this browser's storage, so it always draws the page locked and quiet
  const token = useSyncExternalStore(subscribe, getToken, () => null);
  const soundOn = useSyncExternalStore(subscribe, getSoundOn, () => false);

  // The plans, remembered together with the token they were loaded for
  const [loaded, setLoaded] = useState<{ token: string; plans: Map<string, Plan> } | null>(null);
  const [unlockOpen, setUnlockOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const plans = token && loaded?.token === token ? loaded.plans : EMPTY;

  function showNotice(text: string) {
    setNotice(text);
    setTimeout(() => setNotice((current) => (current === text ? null : current)), 4000);
  }

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getPlans(token)
      .then((list) => {
        if (!cancelled) setLoaded({ token, plans: new Map(list.map((p) => [keyOf(p), p])) });
      })
      .catch((error) => {
        if (cancelled) return;
        if (error instanceof AuthError) setToken(null); // the password changed or the token expired
        else setNotice("Couldn't load your plans.");
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  // Change one plan in the page straight away (the "optimistic" update)
  function putLocal(currentToken: string, key: string, plan: Plan | null) {
    setLoaded((previous) => {
      const next = new Map(previous?.token === currentToken ? previous.plans : EMPTY);
      if (plan) next.set(key, plan);
      else next.delete(key);
      return { token: currentToken, plans: next };
    });
  }

  function setPlan(item: Plannable, status: PlanStatus | null, origin?: Origin) {
    if (!token) return;
    const key = keyOf(item);
    const before = plans.get(key) ?? null;
    if ((before?.status ?? null) === status) return;

    const plan: Plan | null = status
      ? {
          source: item.source,
          title_key: item.title_key,
          status,
          category: item.category,
          title: item.title,
          start_date: item.start_date,
          link: item.link,
        }
      : null;
    putLocal(token, key, plan);

    if (status === "going") celebrate(origin);
    if (soundOn) playSound(status ?? "remove");

    // Then tell the API. If that fails, put things back the way they were.
    savePlan(token, item, status).catch((error) => {
      putLocal(token, key, before);
      if (error instanceof AuthError) {
        setToken(null);
        setUnlockOpen(true);
      } else {
        showNotice("Couldn't save that change. Is the API running?");
      }
    });
  }

  const value: PlansContextValue = {
    unlocked: token !== null,
    token,
    plans: [...plans.values()].sort((a, b) => (a.start_date ?? "9999").localeCompare(b.start_date ?? "9999")),
    statusOf: (item) => plans.get(keyOf(item))?.status ?? null,
    setPlan,
    openUnlock: () => setUnlockOpen(true),
    lock: () => setToken(null),
    soundOn,
    toggleSound: () => {
      setSoundOn(!soundOn);
      if (!soundOn) playSound("want"); // a little sample when switching on
    },
  };

  return (
    <PlansContext.Provider value={value}>
      {children}
      <AnimatePresence>
        {unlockOpen && (
          <UnlockDialog
            onClose={() => setUnlockOpen(false)}
            onUnlocked={(newToken) => {
              setToken(newToken);
              setUnlockOpen(false);
            }}
          />
        )}
      </AnimatePresence>
      <AnimatePresence>
        {notice && (
          <motion.p
            role="status"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            className="fixed inset-x-4 bottom-4 z-[60] mx-auto max-w-sm rounded-2xl bg-ink px-4 py-3 text-center text-sm font-semibold text-bg shadow-lg"
          >
            {notice}
          </motion.p>
        )}
      </AnimatePresence>
    </PlansContext.Provider>
  );
}