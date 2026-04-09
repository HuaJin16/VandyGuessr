<script lang="ts">
import { cn } from "$lib/shared/utils";
import { type VariantProps, tv } from "tailwind-variants";

const buttonVariants = tv({
	base: "inline-flex items-center justify-center gap-2 rounded-md text-sm font-semibold transition-all duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/25 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
	variants: {
		variant: {
			default:
				"border border-transparent bg-brand text-white shadow-xs hover:bg-brand-dark hover:-translate-y-px hover:shadow-sm",
			secondary: "border border-transparent bg-brand/10 text-brand-dark hover:bg-brand/15",
			outline: "border border-line bg-surface text-ink hover:border-brand/35 hover:bg-brand/5",
			ghost: "bg-transparent text-ink hover:bg-black/5",
			danger:
				"border border-transparent bg-danger text-white shadow-xs hover:bg-danger-dark hover:-translate-y-px hover:shadow-sm",
		},
		size: {
			default: "h-11 px-4",
			sm: "h-9 px-3 text-[13px]",
			lg: "h-12 px-6 text-[15px]",
			pill: "h-10 rounded-pill px-4 text-[13px]",
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
