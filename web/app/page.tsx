import EventBrowser from "@/components/EventBrowser";
import Hero from "@/components/Hero";
import ThemeToggle from "@/components/ThemeToggle";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-16 sm:px-6">
      <div className="flex items-center justify-between gap-3 py-5">
        <span className="font-display text-lg font-semibold">What&apos;s On Malaysia</span>
        <ThemeToggle />
      </div>
      <Hero />
      <EventBrowser />
    </main>
  );
}