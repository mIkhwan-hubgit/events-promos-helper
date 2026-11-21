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

function PersonIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" />
    </svg>
  );
}

const pill = "flex shrink-0 items-center gap-1.5 rounded-full border-[1.5px] border-line bg-surface px-2.5 py-1.5 text-sm font-semibold hover:border-ink sm:px-3";

export default function TopBar() {
  const { user, openUnlock, openAccount, soundOn, toggleSound } = usePlans();
  const firstName = user?.name?.split(" ")[0] ?? "Me";

  return (
    <div className="flex items-center justify-between gap-3 py-5">
      <span className="min-w-0 truncate font-display text-base font-semibold sm:text-lg">What&apos;s On Malaysia</span>
      <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
        <button type="button" onClick={toggleSound} aria-pressed={soundOn} aria-label="Sound effects" className={pill}>
          <SpeakerIcon on={soundOn} />
        </button>
        {user ? (
          <button type="button" onClick={openAccount} className={pill} aria-label={`Your account (${firstName})`}>
            {/* a round badge with your first initial */}
            <span aria-hidden="true" className="grid h-[18px] w-[18px] place-items-center rounded-full bg-ink text-[11px] font-bold text-bg">
              {firstName[0]?.toUpperCase()}
            </span>
            <span className="hidden sm:inline">{firstName}</span>
          </button>
        ) : (
          <button type="button" onClick={openUnlock} className={pill}>
            <PersonIcon />
            <span className="hidden sm:inline">Sign in</span>
            <span className="sr-only sm:hidden">Sign in</span>
          </button>
        )}
        <ThemeToggle />
      </div>
    </div>
  );
}