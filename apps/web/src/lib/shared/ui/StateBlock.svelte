<script lang="ts">
import { cn } from "$lib/shared/utils";

export let title = "";
export let copy = "";
export let tone: "default" | "soft" | "error" = "default";

let className = "";
export { className as class };
</script>

<div
	class={cn(
		"state-block",
		tone === "soft" && "state-block--soft",
		tone === "error" && "state-block--error",
		className,
	)}
	{...$$restProps}
>
	{#if $$slots.icon}
		<div>
			<slot name="icon" />
		</div>
	{/if}
	{#if title}
		<p class="state-block__title">{title}</p>
	{/if}
	{#if copy}
		<p class="state-block__copy">{copy}</p>
	{/if}
	{#if $$slots.default}
		<div class="flex flex-wrap items-center justify-center gap-3">
			<slot />
		</div>
	{/if}
</div>
