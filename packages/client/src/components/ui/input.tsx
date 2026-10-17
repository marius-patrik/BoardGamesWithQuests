import type { ComponentProps } from "react";
import { mergeClassNames } from "@/lib/class-names";

// shadcn/ui input: owned, accessible primitive, composed with a real <label>.
export function Input({ className, type, ...props }: ComponentProps<"input">) {
	return (
		<input
			type={type}
			data-slot="input"
			className={mergeClassNames(
				"flex h-10 w-full min-w-0 rounded-md border border-border bg-background px-3 py-2 text-sm outline-none transition-shadow placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
				className,
			)}
			{...props}
		/>
	);
}
