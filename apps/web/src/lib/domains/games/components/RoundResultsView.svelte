<script lang="ts">
import Navbar from "$lib/shared/components/Navbar.svelte";
import { onMount } from "svelte";
import { gamesService } from "../api/games.service";
import type { Game, Round, ScoreDistribution } from "../types";
import ResultsMap from "./ResultsMap.svelte";

export let game: Game;
export let round: Round;
export let roundIndex: number;
export let onNextRound: () => void;
export let onFinish: () => void;

$: isLastRound = roundIndex >= game.rounds.length - 1;
$: roundNumber = roundIndex + 1;

let distribution: ScoreDistribution | null = null;

onMount(async () => {
	if (round.score !== null && round.imageId) {
		try {
			distribution = await gamesService.getScoreDistribution(round.imageId, round.score);
		} catch {
			// non-critical — histogram just won't render
		}
	}
});

function formatDistance(meters: number | null): string {
	if (meters === null) return "\u2014";
	if (meters < 1000) return `${Math.round(meters)}m`;
	return `${(meters / 1000).toFixed(1)}km`;
}

function computeTimeTaken(r: Round): string {
	if (!r.startedAt) return "\u2014";
	const start = new Date(r.startedAt).getTime();
	const end = r.guessedAt ? new Date(r.guessedAt).getTime() : Date.now();
	const diffMs = Math.max(0, end - start);
	const totalSec = Math.floor(diffMs / 1000);
	const mins = String(Math.floor(totalSec / 60)).padStart(2, "0");
	const secs = String(totalSec % 60).padStart(2, "0");
	return `${mins}:${secs}`;
}

function histogramMaxHeight(values: number[]): number {
	return Math.max(...values, 1);
}

function getYourBucket(score: number | null, bucketCount: number): number {
	if (score === null || bucketCount === 0) return -1;
	const bucketSize = 5000 / bucketCount;
	return Math.min(Math.floor(score / bucketSize), bucketCount - 1);
}

$: timeTaken = computeTimeTaken(round);
$: histMax = distribution ? histogramMaxHeight(distribution.histogram) : 1;
$: yourBucket = distribution ? getYourBucket(round.score, distribution.histogram.length) : -1;
</script>

