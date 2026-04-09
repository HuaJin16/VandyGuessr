<script lang="ts">
import Navbar from "$lib/shared/components/Navbar.svelte";
import Button from "$lib/shared/ui/Button.svelte";
import { onMount } from "svelte";
import { gamesService } from "../api/games.service";
import { computeTimeTaken, formatDistance, getRoundQuality } from "../score-quality";
import type { Game, Round, ScoreDistribution } from "../types";
import ProgressDots from "./ProgressDots.svelte";
import ResultsMap from "./ResultsMap.svelte";

export let game: Game;
export let round: Round;
export let roundIndex: number;
export let onNextRound: () => void;
export let onFinish: () => void;

$: isLastRound = roundIndex >= game.rounds.length - 1;
$: roundNumber = roundIndex + 1;
$: quality = getRoundQuality(round.score);
$: timeTaken = computeTimeTaken(round);

let distribution: ScoreDistribution | null = null;
let showQuality = false;

onMount(async () => {
	requestAnimationFrame(() => {
		showQuality = true;
	});

	if (round.score !== null && round.imageId) {
		try {
			distribution = await gamesService.getScoreDistribution(round.imageId, round.score);
		} catch {
			// non-critical
		}
	}
});

$: histMax = distribution ? Math.max(...distribution.histogram, 1) : 1;
$: yourBucket = distribution
	? (() => {
			const count = distribution.histogram.length;
			if (round.score === null || count === 0) return -1;
			const size = 5000 / count;
			return Math.min(Math.floor(round.score / size), count - 1);
		})()
	: -1;
</script>

<div class="results-page">
	<Navbar />

	<main class="main">
		<div class="top-row">
			<span class="round-label">Round {roundNumber} of {game.rounds.length}</span>
			<ProgressDots total={game.rounds.length} completed={roundIndex} current={roundIndex} />
		</div>

		{#if round.guess && round.actual}
			<div class="map-hero">
				<ResultsMap
					guess={round.guess}
					actual={round.actual}
					distanceMeters={round.distanceMeters ?? 0}
					locationName={round.location_name}
				/>
				<div class="map-legend">
					<span class="legend-item"><span class="dot dot-guess" />Your guess</span>
					<span class="legend-item"><span class="dot dot-actual" />Actual</span>
				</div>
			</div>
		{/if}

		<div class="verdict">
			<h1 class="location-name">{round.location_name ?? "Unknown location"}</h1>
			<div class="score-row">
				<span class="score-value" style="color: {quality.color}">
					{(round.score ?? 0).toLocaleString()}
				</span>
				<span class="score-max">/ 5,000</span>
				<span class="quality-word" class:visible={showQuality} style="color: {quality.color}">
					{quality.word}
				</span>
			</div>
		</div>

		<div class="metrics-strip">
			<div class="metric">
				<span class="metric-label">Distance</span>
				<span class="metric-value">{formatDistance(round.distanceMeters)}</span>
			</div>
			<span class="metric-sep" />
			<div class="metric">
				<span class="metric-label">Time</span>
				<span class="metric-value">{timeTaken}</span>
			</div>
			<span class="metric-sep" />
			<div class="metric">
				<span class="metric-label">Percentile</span>
				<span class="metric-value">{distribution ? `Top ${distribution.percentile}%` : "\u2014"}</span>
			</div>
		</div>

		{#if distribution && distribution.histogram.length > 0}
			<div class="histogram-section">
				<span class="histogram-label">Score distribution</span>
				<div class="histogram" aria-label="Score distribution histogram">
					{#each distribution.histogram as count, index}
						<div
							class="hbar"
							class:you={index === yourBucket}
							style="height: {Math.max(2, (count / histMax) * 100)}%"
						/>
					{/each}
				</div>
				<div class="histogram-range">
					<span>0</span>
					<span>5,000</span>
				</div>
			</div>
		{/if}

		<Button size="lg" on:click={isLastRound ? onFinish : onNextRound}>
			{isLastRound ? "See Results" : "Next Round"}
		</Button>
	</main>
</div>

<style>
	.results-page {
		min-height: 100vh;
		background: var(--canvas);
	}

	.main {
		width: min(920px, calc(100% - 32px));
		margin: 16px auto 32px;
		display: grid;
		gap: 16px;
	}

	.top-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.round-label {
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.map-hero {
		position: relative;
		height: 420px;
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		overflow: hidden;
		isolation: isolate;
	}

	.map-legend {
		position: absolute;
		bottom: 10px;
		left: 10px;
		display: flex;
		gap: 12px;
		padding: 6px 12px;
		border-radius: var(--radius-pill);
		background: rgba(255, 255, 255, 0.92);
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
		border: 1px solid rgba(255, 255, 255, 0.5);
		font-size: 12px;
		font-weight: 600;
		color: var(--ink);
		z-index: 600;
		box-shadow: var(--shadow-sm);
	}

	.legend-item {
		display: inline-flex;
		align-items: center;
		gap: 6px;
	}

	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.dot-guess {
		background: var(--brand);
	}

	.dot-actual {
		background: var(--gold);
	}

	.verdict {
		display: grid;
		gap: 6px;
		padding-top: 4px;
	}

	.location-name {
		margin: 0;
		font-size: clamp(22px, 3.5vw, 30px);
		font-weight: 800;
		line-height: 1.1;
		letter-spacing: -0.03em;
	}

	.score-row {
		display: flex;
		align-items: baseline;
		gap: 6px;
		flex-wrap: wrap;
	}

	.score-value {
		font-family: "IBM Plex Mono", monospace;
		font-size: clamp(36px, 6vw, 48px);
		font-weight: 700;
		line-height: 1;
	}

	.score-max {
		font-family: "IBM Plex Mono", monospace;
		font-size: 16px;
		font-weight: 600;
		color: var(--muted);
	}

	.quality-word {
		font-size: clamp(18px, 3vw, 24px);
		font-weight: 800;
		letter-spacing: -0.02em;
		margin-left: 6px;
		opacity: 0;
		transform: scale(0.7);
		transition: opacity 350ms var(--ease), transform 350ms var(--ease);
	}

	.quality-word.visible {
		opacity: 1;
		transform: scale(1);
	}

	.metrics-strip {
		display: flex;
		align-items: center;
		gap: 16px;
		padding: 14px 0;
		border-top: 1px solid var(--line);
		border-bottom: 1px solid var(--line);
	}

	.metric {
		display: grid;
		gap: 2px;
	}

	.metric-label {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.metric-value {
		font-family: "IBM Plex Mono", monospace;
		font-size: 16px;
		font-weight: 600;
		color: var(--ink);
	}

	.metric-sep {
		width: 1px;
		height: 28px;
		background: var(--line);
		flex-shrink: 0;
	}

	.histogram-section {
		display: grid;
		gap: 6px;
	}

	.histogram-label {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.histogram {
		display: flex;
		align-items: end;
		gap: 3px;
		height: 40px;
	}

	.hbar {
		flex: 1;
		border-radius: 2px 2px 0 0;
		background: var(--line);
	}

	.hbar.you {
		background: var(--brand);
	}

	.histogram-range {
		display: flex;
		justify-content: space-between;
		font-size: 10px;
		font-family: "IBM Plex Mono", monospace;
		font-weight: 600;
		color: var(--muted);
	}

	@media (max-width: 640px) {
		.map-hero {
			height: 300px;
		}

		.metrics-strip {
			gap: 12px;
		}
	}
</style>
