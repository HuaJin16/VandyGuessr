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
			class={`toggle-button ${selected === option.value ? "toggle-active" : "toggle-inactive"}`}
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
		border-radius: 9999px;
		padding: 4px;
		border: 1px solid rgba(0, 0, 0, 0.08);
		background: white;
		box-shadow: 4px 4px 0px 0px rgba(0, 0, 0, 0.1);
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
		border-radius: 9999px;
		padding: 7px 16px;
		font-size: 13px;
		transition: all 0.15s;
		cursor: pointer;
		border: none;
		outline: none;
		background: transparent;
		color: #18181b;
		font-weight: 500;
		appearance: none;
	}

	@media (min-width: 640px) {
		.toggle-button {
			flex: none;
		}
	}

	.toggle-button:focus-visible {
		box-shadow: 0 0 0 2px rgba(46, 147, 60, 0.35);
	}

	.toggle-active {
		background: #2e933c;
		color: white;
		font-weight: 600;
	}

	.toggle-inactive:hover {
		background: rgba(46, 147, 60, 0.08);
	}
</style>
