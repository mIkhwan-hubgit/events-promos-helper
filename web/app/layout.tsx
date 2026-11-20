import type { Metadata } from "next";
import { Figtree, Fredoka } from "next/font/google";
import "./globals.css";

// Fredoka for headings, Figtree for everything else
const fredoka = Fredoka({
  variable: "--font-fredoka",
  subsets: ["latin"],
});

const figtree = Figtree({
  variable: "--font-figtree",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "What's On Malaysia",
  description: "Book promotions, tech events, concerts, workshops and gaming events in Malaysia.",
};

// Runs before the page appears: applies a saved light/dark choice, so the page never flashes the wrong theme
const themeScript = `(function(){try{var d=document.documentElement;var t=localStorage.getItem("theme");if(t==="light"||t==="dark"){d.setAttribute("data-theme",t);d.setAttribute("data-choice",t)}else{d.setAttribute("data-choice","system")}}catch(e){}})()`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${fredoka.variable} ${figtree.variable} h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body suppressHydrationWarning className="min-h-full">
        {children}
      </body>
    </html>
  );
}