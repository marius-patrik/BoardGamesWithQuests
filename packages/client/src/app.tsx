import type { Session } from "@supabase/supabase-js";
import { ArrowRight, LoaderCircle, LogOut, UserRound } from "lucide-react";
import { motion } from "motion/react";
import { type FormEvent, useEffect, useState } from "react";
import { auth } from "@/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type Definition = {
	id: string;
	file: string;
	title: string;
	board?: { rows: number; columns: number };
};
type View = "login" | "register";

export function App() {
	const [session, setSession] = useState<Session | null>(null);
	const [initialized, setInitialized] = useState(false);
	const [view, setView] = useState<View>("login");
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState("");
	const [notice, setNotice] = useState("");
	const [definitions, setDefinitions] = useState<Definition[]>([]);
	const [selected, setSelected] = useState<string | null>(null);

	useEffect(() => {
		if (!auth) {
			setInitialized(true);
			return;
		}
		const client = auth;
		let active = true;
		const {
			data: { subscription },
		} = client.auth.onAuthStateChange((_event, value) => {
			if (active) {
				setSession(value);
				setInitialized(true);
			}
		});
		void client.auth
			.getSession()
			.then(({ data, error: sessionError }) => {
				if (!active) return;
				if (sessionError) setError(sessionError.message);
				setSession(data.session);
				setInitialized(true);
			})
			.catch((cause: unknown) => {
				if (active) {
					setError(
						cause instanceof Error
							? cause.message
							: "Unable to load your session.",
					);
					setInitialized(true);
				}
			});
		return () => {
			active = false;
			subscription.unsubscribe();
		};
	}, []);

	useEffect(() => {
		if (!session) return;
		const controller = new AbortController();
		void fetch(
			`${(import.meta.env.PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "")}/api/definitions`,
			{ signal: controller.signal },
		)
			.then((response) => {
				if (!response.ok) throw new Error("Cannot load the game catalog.");
				return response.json() as Promise<{ definitions: Definition[] }>;
			})
			.then((payload) => setDefinitions(payload.definitions))
			.catch((cause: unknown) => {
				if (!controller.signal.aborted)
					setError(
						cause instanceof Error
							? cause.message
							: "Cannot load game definitions.",
					);
			});
		return () => controller.abort();
	}, [session]);

	async function passwordSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		if (!auth) return;
		setBusy(true);
		setError("");
		setNotice("");
		try {
			const { data, error: authError } =
				view === "register"
					? await auth.auth.signUp({ email, password })
					: await auth.auth.signInWithPassword({ email, password });
			if (authError) throw authError;
			if (view === "register" && !data.session)
				setNotice("Check your email to confirm your account.");
		} catch (cause) {
			setError(
				cause instanceof Error ? cause.message : "Authentication failed.",
			);
		} finally {
			setBusy(false);
		}
	}

	async function guestSignIn() {
		if (!auth) return;
		setBusy(true);
		setError("");
		setNotice("");
		try {
			const { error: authError } = await auth.auth.signInAnonymously();
			if (authError) throw authError;
		} catch (cause) {
			setError(
				cause instanceof Error ? cause.message : "Guest sign-in failed.",
			);
		} finally {
			setBusy(false);
		}
	}

	async function signOut() {
		if (!auth) return;
		setBusy(true);
		setError("");
		const { error: signOutError } = await auth.auth.signOut();
		if (signOutError) setError(signOutError.message);
		setSelected(null);
		setBusy(false);
	}

	return (
		<main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-5 py-7 sm:px-8">
			<header className="flex items-center justify-between border-b border-border pb-6">
				<div className="flex items-center gap-3 text-sm font-semibold tracking-wide sm:text-base">
					<img src="/icon.svg" alt="" className="size-9 rounded-lg" />{" "}
					BoardGamesWithQuests
				</div>
				{session && (
					<Button
						size="sm"
						variant="outline"
						disabled={busy}
						onClick={() => {
							void signOut();
						}}
					>
						<LogOut size={16} /> Sign out
					</Button>
				)}
			</header>
			{!initialized ? (
				<section
					className="flex flex-1 items-center justify-center"
					role="status"
				>
					<LoaderCircle className="animate-spin" aria-label="Loading session" />
				</section>
			) : !session ? (
				<section className="flex flex-1 items-center justify-center py-12">
					<motion.div
						initial={{ opacity: 0, y: 12 }}
						animate={{ opacity: 1, y: 0 }}
						className="w-full max-w-md rounded-2xl border border-border bg-card p-7 shadow-sm sm:p-9"
					>
						<h1 className="text-3xl font-semibold">
							{view === "register" ? "Create an account" : "Sign in to play"}
						</h1>
						<p className="mt-2 text-sm text-muted-foreground">
							Use your account or join as a guest.
						</p>
						{!auth && (
							<p
								role="alert"
								className="mt-5 rounded-lg border border-border p-3 text-sm"
							>
								Supabase project configuration is required for sign-in.
							</p>
						)}
						<form
							onSubmit={(event) => {
								void passwordSubmit(event);
							}}
							className="mt-7 space-y-4"
						>
							<label className="block text-sm font-medium" htmlFor="email">
								Email
							</label>
							<Input
								id="email"
								type="email"
								autoComplete="email"
								required
								value={email}
								onChange={(event) => setEmail(event.target.value)}
							/>
							<label className="block text-sm font-medium" htmlFor="password">
								Password
							</label>
							<Input
								id="password"
								type="password"
								minLength={6}
								autoComplete={
									view === "register" ? "new-password" : "current-password"
								}
								required
								value={password}
								onChange={(event) => setPassword(event.target.value)}
							/>
							<Button className="w-full" type="submit" disabled={busy || !auth}>
								{busy
									? "Connecting…"
									: view === "register"
										? "Create account"
										: "Sign in"}{" "}
								<ArrowRight size={16} />
							</Button>
						</form>
						<div className="mt-5 flex flex-col gap-3 border-t border-border pt-5">
							<Button
								variant="outline"
								disabled={busy || !auth}
								onClick={() => {
									void guestSignIn();
								}}
							>
								<UserRound size={16} /> Continue as guest
							</Button>
							<Button
								variant="ghost"
								onClick={() => {
									setView(view === "login" ? "register" : "login");
									setError("");
									setNotice("");
								}}
							>
								{view === "login"
									? "Create an account"
									: "Already have an account? Sign in"}
							</Button>
						</div>
						{notice && (
							<p role="status" className="mt-4 text-sm">
								{notice}
							</p>
						)}
						{error && (
							<p
								role="alert"
								className="mt-4 text-sm text-red-600 dark:text-red-400"
							>
								{error}
							</p>
						)}
					</motion.div>
				</section>
			) : (
				<section className="flex-1 py-12">
					<motion.div
						initial={{ opacity: 0, y: 12 }}
						animate={{ opacity: 1, y: 0 }}
					>
						<p className="text-sm text-muted-foreground">
							{session.user.is_anonymous ? "Guest session" : session.user.email}
						</p>
						<h1 className="mt-3 text-4xl font-semibold tracking-tight">
							Your games
						</h1>
						<p className="mt-3 max-w-xl text-muted-foreground">
							Choose a game definition to inspect its board and rules.
						</p>
						<div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
							{definitions.map((game) => (
								<button
									key={game.id}
									type="button"
									onClick={() => setSelected(game.id)}
									aria-pressed={selected === game.id}
									className="rounded-2xl border border-border bg-card p-6 text-left transition hover:border-ring focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
								>
									<h2 className="text-xl font-semibold">{game.title}</h2>
									<p className="mt-3 text-sm text-muted-foreground">
										{game.board
											? game.board.columns + " × " + game.board.rows + " board"
											: "Configurable board"}
									</p>
									<p className="mt-6 text-sm">
										Inspect definition <ArrowRight className="inline size-4" />
									</p>
								</button>
							))}
						</div>
						{selected && (
							<p role="status" className="mt-6 text-sm text-muted-foreground">
								Selected definition:{" "}
								{definitions.find((game) => game.id === selected)?.title}. Game
								sessions are created through the authenticated server API.
							</p>
						)}
						{error && (
							<p
								role="alert"
								className="mt-5 text-sm text-red-600 dark:text-red-400"
							>
								{error}
							</p>
						)}
					</motion.div>
				</section>
			)}
		</main>
	);
}
