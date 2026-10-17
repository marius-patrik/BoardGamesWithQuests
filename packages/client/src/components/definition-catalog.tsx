import { ArrowRight } from "lucide-react";
import { useEffect, useState } from "react";

type Definition = {
	id: string;
	title: string;
	board?: { rows: number; columns: number };
};

export function DefinitionCatalog() {
	const [definitions, setDefinitions] = useState<Definition[]>([]);
	const [selected, setSelected] = useState<string | null>(null);
	const [error, setError] = useState<string | null>(null);
	useEffect(() => {
		const controller = new AbortController();
		const base = (import.meta.env.PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");
		void fetch(`${base}/api/definitions`, { signal: controller.signal })
			.then((response) => {
				if (!response.ok) throw new Error("Cannot load the game catalog.");
				return response.json() as Promise<{ definitions: Definition[] }>;
			})
			.then(({ definitions: items }) => setDefinitions(items))
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
						<h2 className="text-xl font-semibold">{game.title}</h2>
						<p className="mt-3 text-sm text-muted-foreground">
							{game.board
								? `${game.board.columns} × ${game.board.rows} board`
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
					Selected: {definitions.find((game) => game.id === selected)?.title}.
					Gameplay is provided by the authoritative game service, not the public
					catalog.
				</p>
			)}
		</section>
	);
}
