import type { Session } from "@supabase/supabase-js";
import { DefinitionCatalog } from "@/components/definition-catalog";

export function GamesPage({ session }: { session: Session }) {
	return (
		<>
			<p className="mt-8 text-sm text-muted-foreground">
				{session.user.is_anonymous ? "Guest session" : session.user.email}
			</p>
			<DefinitionCatalog />
		</>
	);
}