<div class="results-page">
	<Navbar />

	<main class="main">
		<!-- Map Card -->
		{#if round.guess && round.actual}
			<section class="card map-card">
				<p class="section-label">Map Debrief</p>
				<div class="map-container">
					<ResultsMap
						guess={round.guess}
						actual={round.actual}
						distanceMeters={round.distanceMeters ?? 0}
						locationName={round.location_name}
					/>
				</div>
				<div class="legend">
					<span class="legend-item"><span class="dot dot-guess"></span>Your Guess</span>
					<span class="legend-item"><span class="dot dot-actual"></span>Actual Location</span>
				</div>
			</section>
		{/if}

		<!-- Summary Card -->
		<section class="card summary-card">
			<p class="section-label">Round {roundNumber} of {game.rounds.length}</p>
			{#if round.location_name}
				<h2 class="location">{round.location_name}</h2>
			{/if}

			<div class="score-area">
				<div class="score-left">
					<div class="score">
						<span class="score-value">{(round.score ?? 0).toLocaleString()}</span>
						<span class="score-unit">points</span>
					</div>
				</div>

				{#if distribution && distribution.histogram.length > 0}
					<div class="histogram-wrap">
						<p class="histogram-label">Score Distribution</p>
						<div class="histogram" aria-label="Score distribution histogram. Your score is in the top {distribution.percentile}%.">
							{#each distribution.histogram as count, i}
								<div
									class="hbar"
									class:you={i === yourBucket}
									style="height: {Math.max(2, (count / histMax) * 100)}%"
								></div>
							{/each}
						</div>
						<div class="histogram-range">
							<span>0</span>
							<span>5,000</span>
						</div>
					</div>
				{/if}
			</div>

			<div class="stats">
				<article class="stat">
					<p class="stat-label">Distance</p>
					<p class="stat-value">{formatDistance(round.distanceMeters)}</p>
				</article>
				<article class="stat">
					<p class="stat-label">Time</p>
					<p class="stat-value">{timeTaken}</p>
				</article>
				<article class="stat">
					<p class="stat-label">Percentile</p>
					<p class="stat-value">{distribution ? `Top ${distribution.percentile}%` : "\u2014"}</p>
				</article>
			</div>

			{#if isLastRound}
				<button class="action-btn" on:click={onFinish}>See Results</button>
			{:else}
				<button class="action-btn" on:click={onNextRound}>Next Round</button>
			{/if}
		</section>
	</main>
</div>

<style>
	.results-page {
		min-height: 100vh;
		background: var(--canvas);
	}

	.main {
		width: min(700px, calc(100% - 32px));
		margin: 16px auto 24px;
		display: grid;
		gap: 14px;
	}

	.card {
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		background: var(--surface);
		box-shadow: var(--shadow-sm);
		padding: 16px;
	}

	.section-label {
		margin: 0;
		color: var(--muted);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	/* Map Card */
	.map-card {
		overflow: hidden;
	}

	.map-container {
		margin-top: 8px;
		height: 300px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		overflow: hidden;
		position: relative;
		isolation: isolate;
	}

	.legend {
		margin-top: 10px;
		display: flex;
		gap: 14px;
		flex-wrap: wrap;
		font-size: 13px;
		color: var(--muted);
	}

	.legend-item {
		display: inline-flex;
		align-items: center;
	}

	.dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		display: inline-block;
		margin-right: 6px;
	}

	.dot-guess { background: var(--brand); }
	.dot-actual { background: var(--gold); }

	/* Summary Card */
	.location {
		margin: 6px 0 0;
		font-size: 24px;
		font-weight: 700;
		line-height: 1.15;
		color: var(--ink);
	}

	.score-area {
		display: flex;
		align-items: flex-end;
		gap: 20px;
		margin-top: 14px;
	}

	.score-left {
		flex-shrink: 0;
	}

	.score {
		display: flex;
		align-items: baseline;
		gap: 10px;
	}

	.score-value {
		font-family: "IBM Plex Mono", monospace;
		font-size: 42px;
		line-height: 1;
		font-weight: 700;
		color: var(--brand);
	}

	.score-unit {
		font-family: "IBM Plex Mono", monospace;
		font-size: 13px;
		font-weight: 600;
		color: var(--muted);
	}

	/* Histogram */
	.histogram-wrap {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
	}

	.histogram-label {
		margin: 0 0 6px;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.histogram {
		display: flex;
		align-items: flex-end;
		gap: 2px;
		height: 48px;
	}

	.hbar {
		flex: 1;
		border-radius: 2px 2px 0 0;
		background: var(--line);
		min-width: 0;
		transition: background 120ms var(--ease);
	}

	.hbar.you {
		background: var(--brand);
	}

	.histogram-range {
		display: flex;
		justify-content: space-between;
		margin-top: 3px;
		font-size: 10px;
		color: var(--muted);
		font-family: "IBM Plex Mono", monospace;
		font-weight: 500;
	}

	/* Stats grid */
	.stats {
		margin-top: 14px;
		display: grid;
		gap: 8px;
		grid-template-columns: repeat(3, minmax(0, 1fr));
	}

	/* Action button */
	.action-btn {
		width: 100%;
		margin-top: 14px;
		border: none;
		border-radius: var(--radius-md);
		background: var(--brand);
		color: #fff;
		font-family: Inter, sans-serif;
		font-size: 15px;
		font-weight: 700;
		padding: 12px 14px;
		box-shadow: 0 4px 0 var(--brand-dark);
		cursor: pointer;
		transition: all 120ms var(--ease);
	}

	.action-btn:hover { background: #278234; }
	.action-btn:active { transform: translateY(4px); box-shadow: 0 0 0 var(--brand-dark); }
	.action-btn:focus-visible { outline: none; box-shadow: 0 4px 0 var(--brand-dark), var(--ring); }

	@media (min-width: 700px) {
		.card { padding: 18px; }
		.map-container { height: 400px; }
	}

	@media (max-width: 500px) {
		.score-area {
			flex-direction: column;
			gap: 12px;
		}

		.score-value {
			font-size: 32px;
		}

		.location {
			font-size: 20px;
		}

		.stats {
			gap: 6px;
		}
	}
</style>
