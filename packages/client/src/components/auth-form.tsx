import { ArrowRight, UserRound } from "lucide-react";
import { motion } from "motion/react";
import { type FormEvent, useState } from "react";
import { Link } from "wouter";
import { auth } from "@/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!auth) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const { data, error: cause } = mode === "register"
        ? await auth.auth.signUp({ email, password })
        : await auth.auth.signInWithPassword({ email, password });
      if (cause) throw cause;
      if (mode === "register" && !data.session) {
        setNotice("Check your email to confirm your account.");
      }
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Authentication failed.");
    } finally { setBusy(false); }
  }

  async function continueAsGuest() {
    if (!auth) return;
    setBusy(true);
    setError("");
    try {
      const { error: cause } = await auth.auth.signInAnonymously();
      if (cause) throw cause;
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "Guest sign-in failed.");
    } finally { setBusy(false); }
  }

  return (
    <motion.section initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
      className="mx-auto my-12 w-full max-w-md rounded-2xl border border-border bg-card p-7 shadow-sm sm:p-9">
      <h1 className="text-3xl font-semibold">{mode === "register" ? "Create an account" : "Sign in to play"}</h1>
      <p className="mt-2 text-sm text-muted-foreground">Use your account or join as a guest.</p>
      {!auth && <p role="alert" className="mt-5 rounded-lg border border-border p-3 text-sm">
        Supabase project configuration is required for sign-in.
      </p>}
      <form onSubmit={(event) => { void submit(event); }} className="mt-7 space-y-4">
        <label className="block text-sm font-medium" htmlFor="email">Email</label>
        <Input id="email" type="email" autoComplete="email" required value={email}
          onChange={(event) => setEmail(event.target.value)} />
        <label className="block text-sm font-medium" htmlFor="password">Password</label>
        <Input id="password" type="password" minLength={6} required
          autoComplete={mode === "register" ? "new-password" : "current-password"}
          value={password} onChange={(event) => setPassword(event.target.value)} />
        <Button className="w-full" type="submit" disabled={busy || !auth}>
          {busy ? "Connecting…" : mode === "register" ? "Create account" : "Sign in"}
          <ArrowRight size={16} />
        </Button>
      </form>
      <div className="mt-5 flex flex-col gap-3 border-t border-border pt-5">
        <Button variant="outline" disabled={busy || !auth}
          onClick={() => { void continueAsGuest(); }}>
          <UserRound size={16} /> Continue as guest
        </Button>
        <Link href={mode === "login" ? "/register" : "/login"}
          className="text-center text-sm underline underline-offset-4">
          {mode === "login" ? "Create an account" : "Already have an account? Sign in"}
        </Link>
      </div>
      {notice && <p role="status" className="mt-4 text-sm">{notice}</p>}
      {error && <p role="alert" className="mt-4 text-sm text-red-600 dark:text-red-400">{error}</p>}
    </motion.section>
  );
}
