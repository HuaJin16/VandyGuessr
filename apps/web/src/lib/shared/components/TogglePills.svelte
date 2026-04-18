<script lang="ts" context="module">
import type { IconProps } from "lucide-svelte";
import type { SvelteComponentTyped } from "svelte";

type IconComponent = typeof SvelteComponentTyped<IconProps>;

export type ToggleOption = {
	value: string;
	label: string;
	icon?: IconComponent;
};
</script>

<script lang="ts">
	import { createEventDispatcher, tick } from "svelte";

	export let options: ToggleOption[] = [];
	export let selected: string;
	export let ariaLabel = "Toggle options";
	export let iconSize = 14;

	const dispatch = createEventDispatcher<{ change: string }>();

	$: selectedIndex = options.findIndex((o) => o.value === selected);

	function handleClick(value: string) {
		dispatch("change", value);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
		e.preventDefault();
		const dir = e.key === "ArrowRight" ? 1 : -1;
		const next = (selectedIndex + dir + options.length) % options.length;
		dispatch("change", options[next].value);
		tick().then(() => {
			const group = (e.currentTarget as HTMLElement)?.closest("[role='radiogroup']");
			const radios = group?.querySelectorAll<HTMLButtonElement>("[role='radio']");
			radios?.[next]?.focus();
		});
	}
</script>

<div class="toggle-group" role="radiogroup" aria-label={ariaLabel}>
	{#each options as option (option.value)}
		<button
			type="button"
			class="toggle-btn"
			class:toggle-btn--active={selected === option.value}
			role="radio"
			aria-checked={selected === option.value}
			tabindex={selected === option.value ? 0 : -1}
			on:click={() => handleClick(option.value)}
			on:keydown={handleKeydown}
		>
			{#if option.icon}
				<span aria-hidden="true">
					<svelte:component this={option.icon} size={iconSize} />
				</span>
			{/if}
			<span>{option.label}</span>
		</button>
	{/each}
</div>

<style>
	.toggle-group {
		display: flex;
		flex-wrap: wrap;
		width: 100%;
		border-radius: var(--radius-sm);
		padding: 3px;
		border: 1px solid var(--line);
		background: var(--surface-strong);
		gap: 3px;
	}

	.toggle-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 5px;
		border-radius: 6px;
		padding: 8px 12px;
		min-height: 44px;
		min-width: 0;
		flex: 1 1 0;
		font-size: 14px;
		font-weight: 500;
		cursor: pointer;
		border: none;
		outline: none;
		background: transparent;
		color: var(--muted);
		appearance: none;
		white-space: normal;
		text-align: center;
		line-height: 1.2;
		transition: color var(--duration-fast) var(--ease),
			background var(--duration-fast) var(--ease);
	}

	.toggle-btn:hover:not(.toggle-btn--active) {
		color: var(--ink);
	}

	.toggle-btn:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.toggle-btn--active {
		background: var(--brand);
		color: #fff;
		font-weight: 600;
	}

	@media (min-width: 640px) {
		.toggle-group {
			display: inline-flex;
			flex-wrap: nowrap;
			width: auto;
		}

		.toggle-btn {
			min-height: 40px;
			flex: 0 1 auto;
			padding: 6px 12px;
			font-size: 13px;
			white-space: nowrap;
		}
	}
</style>
