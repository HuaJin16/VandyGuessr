<script lang="ts">
import { cn } from "$lib/shared/utils";

export let tone: "default" | "subtle" = "default";

let className = "";
export { className as class };
</script>

<div
	class={cn(
		"card-base",
		tone === "subtle" && "card-base--subtle",
		className,
	)}
	{...$$restProps}
>
	<slot />
</div>

<style>
	.card-base {
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-xs);
		padding: 16px;
	}

	.card-base--subtle {
		background: var(--surface-subtle);
		box-shadow: none;
	}

	@media (min-width: 640px) {
		.card-base {
			padding: 20px;
		}
	}
</style>
