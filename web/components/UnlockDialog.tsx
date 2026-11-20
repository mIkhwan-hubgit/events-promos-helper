"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { motion } from "motion/react";
import { login } from "@/lib/api";

type Props = {
  onClose: () => void;
  onUnlocked: (token: string) => void;
};

// The small password window for unlocking "My plans"
export default function UnlockDialog({ onClose, onUnlocked }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    input.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      opener?.focus({ preventScroll: true }); // back to the button that opened it
    };
  }, [onClose]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      onUnlocked(await login(password));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't unlock.");
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
      <motion.form
        onSubmit={handleSubmit}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="unlock-title"
        initial={{ scale: 0.92, y: 12 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ type: "spring", stiffness: 420, damping: 30 }}
        className="w-full max-w-sm rounded-3xl border-2 border-ink bg-surface p-6"
      >
        <h2 id="unlock-title" className="font-display text-2xl font-semibold">
          Unlock my plans
        </h2>
        <p className="mt-1 text-sm text-muted">Only you can see your Want and Going lists.</p>

        <label htmlFor="plans-password" className="mt-5 block text-sm font-semibold">
          Password
        </label>
        <input
          ref={input}
          id="plans-password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1.5 w-full rounded-xl border-[1.5px] border-line bg-bg px-3 py-2.5 outline-none focus:border-ink"
        />
        {error && (
          <p role="alert" className="mt-2 text-sm font-semibold text-books">
            {error}
          </p>
        )}

        <div className="mt-5 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-xl px-4 py-2 font-semibold hover:bg-surface-2">
            Cancel
          </button>
          <button
            type="submit"
            disabled={busy || password === ""}
            className="rounded-xl bg-ink px-4 py-2 font-semibold text-bg disabled:opacity-40"
          >
            {busy ? "Checking..." : "Unlock"}
          </button>
        </div>
      </motion.form>
    </motion.div>
  );
}