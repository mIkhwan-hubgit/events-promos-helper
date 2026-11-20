// Simple hand-drawn style icons, used as decoration and on the tabs.
import type { CategoryId } from "@/lib/api";

type Props = { size?: number; className?: string };

export function BookDoodle({ size = 24, className }: Props) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path d="M12 6C9 4 5 4 2 5v14c3-1 7-1 10 1 3-2 7-2 10-1V5c-3-1-7-1-10 1zM12 6v14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

export function LaptopDoodle({ size = 24, className }: Props) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden="true">
      <rect x="3" y="4" width="18" height="12" rx="2.5" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M1 20h22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function NoteDoodle({ size = 24, className }: Props) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path d="M9 18V5l12-3v13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <circle cx="6" cy="18" r="3" fill="currentColor" />
      <circle cx="18" cy="15" r="3" fill="currentColor" />
    </svg>
  );
}

export function BrushDoodle({ size = 24, className }: Props) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path d="M14 3l7 7-9 9H5v-7z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M5 19l-2 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function GamepadDoodle({ size = 24, className }: Props) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path d="M7 6h10a5 5 0 015 5c0 4-2 7-4 7s-3-2-4-3h-4c-1 1-2 3-4 3s-4-3-4-7a5 5 0 015-5z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M7 10v4M5 12h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function StarDoodle({ size = 24, className }: Props) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" className={className} aria-hidden="true">
      <path d="M20 3l4.5 11 11.5 1-8.8 7.6 2.8 11.4L20 27.8 10 34l2.8-11.4L4 15l11.5-1z" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
    </svg>
  );
}

export function TabIcon({ category, size = 18 }: { category: CategoryId; size?: number }) {
  switch (category) {
    case "bookstore_promo":
      return <BookDoodle size={size} />;
    case "tech_event":
      return <LaptopDoodle size={size} />;
    case "orchestra":
      return <NoteDoodle size={size} />;
    case "workshop":
      return <BrushDoodle size={size} />;
    case "video_games":
      return <GamepadDoodle size={size} />;
  }
}