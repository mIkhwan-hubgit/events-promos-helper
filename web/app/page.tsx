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
    </PlansProvider>
  );
}