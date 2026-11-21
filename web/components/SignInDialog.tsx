"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { loginWithGoogle } from "@/lib/api";
import { GOOGLE_CLIENT_ID, loadGoogle } from "@/lib/google";

type Props = {
  onClose: () => void;
  onSignedIn: (token: string) => void;
};

// The window with the "Sign in with Google" button
export default function SignInDialog({ onClose, onSignedIn }: Props) {
  const closeButton = useRef<HTMLButtonElement>(null);
  const buttonSpot = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Keep the newest onSignedIn, because Google calls back long after this window first appeared
  const signedIn = useRef(onSignedIn);
  useEffect(() => {
    signedIn.current = onSignedIn;
  });

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    closeButton.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      opener?.focus({ preventScroll: true });
    };
  }, [onClose]);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;
    let cancelled = false;
    loadGoogle()
      .then((google) => {
        if (cancelled || !buttonSpot.current) return;
        google.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: (response) => {
            setBusy(true);
            setError(null);
            loginWithGoogle(response.credential)
              .then(({ token }) => signedIn.current(token))
              .catch((err) => {
                setError(err instanceof Error ? err.message : "Sign-in didn't work.");
                setBusy(false);
              });
          },
        });
        const dark = getComputedStyle(document.documentElement).colorScheme === "dark";
        google.renderButton(buttonSpot.current, {
          theme: dark ? "filled_black" : "outline",
          size: "large",
          shape: "pill",
          text: "continue_with",
          width: 260,
        });
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Couldn't load Google sign-in.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <motion.div
      className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-labelledby="sign-in-title"
        onClick={(e) => e.stopPropagation()}
        initial={{ scale: 0.92, y: 12 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ type: "spring", stiffness: 420, damping: 30 }}
        className="relative w-full max-w-sm rounded-3xl border-2 border-ink bg-surface p-6"
      >
        <button
          ref={closeButton}
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute right-4 top-4 grid h-9 w-9 place-items-center rounded-full bg-surface-2 text-lg hover:bg-line"
        >
          ×
        </button>
        <h2 id="sign-in-title" className="pr-10 font-display text-2xl font-semibold">
          Save your plans
        </h2>
        <p className="mt-1 text-sm text-muted">
          Sign in to keep your own Want and Going lists on any device. Only you can see them.
        </p>

        <div className="mt-6 flex min-h-11 justify-center">
          {GOOGLE_CLIENT_ID ? (
            <>
              {/* Google draws its own button inside this box */}
              <div ref={buttonSpot} className={busy ? "hidden" : ""} />
              {busy && <p className="font-semibold">Signing you in...</p>}
            </>
          ) : (
            <p className="text-sm font-semibold text-books">Sign-in isn&apos;t set up yet (NEXT_PUBLIC_GOOGLE_CLIENT_ID is missing).</p>
          )}
        </div>
        {error && (
          <p role="alert" className="mt-3 text-center text-sm font-semibold text-books">
            {error}
          </p>
        )}

        <p className="mt-6 text-xs text-muted">
          We only keep your Google name and email, plus the plans you make. No password is shared with this site, and
          you can delete your account any time.
        </p>
      </motion.div>
    </motion.div>
  );
}