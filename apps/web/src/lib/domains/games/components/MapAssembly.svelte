<script lang="ts">
import GuessMap from "./GuessMap.svelte";

export let position: { lat: number; lng: number } | null = null;
export let disabled = false;

export let onMapClick: (pos: { lat: number; lng: number }) => void;
export let onGuess: () => void;

let expanded = false;

function handleClick(e: CustomEvent<{ lat: number; lng: number }>) {
	onMapClick(e.detail);
}
</script>

<!-- svelte-ignore a11y-no-static-element-interactions -->
<section
	class="dock"
	class:expanded
	aria-label="Map assembly"
	on:mouseenter={() => { expanded = true; }}
	on:mouseleave={() => { expanded = false; }}
>
	<p class="dock-overline">Place Your Guess</p>
	<div class="map-wrapper">
		<GuessMap {position} on:click={handleClick} />
	</div>
	<button
		class="guess-btn"
		disabled={!position || disabled}
		on:click={onGuess}
	>
		Lock Guess
	</button>
	{#if !position}
		<p class="dock-note">Tap map to move marker. Pin position determines your distance score.</p>
	{/if}
</section>

<style>
	.dock {
		border: 1px solid rgba(255, 255, 255, 0.55);
		border-radius: var(--radius-lg);
		background: rgba(255, 255, 255, 0.96);
		color: var(--ink);
		box-shadow: var(--shadow-md);
		padding: 10px;
		backdrop-filter: blur(6px);
		width: 100%;
		transition: all 200ms var(--ease);
		pointer-events: auto;
	}

	.dock-overline {
		margin: 0;
		color: var(--muted);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.map-wrapper {
		position: relative;
		margin-top: 8px;
		height: 180px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		overflow: hidden;
		transition: height 200ms var(--ease);
	}

	.dock.expanded .map-wrapper {
		height: 260px;
	}

	.guess-btn {
		width: 100%;
		margin-top: 10px;
		border: none;
		border-radius: var(--radius-md);
		background: var(--brand);
		color: #fff;
		font-family: Inter, sans-serif;
		font-size: 16px;
		font-weight: 700;
		padding: 13px 14px;
		box-shadow: 0 4px 0 var(--brand-dark);
		cursor: pointer;
		transition: all 120ms var(--ease);
	}

	.guess-btn:hover:not(:disabled) {
		background: #278234;
	}

	.guess-btn:active:not(:disabled) {
		transform: translateY(4px);
		box-shadow: 0 0 0 var(--brand-dark);
	}

	.guess-btn:focus-visible {
		outline: none;
		box-shadow: 0 4px 0 var(--brand-dark), var(--ring);
	}

	.guess-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.dock-note {
		margin: 8px 0 0;
		color: var(--muted);
		font-size: 12px;
		line-height: 1.35;
	}

	/* Mobile: dock is part of grid flow, takes full width */
	@media (max-width: 879px) {
		.dock {
			align-self: end;
		}
	}

	@media (max-width: 400px) {
		.dock {
			padding: 8px;
		}

		.guess-btn {
			font-size: 14px;
			padding: 11px 12px;
		}

		.dock-note {
			font-size: 11px;
		}
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

		.dock.expanded .map-wrapper {
			height: 300px;
		}
	}
</style>
