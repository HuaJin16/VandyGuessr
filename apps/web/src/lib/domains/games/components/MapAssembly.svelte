<script lang="ts">
import Button from "$lib/shared/ui/Button.svelte";
import GuessMap from "./GuessMap.svelte";

export let position: { lat: number; lng: number } | null = null;
export let disabled = false;
export let onMapClick: (pos: { lat: number; lng: number }) => void;
export let onGuess: () => void;

let expanded = false;

function handleClick(event: CustomEvent<{ lat: number; lng: number }>) {
	onMapClick(event.detail);
}

function toggleExpanded() {
	expanded = !expanded;
}
</script>

<section class="dock" class:expanded aria-label="Guess map">
	<div class="dock-header">
		<div>
			<p class="dock-overline">Guess map</p>
			<p class="dock-title">{position ? "Pin placed" : "Place your pin"}</p>
		</div>
		<button
			class="dock-toggle"
			type="button"
			aria-controls="guess-map-panel"
			aria-expanded={expanded}
			on:click={toggleExpanded}
		>
			{expanded ? "Collapse" : "Expand"}
		</button>
	</div>

	<div class="map-wrapper" id="guess-map-panel">
		<GuessMap {position} on:click={handleClick} />
	</div>

	<div class="dock-footer">
		<p class="dock-note">
			{#if position}
				Your latest pin is locked in for submission until you move it again.
			{:else if expanded}
				Tap the map to place a single pin. Accuracy determines your score.
			{:else}
				Expand the map to place a single pin, then collapse it to return to the full panorama.
			{/if}
		</p>
		<Button class="w-full lg:w-auto" size="lg" disabled={!position || disabled} on:click={onGuess}>
			Lock Guess
		</Button>
	</div>
</section>

<style>
	.dock {
		width: 100%;
		max-width: 100%;
		pointer-events: auto;
		display: grid;
		gap: 12px;
		padding: 14px;
		border: 1px solid rgba(255, 255, 255, 0.38);
		border-radius: var(--radius-lg);
		background: rgba(255, 255, 255, 0.92);
		backdrop-filter: blur(18px);
		-webkit-backdrop-filter: blur(18px);
		box-shadow: var(--shadow-md);
	}

	.dock-header {
		display: flex;
		align-items: start;
		justify-content: space-between;
		gap: 12px;
	}

	.dock-overline,
	.dock-title,
	.dock-note {
		margin: 0;
	}

	.dock-overline {
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.dock-title {
		margin-top: 4px;
		font-size: 15px;
		font-weight: 800;
		line-height: 1.2;
	}

	.dock-toggle {
		border: 1px solid var(--line);
		border-radius: var(--radius-pill);
		background: rgba(255, 255, 255, 0.82);
		color: var(--ink);
		font-size: 12px;
		font-weight: 700;
		padding: 10px 12px;
		min-height: 44px;
		cursor: pointer;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		transition: border-color var(--duration-fast) var(--ease),
			background var(--duration-fast) var(--ease);
	}

	.dock-toggle:hover {
		border-color: var(--line-strong);
		background: rgba(255, 255, 255, 0.96);
	}

	.dock-toggle:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.map-wrapper {
		position: relative;
		height: 0;
		border: 1px solid transparent;
		border-radius: var(--radius-md);
		overflow: hidden;
		opacity: 0;
		pointer-events: none;
		transition: height 200ms var(--ease), opacity var(--duration-fast) var(--ease),
			border-color var(--duration-fast) var(--ease);
	}

	.dock.expanded .map-wrapper {
		height: min(42dvh, 320px);
		opacity: 1;
		pointer-events: auto;
		border-color: var(--line);
	}

	.dock-footer {
		display: grid;
		gap: 12px;
	}

	.dock-note {
		font-size: 13px;
		line-height: 1.45;
		color: var(--muted);
	}

	@media (min-width: 1024px) {
		.dock {
			padding: 16px;
			gap: 14px;
		}

		.map-wrapper {
			height: 220px;
			opacity: 1;
			pointer-events: auto;
			border-color: var(--line);
		}

		.dock.expanded .map-wrapper {
			height: 320px;
		}
	}
</style>
