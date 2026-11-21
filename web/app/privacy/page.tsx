import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy · What's On Malaysia",
  description: "What What's On Malaysia stores about you, and how to delete it.",
};

// A plain page that says, in everyday words, what the site keeps and why
export default function PrivacyPage() {
  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-12 sm:px-6">
      <Link href="/" className="text-sm font-semibold text-muted hover:text-ink">
        ← Back to What&apos;s On Malaysia
      </Link>
      <h1 className="mt-6 font-display text-4xl font-semibold">Privacy</h1>
      <p className="mt-2 text-muted">Last updated 21 November 2026</p>

      <div className="mt-8 grid gap-8 leading-relaxed">
        <section>
          <h2 className="font-display text-2xl font-semibold">Browsing</h2>
          <p className="mt-2">
            You can look at every event without signing in. The site doesn&apos;t use tracking or advertising cookies.
            Your browser remembers a few settings on your own device: light or dark mode, whether sounds are on, and
            whether you&apos;re signed in.
          </p>
        </section>

        <section>
          <h2 className="font-display text-2xl font-semibold">Signing in with Google</h2>
          <p className="mt-2">If you sign in to save Want and Going plans, the site keeps only:</p>
          <ul className="mt-2 list-disc space-y-1 pl-6">
            <li>your name and email address from your Google account,</li>
            <li>Google&apos;s ID number for your account (so the site recognises you next time),</li>
            <li>the events you mark as Want or Going.</li>
          </ul>
          <p className="mt-2">
            Your Google password never reaches this site: Google checks it and only tells the site who you are. Your
            plans are private; other visitors can&apos;t see them.
          </p>
        </section>

        <section>
          <h2 className="font-display text-2xl font-semibold">Where it&apos;s kept</h2>
          <p className="mt-2">
            The website runs on Vercel, the server on Render, and the database on Turso. Your details are only used to
            show you your own plans. They&apos;re never sold, shared for advertising, or sent to the AI model that reads
            the event listings.
          </p>
        </section>

        <section>
          <h2 className="font-display text-2xl font-semibold">Deleting your data</h2>
          <p className="mt-2">
            Signed in? Tap your initial at the top of the page, then <strong>Delete my account</strong>. Your account
            and all your plans are removed straight away. You can also remove the site&apos;s access in your Google
            account settings, under &quot;Third-party apps &amp; services&quot;.
          </p>
        </section>

        <section>
          <h2 className="font-display text-2xl font-semibold">About the events</h2>
          <p className="mt-2">
            Events and promotions are collected from public websites and link back to them. For tickets and full
            details, always check the organiser&apos;s own page.
          </p>
        </section>

        <section>
          <h2 className="font-display text-2xl font-semibold">Questions</h2>
          <p className="mt-2">
            This is a personal portfolio project. For questions, open an issue on the{" "}
            <a
              href="https://github.com/mIkhwan-hubgit/bookstore-promos"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold underline"
            >
              project&apos;s GitHub page
            </a>
            .
          </p>
        </section>
      </div>
    </main>
  );
}