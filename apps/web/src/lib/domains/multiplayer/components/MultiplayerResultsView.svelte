<script lang="ts">
import { createEventDispatcher } from "svelte";
import type { RoundResult } from "../types";

export let result: RoundResult;
export let totalRounds: number;
export let isLastRound: boolean;

const dispatch = createEventDispatcher<{ nextRound: undefined }>();

const playerColors = ["#2e933c", "#3b82f6", "#f4c430", "#d95d39", "#8b5cf6"];
</script>

<div class="results-container glass-card">
	<h2 class="round-heading">Round {result.round} Results</h2>
	<p class="location-name">{result.locationName ?? "Unknown Location"}</p>

	<div class="results-list">
		{#each result.results as entry, i (entry.userId)}
			<div class="result-row">
				<div class="color-dot" style="background: {playerColors[i % playerColors.length]}" />
				<span class="player-name">{entry.name}</span>
				<span class="distance">
					{entry.guess
						? `${Math.round(entry.distanceMeters)}m`
						: "No guess"}
				</span>
				<span class="score">{entry.score.toLocaleString()}</span>
			</div>
		{/each}
	</div>

	<div class="standings-section">
		<h3 class="standings-heading">Standings</h3>
		{#each result.standings as standing (standing.userId)}
			<div class="standing-row">
				<span class="standing-rank">#{standing.rank}</span>
				<span class="standing-name">{standing.name}</span>
				<span class="standing-total">{standing.totalScore.toLocaleString()}</span>
			</div>
		{/each}
	</div>

	{#if !isLastRound}
		<button class="btn-3d next-btn" on:click={() => dispatch("nextRound")}>
			Next Round ({result.round}/{totalRounds})
		</button>
	{/if}
</div>

<style>
	.results-container {
		padding: 24px;
		max-width: 480px;
		margin: 0 auto;
	}
	.round-heading {
		font-family: "Rubik", sans-serif;
		font-weight: 700;
		font-size: 1.25rem;
		color: #18181b;
		text-align: center;
		margin-bottom: 4px;
	}
	.location-name {
		text-align: center;
		font-size: 0.875rem;
		color: #636363;
		margin-bottom: 20px;
	}
	.results-list {
		display: flex;
		flex-direction: column;
		gap: 8px;
		margin-bottom: 20px;
	}
	.result-row {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 8px 12px;
		border-radius: 10px;
		background: rgba(0, 0, 0, 0.03);
	}
	.color-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.player-name {
		flex: 1;
		font-family: "Rubik", sans-serif;
		font-weight: 600;
		font-size: 0.9375rem;
		color: #18181b;
	}
	.distance {
		font-size: 0.8125rem;
		color: #636363;
		font-variant-numeric: tabular-nums;
	}
	.score {
		font-family: "Rubik", sans-serif;
		font-weight: 700;
		font-size: 0.9375rem;
		color: #2e933c;
		font-variant-numeric: tabular-nums;
		min-width: 48px;
		text-align: right;
	}
	.standings-section {
		border-top: 1px solid rgba(0, 0, 0, 0.08);
		padding-top: 16px;
		margin-bottom: 20px;
	}
	.standings-heading {
		font-family: "Rubik", sans-serif;
		font-weight: 600;
		font-size: 0.8125rem;
		color: #636363;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 8px;
	}
	.standing-row {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 4px 0;
	}
	.standing-rank {
		font-family: "Rubik", sans-serif;
		font-weight: 700;
		font-size: 0.875rem;
		color: #f4c430;
		min-width: 24px;
	}
	.standing-name {
		flex: 1;
		font-size: 0.875rem;
		color: #18181b;
	}
	.standing-total {
		font-family: "Rubik", sans-serif;
		font-weight: 700;
		font-size: 0.875rem;
		color: #18181b;
		font-variant-numeric: tabular-nums;
	}
	.next-btn {
		width: 100%;
		text-align: center;
	}
</style>
