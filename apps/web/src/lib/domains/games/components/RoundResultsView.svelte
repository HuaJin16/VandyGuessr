<script lang="ts">
import type { Game, Round } from "../types";
import HudPill from "./HudPill.svelte";
import ProgressDots from "./ProgressDots.svelte";
import ResultsMap from "./ResultsMap.svelte";

export let game: Game;
export let round: Round;
export let roundIndex: number;
export let onNextRound: () => void | Promise<void>;
export let onFinish: () => void;
export let isTransitioning = false;

$: isLastRound = roundIndex >= game.rounds.length - 1;
$: roundNumber = roundIndex + 1;
$: completedCount = game.rounds.filter((r) => r.guess || r.skipped).length;

function getMedal(score: number | null): { icon: string; label: string; color: string } | null {
	if (score === null) return null;
	if (score >= 4500) return { icon: "emoji_events", label: "Excellent!", color: "#f4c430" };
	if (score >= 3000) return { icon: "target", label: "Great!", color: "#2e933c" };
	if (score >= 1500) return { icon: "thumb_up", label: "Good", color: "#18181b" };
	return { icon: "location_on", label: "Keep trying", color: "#18181b" };
}

function formatDistance(meters: number | null): string {
	if (meters === null) return "—";
	if (meters < 1000) return `${Math.round(meters)}m`;
	return `${(meters / 1000).toFixed(1)}km`;
}

function computeAccuracy(score: number | null): string {
	if (score === null) return "—";
	return `${Math.round((score / 5000) * 100)}%`;
}

function computeTimeTaken(r: Round): string {
	if (!r.startedAt) return "—";
	const start = new Date(r.startedAt).getTime();
	const end = r.guess ? new Date(game.lastActivityAt).getTime() : start;
	const diffMs = Math.max(0, end - start);
	const totalSec = Math.floor(diffMs / 1000);
	const mins = String(Math.floor(totalSec / 60)).padStart(2, "0");
	const secs = String(totalSec % 60).padStart(2, "0");
	return `${mins}:${secs}`;
}

$: medal = getMedal(round.score);
$: timeTaken = computeTimeTaken(round);
</script>

