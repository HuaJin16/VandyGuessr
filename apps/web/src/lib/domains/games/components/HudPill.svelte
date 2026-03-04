<script lang="ts">
export let round: number;
export let totalRounds: number;
export let score: number;
export let timer: string | null = null;
export let timerDanger = false;
export let showCheck = false;
</script>

<section class="hud" aria-label="Gameplay status">
	<div class="hud-cell">
		<span class="hud-label">Round</span>
		<span class="hud-value">{round}/{totalRounds}</span>
	</div>
	<div class="hud-cell">
		<span class="hud-label">Score</span>
		<span class="hud-value score">{score.toLocaleString()}</span>
	</div>
	{#if timer !== null}
		<div class="hud-cell">
			{#if showCheck}
				<span class="hud-label" style="color: var(--brand);">&#10003;</span>
			{:else}
				<span class="hud-label">Time</span>
			{/if}
			<span class="hud-value" class:timer={timerDanger} class:score={showCheck && !timerDanger}>{timer}</span>
		</div>
	{/if}
</section>

<style>
	.hud {
		pointer-events: auto;
		display: inline-flex;
		align-items: center;
		gap: 0;
		border: 1px solid var(--line);
		border-radius: var(--radius-pill);
		background: rgba(255, 255, 255, 0.95);
		color: var(--ink);
		box-shadow: var(--shadow-md);
		padding: 6px 4px;
		width: min(100%, 540px);
		justify-content: center;
	}

	.hud-cell {
		padding: 4px 12px;
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.hud-cell + .hud-cell {
		border-left: 1px solid var(--line);
	}

	.hud-label {
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.hud-value {
		font-family: "IBM Plex Mono", monospace;
		font-size: 14px;
		font-weight: 600;
		color: var(--ink);
	}

	.hud-value.score {
		color: var(--gold-dark);
	}

	.hud-value.timer {
		color: var(--danger);
	}

	@media (max-width: 400px) {
		.hud {
			padding: 4px 2px;
		}

		.hud-cell {
			padding: 3px 8px;
			gap: 4px;
		}

		.hud-label {
			font-size: 10px;
		}

		.hud-value {
			font-size: 12px;
		}
	}
</style>
