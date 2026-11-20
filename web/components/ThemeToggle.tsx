"use client";

const ORDER = ["system", "light", "dark"] as const;
type Choice = (typeof ORDER)[number];

// Cycles Auto -> Light -> Dark. "Auto" follows the visitor's computer or phone setting.
export default function ThemeToggle() {
  function cycle() {
    const root = document.documentElement;
    const current = (root.dataset.choice ?? "system") as Choice;
    const next = ORDER[(ORDER.indexOf(current) + 1) % ORDER.length];

    root.dataset.choice = next;
    if (next === "system") root.removeAttribute("data-theme");
    else root.dataset.theme = next;

    try {
      if (next === "system") localStorage.removeItem("theme");
      else localStorage.setItem("theme", next);
    } catch {
      // storage can be blocked (e.g. private windows); the switch still works for this visit
    }
  }

  return (
    <button
      type="button"
      onClick={cycle}
      aria-label="Change colour theme"
      className="rounded-full border-[1.5px] border-line bg-surface px-4 py-1.5 text-sm font-semibold hover:border-ink"
    >
      <span className="theme-label" data-for="system">Theme: auto</span>
      <span className="theme-label" data-for="light">Theme: light</span>
      <span className="theme-label" data-for="dark">Theme: dark</span>
    </button>
  );
}