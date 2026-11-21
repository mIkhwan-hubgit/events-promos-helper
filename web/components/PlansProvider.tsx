"use client";

import { createContext, useContext, useEffect, useState, useSyncExternalStore, type ReactNode } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  AuthError,
  deleteAccount,
  getMe,
  getPlans,
  savePlan,
  type Plan,
  type PlanStatus,
  type Plannable,
  type User,
} from "@/lib/api";
import { celebrate, playSound, type Origin } from "@/lib/fun";
import { forgetGoogleChoice } from "@/lib/google";
import { getSoundOn, getToken, setSoundOn, setToken, subscribe } from "@/lib/session";
import AccountDialog from "./AccountDialog";
import SignInDialog from "./SignInDialog";

type PlansContextValue = {
  unlocked: boolean; // signed in
  token: string | null;
  user: User | null;
  isOwner: boolean; // you, the site owner: gets the Refresh button
  plans: Plan[];
  statusOf: (item: Plannable) => PlanStatus | null;
  setPlan: (item: Plannable, status: PlanStatus | null, origin?: Origin) => void;
  openUnlock: () => void; // the sign-in window
  openAccount: () => void;
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

type Loaded = { token: string; user: User; plans: Map<string, Plan> };

// Holds "who is signed in?" and their Want/Going plans for the whole page
export default function PlansProvider({ children }: { children: ReactNode }) {
  // The server can't see this browser's storage, so it always draws the page signed out and quiet
  const token = useSyncExternalStore(subscribe, getToken, () => null);
  const soundOn = useSyncExternalStore(subscribe, getSoundOn, () => false);

  // The person and their plans, remembered together with the token they were loaded for
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [signInOpen, setSignInOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const current = token && loaded?.token === token ? loaded : null;
  const plans = current?.plans ?? EMPTY;

  function showNotice(text: string) {
    setNotice(text);
    setTimeout(() => setNotice((now) => (now === text ? null : now)), 4000);
  }

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    Promise.all([getMe(token), getPlans(token)])
      .then(([user, list]) => {
        if (!cancelled) setLoaded({ token, user, plans: new Map(list.map((p) => [keyOf(p), p])) });
      })
      .catch((error) => {
        if (cancelled) return;
        if (error instanceof AuthError) setToken(null); // signed out elsewhere, deleted, or expired
        else setNotice("Couldn't load your plans.");
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  // Change one plan in the page straight away (the "optimistic" update)
  function putLocal(key: string, plan: Plan | null) {
    setLoaded((previous) => {
      if (!previous || previous.token !== token) return previous;
      const next = new Map(previous.plans);
      if (plan) next.set(key, plan);
      else next.delete(key);
      return { ...previous, plans: next };
    });
  }

  function setPlan(item: Plannable, status: PlanStatus | null, origin?: Origin) {
    if (!token || !current) return;
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
    putLocal(key, plan);

    if (status === "going") celebrate(origin);
    if (soundOn) playSound(status ?? "remove");

    // Then tell the API. If that fails, put things back the way they were.
    savePlan(token, item, status).catch((error) => {
      putLocal(key, before);
      if (error instanceof AuthError) {
        setToken(null);
        setSignInOpen(true);
      } else {
        showNotice("Couldn't save that change. Please try again.");
      }
    });
  }

  function signOut() {
    setToken(null);
    setAccountOpen(false);
    forgetGoogleChoice();
  }

  const value: PlansContextValue = {
    unlocked: current !== null,
    token,
    user: current?.user ?? null,
    isOwner: current?.user.is_owner ?? false,
    plans: [...plans.values()].sort((a, b) => (a.start_date ?? "9999").localeCompare(b.start_date ?? "9999")),
    statusOf: (item) => plans.get(keyOf(item))?.status ?? null,
    setPlan,
    openUnlock: () => setSignInOpen(true),
    openAccount: () => setAccountOpen(true),
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
        {signInOpen && (
          <SignInDialog
            onClose={() => setSignInOpen(false)}
            onSignedIn={(newToken) => {
              setToken(newToken);
              setSignInOpen(false);
            }}
          />
        )}
      </AnimatePresence>
      <AnimatePresence>
        {accountOpen && current && (
          <AccountDialog
            user={current.user}
            onClose={() => setAccountOpen(false)}
            onSignOut={signOut}
            onDelete={async () => {
              await deleteAccount(current.token);
              signOut();
              showNotice("Your account and plans have been deleted.");
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