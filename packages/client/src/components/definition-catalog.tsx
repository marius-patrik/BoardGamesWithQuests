import { ArrowRight } from "lucide-react";
import { useEffect, useState } from "react";

type Definition = {
	id: string;
	name: string;
	minimum_participants: number;
	maximum_participants: number;
};

export function DefinitionCatalog() {
	const [definitions, setDefinitions] = useState<Definition[]>([]);
	const [selected, setSelected] = useState<string | null>(null);
	const [error, setError] = useState<string | null>(null);
	useEffect(() => {
		const controller = new AbortController();
		const base = (import.meta.env.PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");
		void fetch(`${base}/api/v1/definitions`, { signal: controller.signal })
			.then((response) => {
				if (!response.ok) throw new Error("Cannot load the game catalog.");
				return response.json() as Promise<Definition[]>;
			})
			.then((items) => setDefinitions(items))
			.catch((cause: unknown) => {
				if (!controller.signal.aborted) {
					setError(
						cause instanceof Error
							? cause.message
							: "Cannot load game definitions.",
					);
				}
			});
		return () => controller.abort();
	}, []);
	return (
		<section className="py-12">
			<h1 className="text-4xl font-semibold tracking-tight">Available games</h1>
			<p className="mt-3 max-w-xl text-muted-foreground">
				Inspect published definitions.
			</p>
			{error && (
				<p role="alert" className="mt-5 text-sm text-red-600 dark:text-red-400">
					{error}
				</p>
			)}
			<div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{definitions.map((game) => (
					<button
						key={game.id}
						type="button"
						onClick={() => setSelected(game.id)}
						aria-pressed={selected === game.id}
						className="rounded-2xl border border-border bg-card p-6 text-left transition hover:border-ring focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
					>
						<h2 className="text-xl font-semibold">{game.name}</h2>
						<p className="mt-3 text-sm text-muted-foreground">
							{`${game.minimum_participants}–${game.maximum_participants} participants`}
						</p>
						<p className="mt-6 text-sm">
							Inspect definition <ArrowRight className="inline size-4" />
						</p>
					</button>
				))}
			</div>
			{selected && (
				<p role="status" className="mt-6 text-sm text-muted-foreground">
					Selected: {definitions.find((game) => game.id === selected)?.name}.
					Gameplay is provided by the authoritative game service, not the public
					catalog.
				</p>
			)}
		</section>
	);
}
