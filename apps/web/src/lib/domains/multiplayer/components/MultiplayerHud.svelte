<script lang="ts">
export let currentRound: number;
export let totalRounds: number;
export let timeRemaining: number | null;
export let totalScore: number;
export let playersGuessedCount: number;
export let totalPlayers: number;

$: minutes = timeRemaining !== null ? Math.floor(timeRemaining / 60) : 0;
$: seconds = timeRemaining !== null ? timeRemaining % 60 : 0;
$: timerUrgent = timeRemaining !== null && timeRemaining <= 15;
</script>

<section class="hud" aria-label="Multiplayer gameplay status">
	<div class="hud-cell">
		<span class="hud-label">Round</span>
		<span class="hud-value">{currentRound}/{totalRounds}</span>
	</div>
	<div class="hud-cell">
		<span class="hud-label">Score</span>
		<span class="hud-value hud-value--score">{totalScore.toLocaleString()}</span>
	</div>
	<div class="hud-cell">
		<span class="hud-label">Time</span>
		<span class="hud-value hud-value--timer" class:urgent={timerUrgent}>{minutes}:{seconds.toString().padStart(2, "0")}</span>
	</div>
	<div class="hud-cell">
		<span class="hud-label">Guessed</span>
		<span class="hud-value hud-value--mp">{playersGuessedCount}/{totalPlayers}</span>
	</div>
</section>

<style>
	.hud {
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
		max-width: min(100%, 620px);
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

	.hud-value--timer.urgent {
		animation: pulse 1s ease-in-out infinite;
	}

	.hud-value--mp {
		color: var(--mp);
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
		}

		50% {
			opacity: 0.5;
		}
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
