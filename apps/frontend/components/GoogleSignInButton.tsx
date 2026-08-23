"use client";

import { useEffect, useRef, useState } from "react";
import { api, setToken, ApiError } from "../lib/api";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: { client_id: string; callback: (response: { credential: string }) => void }) => void;
          renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

const SCRIPT_SRC = "https://accounts.google.com/gsi/client";

function loadGoogleScript(): Promise<void> {
  if (window.google?.accounts?.id) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${SCRIPT_SRC}"]`);
    if (existing) {
      existing.addEventListener("load", () => resolve());
      return;
    }
    const script = document.createElement("script");
    script.src = SCRIPT_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Identity Services"));
    document.body.appendChild(script);
  });
}

/** Renders nothing if the backend hasn't configured GOOGLE_CLIENT_ID —
 * see docs/ARCHITECTURE.md and .env.example for setup. */
export default function GoogleSignInButton({ onSuccess, onError }: { onSuccess: () => void; onError: (message: string) => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    let cancelled = false;

    api
      .googleConfig()
      .then(async (config) => {
        if (cancelled || !config.enabled || !config.client_id) return;
        await loadGoogleScript();
        if (cancelled || !containerRef.current || !window.google) return;

        window.google.accounts.id.initialize({
          client_id: config.client_id,
          callback: async (response) => {
            try {
              const result = await api.loginWithGoogle(response.credential);
              setToken(result.access_token);
              onSuccess();
            } catch (err) {
              onError(err instanceof ApiError ? err.message : "Google sign-in failed");
            }
          },
        });
        window.google.accounts.id.renderButton(containerRef.current, { theme: "outline", size: "large", width: 328 });
        setEnabled(true);
      })
      .catch(() => {
        /* Google sign-in just doesn't appear — email/password still works. */
      });

    return () => {
      cancelled = true;
    };
  }, [onSuccess, onError]);

  // The container div must exist in the DOM before the effect above runs
  // (Google's renderButton needs a real element to mount into), so it's
  // never conditionally unmounted — only the surrounding chrome is, once we
  // actually know whether Google sign-in is configured.
  return (
    <div style={{ marginTop: enabled ? 16 : 0 }}>
      {enabled && <div style={{ textAlign: "center", fontSize: 12, color: "#999", margin: "12px 0" }}>or</div>}
      <div ref={containerRef} />
    </div>
  );
}
