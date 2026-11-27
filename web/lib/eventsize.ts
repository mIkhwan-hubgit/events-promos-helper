import type { CategoryId } from "./api";

// Eventsize has no public search address to link to, so each keyword opens a
// Google search limited to eventsize.com pages. If Eventsize ever adds a search
// page, only this function needs to change.
export function eventsizeLink(keyword: string): string {
  const query = `site:eventsize.com ${keyword} Malaysia`;
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

// Every Eventsize event in Malaysia
export const EVENTSIZE_MALAYSIA = "https://eventsize.com/events/location/Malaysia";

// Keywords for each tab. Add or remove words freely; each one becomes a link.
export const EVENTSIZE_KEYWORDS: Record<CategoryId, string[]> = {
  bookstore_promo: [
    "book fair", "book sale", "Big Bad Wolf", "Pesta Buku", "book launch", "book signing",
    "author talk", "book club", "reading", "poetry", "literary festival", "writing workshop",
    "storytelling", "comics", "zine", "library",
  ],
  tech_event: [
    "tech", "AI", "machine learning", "data science", "coding", "developer", "hackathon",
    "startup", "cybersecurity", "cloud", "blockchain", "fintech", "robotics", "UI UX design",
    "digital marketing", "tech conference", "tech meetup", "webinar",
  ],
  orchestra: [
    "orchestra", "symphony", "philharmonic", "classical music", "concert", "choir", "recital",
    "piano", "violin", "string quartet", "chamber music", "opera", "jazz", "musical theatre",
    "ensemble", "film music concert",
  ],
  workshop: [
    "workshop", "class", "pottery", "ceramics", "painting", "art jamming", "watercolour",
    "calligraphy", "baking", "cooking class", "candle making", "perfume making", "terrarium",
    "floral", "crochet", "knitting", "sewing", "leather craft", "resin art", "photography", "DIY",
  ],
  video_games: [
    "gaming", "esports", "game tournament", "LAN party", "cosplay", "anime", "comic con",
    "convention", "game developer", "indie games", "board games", "card games", "Pokémon",
    "Mobile Legends", "Valorant", "Dota 2", "retro gaming", "VR",
  ],
};