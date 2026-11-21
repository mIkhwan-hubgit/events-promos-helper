// Loads Google's "Sign in with Google" script once, when someone first opens the sign-in window

export const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "";

type GoogleId = {
  initialize: (options: { client_id: string; callback: (response: { credential: string }) => void }) => void;
  renderButton: (parent: HTMLElement, options: Record<string, string | number>) => void;
  disableAutoSelect: () => void;
};

declare global {
  interface Window {
    google?: { accounts: { id: GoogleId } };
  }
}

let loading: Promise<GoogleId> | null = null;

export function loadGoogle(): Promise<GoogleId> {
  loading ??= new Promise<GoogleId>((resolve, reject) => {
    if (window.google?.accounts?.id) return resolve(window.google.accounts.id);
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = () => {
      if (window.google?.accounts?.id) resolve(window.google.accounts.id);
      else reject(new Error("Couldn't load Google sign-in."));
    };
    script.onerror = () => {
      loading = null; // allow another try later
      reject(new Error("Couldn't load Google sign-in. Check your internet connection or ad blocker."));
    };
    document.head.appendChild(script);
  });
  return loading;
}

// After signing out, don't sign the same Google account straight back in by itself
export function forgetGoogleChoice() {
  window.google?.accounts?.id.disableAutoSelect();
}