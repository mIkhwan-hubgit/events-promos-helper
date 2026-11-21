import Link from "next/link";
import EventBrowser from "@/components/EventBrowser";
import Hero from "@/components/Hero";
import PlansProvider from "@/components/PlansProvider";
import TopBar from "@/components/TopBar";

export default function Home() {
  return (
    <PlansProvider>
      <main className="mx-auto w-full max-w-6xl px-4 pb-16 sm:px-6">
        <TopBar />
        <Hero />
        <EventBrowser />
      </main>
      <footer className="mx-auto flex w-full max-w-6xl flex-wrap gap-x-6 gap-y-2 border-t-[1.5px] border-line px-4 py-6 text-sm text-muted sm:px-6">
        <span>Events are collected from public sites. Check the organiser&apos;s page for tickets.</span>
        <Link href="/privacy" className="font-semibold hover:text-ink">
          Privacy
        </Link>
        <a
          href="https://github.com/mIkhwan-hubgit/bookstore-promos"
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold hover:text-ink"
        >
          Source code
        </a>
      </footer>
    </PlansProvider>
  );
}