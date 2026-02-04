<script lang="ts">
import { cn } from "$lib/shared/utils";
import { type VariantProps, tv } from "tailwind-variants";

const buttonVariants = tv({
	base: "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
	variants: {
		variant: {
			default: "bg-neutral-900 text-white hover:bg-neutral-800",
			outline: "border border-neutral-300 bg-transparent hover:bg-neutral-100",
			ghost: "hover:bg-neutral-100",
		},
		size: {
			default: "h-10 px-4 py-2",
			sm: "h-9 px-3",
			lg: "h-11 px-8",
		},
	},
	defaultVariants: {
		variant: "default",
		size: "default",
	},
});

type ButtonVariants = VariantProps<typeof buttonVariants>;

export let variant: ButtonVariants["variant"] = "default";
export let size: ButtonVariants["size"] = "default";
export let disabled = false;
let className = "";
export { className as class };
</script>

<button
	class={cn(buttonVariants({ variant, size }), className)}
	{disabled}
	on:click
	{...$$restProps}
>
	<slot />
</button>
