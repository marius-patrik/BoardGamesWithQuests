import type { Session } from "@supabase/supabase-js";
import { useEffect, useState } from "react";
import { auth } from "@/auth";

export function useAuthSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [initialized, setInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!auth) {
      setInitialized(true);
      return;
    }
    let active = true;
    const { data: { subscription } } = auth.auth.onAuthStateChange((_event, current) => {
      if (active) { setSession(current); setInitialized(true); }
    });
    void auth.auth.getSession().then(({ data, error: cause }) => {
      if (!active) return;
      if (cause) setError(cause.message);
      setSession(data.session);
      setInitialized(true);
    }).catch((cause: unknown) => {
      if (active) {
        setError(cause instanceof Error ? cause.message : "Unable to load session");
        setInitialized(true);
      }
    });
    return () => { active = false; subscription.unsubscribe(); };
  }, []);
  return { session, initialized, error };
}
