// Everything the website needs to talk to the Python API.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const CATEGORIES = [
  { id: "bookstore_promo", label: "Books" },
  { id: "tech_event", label: "Tech" },
  { id: "orchestra", label: "Orchestra" },
  { id: "workshop", label: "Workshops" },
  { id: "video_games", label: "Video games" },
] as const;

export type CategoryId = (typeof CATEGORIES)[number]["id"];

// The shape of one event, exactly as the API sends it
export type EventItem = {
  id: number;
  source: string;
  category: CategoryId;
  title: string;
  title_key: string;
  details: string | null;
  start_date: string | null; // "2026-11-20"
  end_date: string | null;
  location: string | null;
  channel: string | null;
  link: string | null;
  topic: string | null;
  first_seen: string;
  last_seen: string;
  is_new: boolean;
};

export type CategoryEvents = {
  category: CategoryId;
  refreshed_at: string | null;
  next_refresh_at: string | null; // null means Refresh is allowed now
  events: EventItem[];
};

export type WatchItem = { name: string; site?: string; note?: string; search: string };

async function readError(response: Response) {
  try {
    const body = await response.json();
    return typeof body.detail === "string" ? body.detail : `Error ${response.status}`;
  } catch {
    return `Error ${response.status}`;
  }
}

export async function getEvents(category: CategoryId): Promise<CategoryEvents> {
  const response = await fetch(`${API_URL}/api/events/${category}`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function refreshCategory(category: CategoryId): Promise<string[]> {
  const response = await fetch(`${API_URL}/api/refresh/${category}`, { method: "POST" });
  if (!response.ok) throw new Error(await readError(response));
  const body = await response.json();
  return body.problems;
}

export async function getWatchlist(): Promise<WatchItem[]> {
  const response = await fetch(`${API_URL}/api/watchlist`);
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}



// ---------- Private plans ----------

export type PlanStatus = "want" | "going";

// What the API stores for each plan (a small copy of the event, so the board works even after the event expires)
export type Plan = {
  source: string;
  title_key: string;
  status: PlanStatus;
  category: string | null;
  title: string | null;
  start_date: string | null;
  link: string | null;
};

// Anything that can be planned: an event from the list, or a plan already on the board
export type Plannable = Omit<Plan, "status">;

// Thrown when the saved password token is missing, wrong or expired
export class AuthError extends Error {}

async function check(response: Response) {
  if (response.status === 401) throw new AuthError(await readError(response));
  if (!response.ok) throw new Error(await readError(response));
  return response.json();
}

export async function login(password: string): Promise<string> {
  const response = await fetch(`${API_URL}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!response.ok) throw new Error(await readError(response)); // a wrong password is a normal error here
  const body = await response.json();
  return body.token;
}

export async function getPlans(token: string): Promise<Plan[]> {
  const response = await fetch(`${API_URL}/api/plans`, { headers: { Authorization: `Bearer ${token}` } });
  return check(response);
}

export async function savePlan(token: string, item: Plannable, status: PlanStatus | null): Promise<void> {
  const response = await fetch(`${API_URL}/api/plans`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      source: item.source,
      title_key: item.title_key,
      status,
      category: item.category,
      title: item.title,
      start_date: item.start_date,
      link: item.link,
    }),
  });
  await check(response);
}