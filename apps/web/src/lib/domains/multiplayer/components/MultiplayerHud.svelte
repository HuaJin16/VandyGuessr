<script lang="ts">
import type { Standing } from "../types";

export let currentRound: number;
export let totalRounds: number;
export let timeRemaining: number | null;
export let standings: Standing[];
export let hasGuessed: boolean;
export let playersGuessedCount: number;
export let totalPlayers: number;

$: minutes = timeRemaining !== null ? Math.floor(timeRemaining / 60) : 0;
$: seconds = timeRemaining !== null ? timeRemaining % 60 : 0;
$: timerUrgent = timeRemaining !== null && timeRemaining <= 15;
</script>

<div class="hud">
	<div class="hud-pill round-pill">
		<span class="hud-label">Round</span>
		<span class="hud-value">{currentRound}/{totalRounds}</span>
	</div>

	<div class="hud-pill timer-pill" class:urgent={timerUrgent}>
		<span class="hud-value timer-value">
			{minutes}:{seconds.toString().padStart(2, "0")}
		</span>
	</div>

	<div class="hud-pill guess-pill">
		{#if hasGuessed}
			<span class="hud-value guessed">Guess Locked</span>
		{:else}
			<span class="hud-label">Guesses</span>
			<span class="hud-value">{playersGuessedCount}/{totalPlayers}</span>
		{/if}
	</div>
</div>

{#if standings.length > 0}
	<div class="standings-strip">
		{#each standings as standing, i (standing.userId)}
			<div class="standing-item" class:leader={i === 0}>
				<span class="rank">#{standing.rank}</span>
				<span class="standing-name">{standing.name}</span>
				<span class="standing-score">{standing.totalScore.toLocaleString()}</span>
			</div>
		{/each}
	</div>
{/if}

<style>
	.hud {
		display: flex;
		gap: 8px;
		justify-content: center;
		align-items: center;
		pointer-events: auto;
	}
	.hud-label {
		font-size: 0.625rem;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #636363;
	}
	.hud-value {
		font-family: "Rubik", sans-serif;
		font-weight: 700;
		font-size: 0.9375rem;
		color: #18181b;
	}
	.round-pill, .guess-pill {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
		padding: 6px 14px;
	}
	.timer-pill {
		padding: 8px 18px;
	}
	.timer-value {
		font-size: 1.25rem;
		font-variant-numeric: tabular-nums;
	}
	.timer-pill.urgent .timer-value {
		color: #d95d39;
		animation: pulse 1s ease-in-out infinite;
	}
	.guessed {
		font-size: 0.8125rem;
		color: #2e933c;
	}
	.standings-strip {
		display: flex;
		gap: 6px;
		justify-content: center;
		margin-top: 6px;
		pointer-events: auto;
	}
	.standing-item {
		display: flex;
		align-items: center;
		gap: 4px;
		font-family: "Rubik", sans-serif;
		font-size: 0.75rem;
		color: #636363;
		background: rgba(255, 255, 255, 0.85);
		padding: 3px 8px;
		border-radius: 9999px;
	}
	.standing-item.leader {
		color: #18181b;
		font-weight: 600;
	}
	.rank {
		font-weight: 700;
		color: #f4c430;
	}
	.standing-score {
		font-variant-numeric: tabular-nums;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}
</style>
