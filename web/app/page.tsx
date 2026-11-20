import EventBrowser from "@/components/EventBrowser";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-10">
      <h1 className="text-4xl font-bold">What&apos;s On Malaysia</h1>
      <p className="mt-2 text-neutral-500">
        Books, tech meetups, concerts, workshops and gaming events in Malaysia, in one place.
      </p>
      <EventBrowser />
    </main>
  );
}