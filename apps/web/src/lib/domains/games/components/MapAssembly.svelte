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
<div
	class="map-assembly"
	class:expanded
	on:mouseenter={() => { expanded = true; }}
	on:mouseleave={() => { expanded = false; }}
>
	<div class="map-wrapper">
		<GuessMap {position} on:click={handleClick} />
		{#if !position}
			<div class="map-hint">Click to place your guess</div>
		{/if}
	</div>
	<button
		class="btn-3d guess-btn"
		disabled={!position || disabled}
		on:click={onGuess}
	>
		GUESS
	</button>
</div>

<style>
	.map-assembly {
		position: fixed;
		bottom: 20px;
		right: 20px;
		z-index: 40;
		display: flex;
		flex-direction: column;
		gap: 10px;
		width: 300px;
		transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1),
		            height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.map-assembly.expanded {
		width: 480px;
	}

	.map-wrapper {
		position: relative;
		height: 200px;
		border-radius: 12px;
		overflow: hidden;
		box-shadow: 4px 4px 0px 0px rgba(0, 0, 0, 0.1);
		border: 2px solid rgba(255, 255, 255, 0.5);
		transition: height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}

	.map-assembly.expanded .map-wrapper {
		height: 320px;
	}

	.map-hint {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		text-align: center;
		padding: 8px;
		background: rgba(0, 0, 0, 0.6);
		color: white;
		font-size: 12px;
		font-weight: 500;
		pointer-events: none;
	}

	.guess-btn {
		width: 100%;
		padding: 14px;
		font-size: 16px;
		font-weight: 700;
		letter-spacing: 0.05em;
		background: #2e933c;
		color: white;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		box-shadow: 0 6px 0 #236e2d;
		transition: transform 0.1s, box-shadow 0.1s;
	}

	.guess-btn:active:not(:disabled) {
		transform: translateY(6px);
		box-shadow: 0 0 0 #236e2d;
	}

	.guess-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	@media (max-width: 640px) {
		.map-assembly {
			bottom: 12px;
			right: 12px;
			left: 12px;
			width: auto;
		}

		.map-assembly.expanded {
			width: auto;
		}

		.map-wrapper {
			height: 180px;
		}

		.map-assembly.expanded .map-wrapper {
			height: 180px;
		}
	}
</style>
