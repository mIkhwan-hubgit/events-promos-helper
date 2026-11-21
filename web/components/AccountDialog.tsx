"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import type { User } from "@/lib/api";

type Props = {
  user: User;
  onClose: () => void;
  onSignOut: () => void;
  onDelete: () => Promise<void>;
};

// Your account: sign out, or delete your account and plans
export default function AccountDialog({ user, onClose, onSignOut, onDelete }: Props) {
  const closeButton = useRef<HTMLButtonElement>(null);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  async function handleDelete() {
    setBusy(true);
    setError(null);
    try {
      await onDelete();
    } catch {
      setError("Couldn't delete your account. Please try again.");
      setBusy(false);
    }
  }

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
        aria-labelledby="account-title"
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
        <h2 id="account-title" className="pr-10 font-display text-2xl font-semibold">
          {user.name ? `Hi, ${user.name.split(" ")[0]}!` : "Your account"}
        </h2>
        <p className="mt-1 break-all text-sm text-muted">{user.email}</p>

        {!confirming ? (
          <div className="mt-6 grid gap-2">
            <button type="button" onClick={onSignOut} className="rounded-xl bg-ink px-4 py-2.5 font-semibold text-bg">
              Sign out
            </button>
            <button type="button" onClick={() => setConfirming(true)} className="rounded-xl px-4 py-2.5 text-sm font-semibold text-muted hover:bg-surface-2">
              Delete my account...
            </button>
          </div>
        ) : (
          <div className="mt-6 rounded-2xl border-[1.5px] border-books p-4">
            <p className="text-sm">
              This deletes your account and all your Want and Going plans for good. It can&apos;t be undone.
            </p>
            {error && (
              <p role="alert" className="mt-2 text-sm font-semibold text-books">
                {error}
              </p>
            )}
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" onClick={() => setConfirming(false)} className="rounded-xl px-4 py-2 font-semibold hover:bg-surface-2">
                Keep it
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={busy}
                className="rounded-xl bg-books px-4 py-2 font-semibold text-white disabled:opacity-40"
              >
                {busy ? "Deleting..." : "Delete for good"}
              </button>
            </div>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}