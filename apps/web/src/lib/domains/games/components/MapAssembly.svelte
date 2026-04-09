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
		<button class="dock-toggle" type="button" on:click={toggleExpanded}>
			{expanded ? "Collapse" : "Expand"}
		</button>
	</div>

	<div class="map-wrapper">
		<GuessMap {position} on:click={handleClick} />
	</div>

	<div class="dock-footer">
		<p class="dock-note">
			{#if position}
				Your latest pin is locked in for submission until you move it again.
			{:else}
				Tap the map to place a single pin. Accuracy determines your score.
			{/if}
		</p>
		<Button class="w-full sm:w-auto" size="lg" disabled={!position || disabled} on:click={onGuess}>
			Lock Guess
		</Button>
	</div>
</section>

<style>
	.dock {
		width: 100%;
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
		border: none;
		background: transparent;
		color: var(--muted);
		font-size: 12px;
		font-weight: 700;
		cursor: pointer;
	}

	.map-wrapper {
		position: relative;
		height: 190px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		overflow: hidden;
		transition: height 200ms var(--ease);
	}

	.dock.expanded .map-wrapper {
		height: 320px;
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

	@media (min-width: 880px) {
		.dock {
			grid-column: 2;
			grid-row: 2;
			align-self: end;
		}

		.map-wrapper {
			height: 220px;
		}
	}
</style>
