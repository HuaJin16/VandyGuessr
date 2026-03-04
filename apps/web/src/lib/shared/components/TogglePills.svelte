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
	import { createEventDispatcher } from "svelte";

	export let options: ToggleOption[] = [];
	export let selected: string;
	export let ariaLabel = "Toggle options";
	export let iconSize = 14;

	const dispatch = createEventDispatcher<{ change: string }>();

	function handleClick(value: string) {
		dispatch("change", value);
	}
</script>

<div class="toggle-group" role="group" aria-label={ariaLabel}>
	{#each options as option (option.value)}
		<button
			type="button"
			class="toggle-button {selected === option.value ? 'toggle-active' : 'toggle-inactive'}"
			aria-pressed={selected === option.value}
			on:click={() => handleClick(option.value)}
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
		border-radius: var(--radius-pill);
		padding: 3px;
		gap: 3px;
		border: 1px solid var(--line);
		background: var(--surface);
		box-shadow: var(--shadow-sm);
	}

	@media (min-width: 640px) {
		.toggle-group {
			display: inline-flex;
		}
	}

	.toggle-button {
		display: inline-flex;
		flex: 1;
		align-items: center;
		justify-content: center;
		gap: 5px;
		border-radius: var(--radius-pill);
		padding: 7px 13px;
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
		border: none;
		outline: none;
		background: transparent;
		color: var(--muted);
		appearance: none;
		transition: all var(--duration-fast) var(--ease);
		text-align: center;
	}

	@media (min-width: 640px) {
		.toggle-button {
			flex: none;
		}
	}

	.toggle-button:hover {
		color: var(--ink);
		background: rgba(0, 0, 0, 0.05);
	}

	.toggle-button:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.toggle-active {
		background: var(--brand);
		color: #fff;
		box-shadow: 0 2px 0 var(--brand-dark);
	}

	.toggle-active:hover {
		background: var(--brand);
		color: #fff;
	}

	.toggle-active:focus-visible {
		box-shadow: 0 2px 0 var(--brand-dark), var(--ring);
	}
</style>