<div class="results-root">
	{#if round.guess && round.actual}
		<ResultsMap
			guess={round.guess}
			actual={round.actual}
			distanceMeters={round.distanceMeters ?? 0}
			locationName={round.location_name}
		/>
	{/if}

	<div class="hud-bar">
		<HudPill
			round={roundNumber}
			totalRounds={game.rounds.length}
			score={game.totalScore}
			timer={timeTaken}
			showCheck
		/>
	</div>

	<div class="bottom-sheet">
		<ProgressDots
			total={game.rounds.length}
			completed={completedCount}
			current={roundIndex + 1}
		/>

		<div class="score-section">
			<div class="score-left">
				<p class="score-label">Round Score</p>
				<div class="score-display">
					<span class="score-value font-heading">
						{(round.score ?? 0).toLocaleString()}
					</span>
					<span class="score-unit font-mono">pts</span>
				</div>
			</div>

			{#if medal}
				<div class="medal-badge">
					<div class="medal-circle" style="background: {medal.color}20">
						<span
							class="material-symbols-outlined medal-icon"
							style="color: {medal.color}; font-variation-settings: 'FILL' 1;"
						>{medal.icon}</span>
					</div>
					<span class="medal-label" style="color: {medal.color}">{medal.label}</span>
				</div>
			{/if}
		</div>

		{#if round.location_name}
			<div class="location-card">
				<div class="stat-card-label">Location</div>
				<div class="location-value">{round.location_name}</div>
			</div>
		{/if}

		<div class="stats-row">
			<div class="stat-card">
				<div class="stat-card-label">Distance</div>
				<div class="stat-card-value font-mono">{formatDistance(round.distanceMeters)}</div>
			</div>
			<div class="stat-card">
				<div class="stat-card-label">Time</div>
				<div class="stat-card-value font-mono">{timeTaken}</div>
			</div>
			<div class="stat-card">
				<div class="stat-card-label">Accuracy</div>
				<div class="stat-card-value font-mono accuracy">{computeAccuracy(round.score)}</div>
			</div>
		</div>

		{#if isLastRound}
			<button class="btn-3d next-btn" on:click={onFinish}>
				<span>See Results</span>
				<span class="material-symbols-outlined btn-icon">arrow_forward</span>
			</button>
		{:else}
			<button class="btn-3d next-btn" on:click={onNextRound} disabled={isTransitioning}>
				<span>{isTransitioning ? "Starting..." : "Next Round"}</span>
				<span class="material-symbols-outlined btn-icon">arrow_forward</span>
			</button>
		{/if}
	</div>
</div>

<style>
	.results-root {
		position: fixed;
		inset: 0;
		background: #f5f2e9;
		overflow: hidden;
	}

	.hud-bar {
		position: absolute;
		top: 20px;
		left: 50%;
		transform: translateX(-50%);
		z-index: 30;
	}

	.bottom-sheet {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		z-index: 50;
		background: white;
		border-top-left-radius: 24px;
		border-top-right-radius: 24px;
		box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.08);
		padding: 20px 24px 28px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 16px;
		animation: slideUp 0.4s ease-out;
	}

	@keyframes slideUp {
		from {
			transform: translateY(100%);
		}
		to {
			transform: translateY(0);
		}
	}

	.score-section {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		max-width: 320px;
	}

	.score-left {
		flex: 1;
	}

	.score-label {
		font-size: 11px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: rgba(24, 24, 27, 0.4);
		margin-bottom: 4px;
	}

	.score-display {
		display: flex;
		align-items: baseline;
		gap: 8px;
	}

	.score-value {
		font-size: 2.5rem;
		font-weight: 700;
		color: #2e933c;
		animation: scorePop 0.5s ease-out;
	}

	@keyframes scorePop {
		0% {
			transform: scale(0.5);
			opacity: 0;
		}
		70% {
			transform: scale(1.1);
		}
		100% {
			transform: scale(1);
			opacity: 1;
		}
	}

	.score-unit {
		font-size: 1rem;
		font-weight: 500;
		color: rgba(24, 24, 27, 0.3);
	}

	.medal-badge {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
	}

	.medal-circle {
		width: 56px;
		height: 56px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.medal-icon {
		font-size: 32px;
	}

	.medal-label {
		font-size: 11px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.location-card {
		width: 100%;
		max-width: 320px;
		padding: 12px;
		background: rgba(245, 242, 233, 0.6);
		border-radius: 12px;
		text-align: center;
	}

	.location-value {
		font-size: 16px;
		font-weight: 700;
		color: #18181b;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.stats-row {
		display: flex;
		gap: 12px;
		width: 100%;
		max-width: 320px;
	}

	.stat-card {
		flex: 1;
		padding: 12px;
		background: rgba(245, 242, 233, 0.6);
		border-radius: 12px;
		text-align: center;
	}

	.stat-card-label {
		font-size: 10px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: rgba(24, 24, 27, 0.4);
		margin-bottom: 4px;
	}

	.stat-card-value {
		font-size: 18px;
		font-weight: 700;
		color: #18181b;
	}

	.stat-card-value.accuracy {
		color: #2e933c;
	}

	.next-btn {
		width: 100%;
		max-width: 320px;
		padding: 16px;
		font-size: 16px;
		font-weight: 700;
		letter-spacing: 0.02em;
		background: #2e933c;
		color: white;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		box-shadow: 0 6px 0 #236e2d;
		transition: transform 0.1s, box-shadow 0.1s;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
	}

	.next-btn:active {
		transform: translateY(6px);
		box-shadow: 0 0 0 #236e2d;
	}

	.next-btn:disabled {
		cursor: not-allowed;
		opacity: 0.8;
	}

	.next-btn:disabled:active {
		transform: none;
		box-shadow: 0 6px 0 #236e2d;
	}

	.btn-icon {
		font-size: 20px;
	}

	@media (max-width: 640px) {
		.hud-bar {
			top: 12px;
		}

		.bottom-sheet {
			padding: 14px 16px 24px;
		}

		.score-value {
			font-size: 2rem;
		}

		.score-section,
		.location-card,
		.stats-row,
		.next-btn {
			max-width: 100%;
		}
	}
</style>
