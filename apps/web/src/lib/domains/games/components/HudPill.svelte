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
		<span class="hud-value hud-value--score">{score.toLocaleString()}</span>
	</div>
	{#if timer !== null}
		<div class="hud-cell">
			{#if showCheck}
				<span class="hud-label hud-label--check">Done</span>
			{:else}
				<span class="hud-label">Time</span>
			{/if}
			<span class="hud-value" class:hud-value--timer={timerDanger} class:hud-value--ok={showCheck && !timerDanger}>
				{timer}
			</span>
		</div>
	{/if}
</section>

<style>
	.hud {
		pointer-events: auto;
		display: inline-flex;
		align-items: center;
		gap: 0;
		border-radius: var(--radius-pill);
		background: rgba(255, 255, 255, 0.92);
		backdrop-filter: blur(18px);
		-webkit-backdrop-filter: blur(18px);
		border: 1px solid rgba(255, 255, 255, 0.6);
		box-shadow: var(--shadow-md);
		padding: 6px 4px;
		max-width: min(100%, 560px);
	}

	.hud-cell {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding: 5px 14px;
	}

	.hud-cell + .hud-cell {
		border-left: 1px solid rgba(28, 25, 23, 0.08);
	}

	.hud-label {
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.hud-label--check {
		color: var(--brand-dark);
	}

	.hud-value {
		font-family: "IBM Plex Mono", monospace;
		font-size: 14px;
		font-weight: 600;
		color: var(--ink);
	}

	.hud-value--score {
		color: var(--gold-dark);
	}

	.hud-value--timer {
		color: var(--danger);
	}

	.hud-value--ok {
		color: var(--brand-dark);
	}

	@media (max-width: 480px) {
		.hud {
			padding: 4px 2px;
		}

		.hud-cell {
			padding: 4px 10px;
			gap: 6px;
		}

		.hud-label {
			font-size: 9px;
		}

		.hud-value {
			font-size: 12px;
		}
	}
</style>
