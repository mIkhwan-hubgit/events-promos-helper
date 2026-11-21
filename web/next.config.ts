import type { NextConfig } from "next";

// Security headers: tell browsers what this site is allowed to load and do.
// The Content-Security-Policy (CSP) is a list of places scripts, styles, images and connections may come from,
// so even if someone slipped a script into the page, the browser would refuse to run or send anything elsewhere.
const isDev = process.env.NODE_ENV !== "production";
const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";

const contentSecurityPolicy = [
  "default-src 'self'",
  // 'unsafe-inline': Next.js and our theme script use small inline scripts. 'unsafe-eval' only while developing.
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""} https://accounts.google.com/gsi/client`,
  "style-src 'self' 'unsafe-inline' https://accounts.google.com/gsi/style",
  "img-src 'self' data: blob: https://*.googleusercontent.com",
  "font-src 'self'",
  `connect-src 'self' ${apiUrl} https://accounts.google.com/gsi/`, // our API and Google sign-in only
  "frame-src https://accounts.google.com/gsi/", // the Google sign-in button and pop-up
  "worker-src 'self' blob:", // the confetti runs in a small background worker
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'", // nobody may show this site inside their own page (stops "clickjacking")
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: contentSecurityPolicy },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
];

const nextConfig: NextConfig = {
  /* config options here */
  experimental: {
    agentFeedback: true,
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
};

export default nextConfig;