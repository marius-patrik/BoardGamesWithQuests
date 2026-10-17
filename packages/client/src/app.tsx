import { LoaderCircle } from "lucide-react";
import { useState } from "react";
import { Link, Redirect, Route, Switch } from "wouter";
import { auth } from "@/auth";
import { AppHeader } from "@/components/app-header";
import { useAuthSession } from "@/hooks/use-auth-session";
import { AuthPage } from "@/pages/auth-page";
import { GamesPage } from "@/pages/games-page";

export function App() {
	const { session, initialized, error: sessionError } = useAuthSession();
	const [signingOut, setSigningOut] = useState(false);
	const [signOutError, setSignOutError] = useState<string | null>(null);
	async function signOut() {
		if (!auth) return;
		setSigningOut(true);
		setSignOutError(null);
		const { error } = await auth.auth.signOut();
		if (error) setSignOutError(error.message);
		setSigningOut(false);
	}
	return (
		<main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-5 py-7 sm:px-8">
			<AppHeader
				signedIn={Boolean(session)}
				busy={signingOut}
				onSignOut={() => {
					void signOut();
				}}
			/>
			{(sessionError || signOutError) && (
				<p role="alert" className="mt-4 text-sm text-red-600 dark:text-red-400">
					{sessionError || signOutError}
				</p>
			)}
			{!initialized ? (
				<section
					className="flex flex-1 items-center justify-center"
					role="status"
				>
					<LoaderCircle className="animate-spin" aria-label="Loading session" />
				</section>
			) : (
				<Switch>
					<Route path="/login">
						{session ? <Redirect to="/games" /> : <AuthPage mode="login" />}
					</Route>
					<Route path="/register">
						{session ? <Redirect to="/games" /> : <AuthPage mode="register" />}
					</Route>
					<Route path="/games">
						{session ? (
							<GamesPage session={session} />
						) : (
							<Redirect to="/login" />
						)}
					</Route>
					<Route path="/">
						<Redirect to={session ? "/games" : "/login"} />
					</Route>
					<Route>
						<section className="py-12">
							<h1 className="text-3xl font-semibold">Page not found</h1>
							<Link href="/games" className="mt-3 inline-block underline">
								Back to games
							</Link>
						</section>
					</Route>
				</Switch>
			)}
		</main>
	);
}
