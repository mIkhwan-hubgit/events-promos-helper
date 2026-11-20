// Remembers two things in this browser: the plans token and whether sound is on.
// React components read them with useSyncExternalStore, so every part of the page stays in sync.

const TOKEN_KEY = "plans-token";
const SOUND_KEY = "sound";

const listeners = new Set<() => void>();
const memory = new Map<string, string>(); // used when the browser blocks storage (some private windows)

function read(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return memory.get(key) ?? null;
  }
}

function write(key: string, value: string | null) {
  if (value === null) memory.delete(key);
  else memory.set(key, value);
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    // storage blocked: the memory copy keeps it for this visit
  }
  listeners.forEach((listener) => listener());
}

export function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", listener); // another tab locked or unlocked
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

// The token looks like "1797768374.abc123...": the first part is when it expires (in seconds)
export function getToken(): string | null {
  const token = read(TOKEN_KEY);
  if (!token) return null;
  const expiry = Number(token.split(".")[0]);
  return expiry * 1000 > Date.now() ? token : null;
}

export function setToken(token: string | null) {
  write(TOKEN_KEY, token);
}

export function getSoundOn(): boolean {
  return read(SOUND_KEY) === "on";
}

export function setSoundOn(on: boolean) {
  write(SOUND_KEY, on ? "on" : null);
}