<script lang="ts">
import { cn } from "$lib/shared/utils";

export let eyebrow = "";
export let title = "";
export let copy = "";
export let split = false;

let className = "";
export { className as class };
</script>

<header class={cn("page-header", split && "page-header--split", className)} {...$$restProps}>
	<div class="grid gap-3">
		{#if eyebrow}
			<p class="page-header__eyebrow">{eyebrow}</p>
		{/if}
		{#if title}
			<h1 class="page-header__title">{title}</h1>
		{/if}
		{#if copy}
			<p class="page-header__copy">{copy}</p>
		{/if}
	</div>
	{#if $$slots.actions}
		<div class="flex flex-wrap items-center gap-3">
			<slot name="actions" />
		</div>
	{/if}
</header>
