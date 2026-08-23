"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "./api";

/** Redirects to /login if there's no token yet. Returns whether auth has
 * been checked (avoids a flash of protected content before the redirect). */
export function useRequireAuth(): boolean {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    } else {
      setReady(true);
    }
  }, [router]);

  return ready;
}
