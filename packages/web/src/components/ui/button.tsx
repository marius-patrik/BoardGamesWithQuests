import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
	"inline-flex cursor-pointer items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
	{
		variants: {
			variant: {
				default: "bg-primary text-primary-foreground hover:bg-primary/90",
				outline: "border border-border bg-background hover:bg-accent",
				ghost: "hover:bg-accent",
			},
			size: {
				default: "h-10 px-4 py-2",
				sm: "h-8 px-3",
				lg: "h-12 px-6",
			},
		},
		defaultVariants: { variant: "default", size: "default" },
	},
);

export type ButtonProps = ComponentProps<"button"> &
	VariantProps<typeof buttonVariants> & { asChild?: boolean };

export function Button({
	asChild = false,
	className,
	variant,
	size,
	...props
}: ButtonProps) {
	const Component = asChild ? Slot : "button";
	return (
		<Component
			data-slot="button"
			className={cn(buttonVariants({ variant, size, className }))}
			{...props}
		/>
	);
}
