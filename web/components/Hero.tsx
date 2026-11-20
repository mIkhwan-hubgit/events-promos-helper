import { BookDoodle, GamepadDoodle, NoteDoodle, StarDoodle } from "./Doodles";

const CHIPS = [
  { label: "Books", color: "var(--books)" },
  { label: "Tech", color: "var(--tech)" },
  { label: "Orchestra", color: "var(--orchestra)" },
  { label: "Workshops", color: "var(--workshop)" },
  { label: "Video games", color: "var(--games)" },
];

export default function Hero() {
  return (
    <header className="relative isolate overflow-hidden rounded-[28px] border-[1.5px] border-line bg-surface px-6 py-12 sm:px-14 sm:py-16">
      <div aria-hidden="true" className="hero-blob blob-1" />
      <div aria-hidden="true" className="hero-blob blob-2" />
      <div aria-hidden="true" className="hero-blob blob-3" />
      <div aria-hidden="true" className="hero-blob blob-4" />

      <BookDoodle size={52} className="doodle top-6 right-[26%] hidden sm:block" />
      <GamepadDoodle size={56} className="doodle bottom-7 right-[8%] hidden sm:block [animation-delay:-3s]" />
      <NoteDoodle size={44} className="doodle top-[46%] right-[40%] hidden md:block [animation-delay:-2s]" />
      <StarDoodle size={40} className="doodle top-6 right-[7%] [animation-delay:-4s]" />

      <p className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">Kuala Lumpur and beyond</p>
      <h1 className="mt-2 max-w-[12ch] font-display text-5xl font-semibold leading-[1.05] sm:text-7xl">
        What&apos;s On Malaysia<span className="text-books">.</span>
      </h1>
      <p className="mt-4 max-w-[52ch] text-lg text-muted">
        Book sales, tech meetups, orchestra nights, hobby workshops and gaming festivals, gathered from the
        sites that list them.
      </p>
      <div className="mt-6 flex flex-wrap gap-2">
        {CHIPS.map((chip) => (
          <span
            key={chip.label}
            className="rounded-full border-[1.5px] px-3 py-1 text-sm font-semibold"
            style={{
              background: `color-mix(in srgb, ${chip.color} 14%, var(--surface))`,
              borderColor: `color-mix(in srgb, ${chip.color} 45%, transparent)`,
            }}
          >
            {chip.label}
          </span>
        ))}
      </div>
    </header>
  );
}