<script lang="ts">
import Navbar from "$lib/shared/components/Navbar.svelte";
import Button from "$lib/shared/ui/Button.svelte";
import Card from "$lib/shared/ui/Card.svelte";
import { createEventDispatcher } from "svelte";
import type { RoundResult } from "../types";
import MultiplayerResultsMap from "./MultiplayerResultsMap.svelte";

export let result: RoundResult;
export let currentUserId: string;
export let readySent = false;

const dispatch = createEventDispatcher<{ readyNext: undefined }>();

const playerColors = [
	"var(--p-you)",
	"var(--p-blue)",
	"var(--p-purple)",
	"var(--p-orange)",
	"var(--p-cyan)",
	"var(--p-pink)",
];

function getPlayerColor(userId: string, index: number): string {
	if (userId === currentUserId) return playerColors[0];
	let opponentIdx = 0;
	for (let i = 0; i < result.results.length; i += 1) {
		if (result.results[i].userId === currentUserId) continue;
		if (result.results[i].userId === userId) return playerColors[1 + opponentIdx];
		opponentIdx += 1;
	}
	return playerColors[index % playerColors.length];
}

function getInitials(name: string): string {
	return name
		.split(" ")
		.map((word) => word[0])
		.join("")
		.toUpperCase()
		.slice(0, 2);
}

function formatDistance(meters: number | null): string {
	if (meters === null) return "—";
	return `${Math.round(meters)}m`;
}

$: sortedResults = [...result.results].sort((a, b) => b.score - a.score);
$: roundDots = Array.from({ length: 5 }, (_, index) => {
	if (index + 1 < result.round) return "done" as const;
	if (index + 1 === result.round) return "current" as const;
	return "pending" as const;
});
</script>

