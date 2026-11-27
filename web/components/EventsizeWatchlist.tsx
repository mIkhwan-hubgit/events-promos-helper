import type { CategoryId } from "@/lib/api";
import { EVENTSIZE_KEYWORDS, EVENTSIZE_MALAYSIA, eventsizeLink } from "@/lib/eventsize";

// Keyword links that search Eventsize; nothing is read from the site itself
export default function EventsizeWatchlist({ category }: { category: CategoryId }) {
  return (
    <div className="mt-12">
      <h2 className="font-display text-2xl font-semibold">Explore on Eventsize</h2>
      <p className="mt-1 text-muted">
        Eventsize isn&apos;t included automatically yet. Tap a keyword to search its Malaysian listings in a new tab.
      </p>
      <ul className="mt-4 flex flex-wrap gap-2">
        {EVENTSIZE_KEYWORDS[category].map((keyword) => (
          <li key={keyword}>
            <a
              href={eventsizeLink(keyword)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block rounded-full border-[1.5px] border-line bg-surface px-3 py-1.5 text-sm font-semibold transition-colors hover:border-accent hover:text-accent"
            >
              {keyword} ↗
            </a>
          </li>
        ))}
      </ul>
      <a
        href={EVENTSIZE_MALAYSIA}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-4 inline-block text-sm font-semibold text-accent hover:underline"
      >
        All Eventsize events in Malaysia ↗
      </a>
    </div>
  );
}