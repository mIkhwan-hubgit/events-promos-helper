"use client";

import { usePlans } from "./PlansProvider";
import ThemeToggle from "./ThemeToggle";

function SpeakerIcon({ on }: { on: boolean }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 9h4l5-4v14l-5-4H4z" />
      {on ? <path d="M17 9c1.5 1.7 1.5 4.3 0 6M19.5 6.5c3 3.2 3 7.8 0 11" /> : <path d="M17 9l5 6M22 9l-5 6" />}
    </svg>
  );
}

function LockIcon({ open }: { open: boolean }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="11" width="16" height="10" rx="2.5" />
      <path d={open ? "M8 11V7a4 4 0 017.6-1.7" : "M8 11V7a4 4 0 018 0v4"} />
    </svg>
  );
}

const pill = "flex items-center gap-1.5 rounded-full border-[1.5px] border-line bg-surface px-3 py-1.5 text-sm font-semibold hover:border-ink";

export default function TopBar() {
  const { unlocked, openUnlock, lock, soundOn, toggleSound } = usePlans();

  return (
    <div className="flex items-center justify-between gap-3 py-5">
      <span className="whitespace-nowrap font-display text-lg font-semibold">What&apos;s On Malaysia</span>
      <div className="flex items-center gap-2">
        <button type="button" onClick={toggleSound} aria-pressed={soundOn} aria-label="Sound effects" className={pill}>
          <SpeakerIcon on={soundOn} />
        </button>
        <button type="button" onClick={unlocked ? lock : openUnlock} className={pill}>
          <LockIcon open={unlocked} />
          <span className="hidden sm:inline">{unlocked ? "Lock plans" : "My plans"}</span>
          <span className="sr-only sm:hidden">{unlocked ? "Lock plans" : "Unlock my plans"}</span>
        </button>
        <ThemeToggle />
      </div>
    </div>
  );
}