<div class="min-h-screen bg-canvas">
	<Navbar />

	<main class="results-shell">
		<Card class="results-header-card">
			<div class="results-header-card__top">
				<div>
					<p class="section-label">Round {result.round} of 5</p>
					<h1>{result.locationName ?? "Unknown location"}</h1>
					<p class="results-copy">Standings first, map proof underneath. Keep the pace moving toward the next round.</p>
				</div>
				<div class="round-progress">
					{#each roundDots as dot}
						<div class={`round-progress__dot ${dot === "done" || dot === "current" ? "round-progress__dot--active" : ""} ${dot === "current" ? "round-progress__dot--current" : ""}`}></div>
					{/each}
				</div>
			</div>

			<div class="score-columns">
				<Card tone="subtle" class="score-column">
					<p class="section-label">Round standings</p>
					<div class="score-list">
						{#each sortedResults as entry, index (entry.userId)}
							{@const isYou = entry.userId === currentUserId}
							<div class={`score-row ${isYou ? "score-row--you" : ""}`}>
								<span class="score-row__rank">#{index + 1}</span>
								<div class="score-row__avatar" style="background: {getPlayerColor(entry.userId, index)};">{getInitials(entry.name)}</div>
								<div class="score-row__main">
									<p class="score-row__name">{entry.name}</p>
									<p class="score-row__meta">{entry.guess ? formatDistance(entry.distanceMeters) : "No guess"}</p>
								</div>
								<span class="score-row__score">{entry.score.toLocaleString()}</span>
							</div>
						{/each}
					</div>
				</Card>

				<Card tone="subtle" class="score-column">
					<p class="section-label">Total standings</p>
					<div class="score-list">
						{#each result.standings as standing, index (standing.userId)}
							{@const isYou = standing.userId === currentUserId}
							<div class={`score-row ${isYou ? "score-row--you" : ""}`}>
								<span class="score-row__rank">#{standing.rank}</span>
								<div class="score-row__avatar" style="background: {getPlayerColor(standing.userId, index)};">{getInitials(standing.name)}</div>
								<div class="score-row__main">
									<p class="score-row__name">{standing.name}</p>
									<p class="score-row__meta">Overall score</p>
								</div>
								<span class="score-row__score">{standing.totalScore.toLocaleString()}</span>
							</div>
						{/each}
					</div>
				</Card>
			</div>
		</Card>

		<Card class="map-card">
			<p class="section-label">Map debrief</p>
			<MultiplayerResultsMap {result} {currentUserId} />
			<div class="legend">
				{#each sortedResults as entry, index (entry.userId)}
					<span class="legend-item">
						<span class="legend-dot" style="background: {getPlayerColor(entry.userId, index)};"></span>
						{entry.userId === currentUserId ? "You" : entry.name.split(" ")[0]}
					</span>
				{/each}
				<span class="legend-item">
					<span class="legend-dot legend-dot--actual"></span>
					Actual
				</span>
			</div>
		</Card>

		<div class="results-actions">
			<p class="results-actions__copy">{readySent ? "Waiting for other players to ready up..." : "Ready when you are."}</p>
			<Button size="lg" disabled={readySent} on:click={() => dispatch("readyNext")}>
				{readySent ? "Waiting for others..." : "Ready for Next Round"}
			</Button>
		</div>
	</main>
</div>

<style>
	.results-shell {
		width: min(980px, calc(100% - 32px));
		margin: 16px auto 24px;
		display: grid;
		gap: 18px;
	}

	.section-label,
	h1,
	.results-copy,
	.results-actions__copy {
		margin: 0;
	}

	.section-label {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	h1 {
		margin-top: 8px;
		font-size: clamp(28px, 4vw, 38px);
		font-weight: 800;
		line-height: 1;
		letter-spacing: -0.04em;
	}

	.results-copy,
	.results-actions__copy {
		font-size: 14px;
		line-height: 1.55;
		color: var(--muted);
	}

	.results-header-card,
	.map-card {
		display: grid;
		gap: 18px;
	}

	.results-header-card__top {
		display: grid;
		gap: 16px;
	}

	.round-progress {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.round-progress__dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--line);
	}

	.round-progress__dot--active {
		background: var(--brand);
	}

	.round-progress__dot--current {
		box-shadow: 0 0 0 4px rgba(46, 147, 60, 0.16);
	}

	.score-columns {
		display: grid;
		gap: 14px;
	}

	.score-column {
		display: grid;
		gap: 14px;
	}

	.score-list {
		display: grid;
		gap: 10px;
	}

	.score-row {
		display: grid;
		grid-template-columns: auto auto minmax(0, 1fr) auto;
		gap: 12px;
		align-items: center;
		padding: 12px 14px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
	}

	.score-row--you {
		background: color-mix(in srgb, var(--brand-quiet) 85%, var(--surface));
		border-color: color-mix(in srgb, var(--brand) 25%, var(--line));
	}

	.score-row__rank,
	.score-row__name,
	.score-row__meta,
	.score-row__score {
		margin: 0;
	}

	.score-row__rank {
		font-size: 12px;
		font-weight: 700;
		color: var(--muted);
	}

	.score-row__avatar {
		width: 32px;
		height: 32px;
		border-radius: 50%;
		color: #fff;
		font-size: 11px;
		font-weight: 700;
		display: grid;
		place-items: center;
	}

	.score-row__main {
		min-width: 0;
	}

	.score-row__name {
		font-size: 14px;
		font-weight: 700;
	}

	.score-row__meta {
		margin-top: 4px;
		font-size: 12px;
		color: var(--muted);
	}

	.score-row__score {
		font-family: "IBM Plex Mono", monospace;
		font-size: 15px;
		font-weight: 700;
	}

	.legend {
		display: flex;
		flex-wrap: wrap;
		gap: 12px;
		font-size: 12px;
		font-weight: 600;
		color: var(--muted);
	}

	.legend-item {
		display: inline-flex;
		align-items: center;
		gap: 8px;
	}

	.legend-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		display: inline-block;
	}

	.legend-dot--actual {
		background: var(--gold);
	}

	.results-actions {
		display: grid;
		gap: 12px;
	}

	@media (min-width: 900px) {
		.results-header-card__top {
			grid-template-columns: minmax(0, 1fr) auto;
			align-items: end;
		}

		.score-columns {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.results-actions {
			grid-template-columns: minmax(0, 1fr) auto;
			align-items: center;
		}
	}
</style>
