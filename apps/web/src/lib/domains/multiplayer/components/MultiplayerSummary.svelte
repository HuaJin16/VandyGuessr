<script lang="ts">
import Button from "$lib/shared/ui/Button.svelte";
import Card from "$lib/shared/ui/Card.svelte";
import { createEventDispatcher } from "svelte";
import type { GameOverRound, RoundPlayerResult, Standing } from "../types";

export let standings: Standing[];
export let rounds: GameOverRound[] = [];
export let currentUserId: string;
export let hostId: string;

const dispatch = createEventDispatcher<{ home: undefined; rematch: undefined }>();

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
	for (const standing of standings) {
		if (standing.userId === currentUserId) continue;
		if (standing.userId === userId) return playerColors[1 + opponentIdx];
		opponentIdx += 1;
	}
	return playerColors[index % playerColors.length];
}

function getPlayerColorById(userId: string): string {
	if (userId === currentUserId) return playerColors[0];
	let opponentIdx = 0;
	for (const standing of standings) {
		if (standing.userId === currentUserId) continue;
		if (standing.userId === userId) return playerColors[1 + opponentIdx];
		opponentIdx += 1;
	}
	return "var(--muted)";
}

function getInitials(name: string): string {
	return name
		.split(" ")
		.map((word) => word[0])
		.join("")
		.toUpperCase()
		.slice(0, 2);
}

$: roundBreakdown = rounds.map((round) => {
	const myResult = round.results.find(
		(result: RoundPlayerResult) => result.userId === currentUserId,
	);
	const myScore = myResult?.score ?? 0;
	const bestResult = round.results.reduce(
		(best: RoundPlayerResult, result: RoundPlayerResult) =>
			result.score > best.score ? result : best,
		round.results[0],
	);
	const youWon = bestResult?.userId === currentUserId;
	const barPercent = bestResult?.score ? Math.round((myScore / 5000) * 100) : 0;
	return {
		round: round.round,
		myScore,
		bestScore: bestResult?.score ?? 0,
		bestName: bestResult?.name ?? "",
		bestUserId: bestResult?.userId ?? "",
		youWon,
		barPercent,
	};
});

$: isHost = hostId === currentUserId;
$: winner = standings[0];
</script>

<div class="summary-page">
	<main class="summary-shell">
		<Card class="summary-hero">
			<p class="section-label">Match complete</p>
			<h1>{winner ? `${winner.name} wins` : "Final standings"}</h1>
			<p class="summary-copy">Celebrate the standings, review the flow of the match, and launch a rematch if the lobby wants another run.</p>
		</Card>

		<section class="summary-grid">
			<Card class="summary-card">
				<p class="section-label">Final standings</p>
				<div class="standings-list">
					{#each standings as standing, index (standing.userId)}
						{@const isYou = standing.userId === currentUserId}
						<div class={`standing-row ${isYou ? "standing-row--you" : ""} ${standing.rank === 1 ? "standing-row--winner" : ""}`}>
							<span class="standing-rank">#{standing.rank}</span>
							<div class="standing-avatar" style="background: {getPlayerColor(standing.userId, index)};">{getInitials(standing.name)}</div>
							<div class="standing-main">
								<p class="standing-name">{standing.name}</p>
								<p class="standing-meta">{isYou ? "You" : standing.rank === 1 ? "Winner" : "Finished match"}</p>
							</div>
							<span class="standing-score">{standing.totalScore.toLocaleString()}</span>
						</div>
					{/each}
				</div>
			</Card>

			<Card class="summary-card">
				<p class="section-label">Match story</p>
				<div class="story-list">
					{#each roundBreakdown as round}
						{@const bestColor = getPlayerColorById(round.bestUserId)}
						<div class="story-row">
							<div class="story-row__round">R{round.round}</div>
							<div class="story-row__bar-wrap">
								<div class="story-row__bar" style="width: {round.barPercent}%; background: {round.youWon ? 'var(--brand)' : 'var(--line-strong)'};"></div>
							</div>
							<div class="story-row__scores">
								<p>{round.myScore.toLocaleString()}</p>
								<span style="color: {bestColor};">{round.youWon ? "You" : round.bestName}</span>
							</div>
						</div>
					{/each}
				</div>
			</Card>
		</section>

		<div class="summary-actions">
			{#if isHost}
				<Button size="lg" on:click={() => dispatch("rematch")}>Rematch</Button>
			{/if}
			<Button variant="secondary" size="lg" on:click={() => dispatch("home")}>Home</Button>
			<Button variant="outline" size="lg" on:click={() => dispatch("home")}>Leaderboard later</Button>
		</div>
	</main>
</div>

<style>
	.summary-page {
		min-height: 100vh;
		background: var(--canvas);
	}

	.summary-shell {
		width: min(980px, calc(100% - 32px));
		margin: 24px auto;
		display: grid;
		gap: 18px;
	}

	.section-label,
	h1,
	.summary-copy {
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
		font-size: clamp(32px, 5vw, 48px);
		font-weight: 800;
		line-height: 1;
		letter-spacing: -0.05em;
	}

	.summary-copy {
		margin-top: 12px;
		max-width: 60ch;
		font-size: 15px;
		line-height: 1.6;
		color: var(--muted);
	}

	.summary-grid {
		display: grid;
		gap: 18px;
	}

	.summary-card {
		display: grid;
		gap: 16px;
	}

	.standings-list,
	.story-list {
		display: grid;
		gap: 10px;
	}

	.standing-row {
		display: grid;
		grid-template-columns: auto auto minmax(0, 1fr) auto;
		gap: 12px;
		align-items: center;
		padding: 12px 14px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
	}

	.standing-row--you {
		background: color-mix(in srgb, var(--brand-quiet) 85%, var(--surface));
		border-color: color-mix(in srgb, var(--brand) 25%, var(--line));
	}

	.standing-row--winner {
		background: color-mix(in srgb, var(--gold-light) 70%, var(--surface));
		border-color: color-mix(in srgb, var(--gold) 22%, var(--line));
	}

	.standing-rank,
	.standing-name,
	.standing-meta,
	.standing-score,
	.story-row__scores p,
	.story-row__scores span {
		margin: 0;
	}

	.standing-rank {
		font-size: 12px;
		font-weight: 700;
		color: var(--muted);
	}

	.standing-avatar {
		width: 34px;
		height: 34px;
		border-radius: 50%;
		color: #fff;
		font-size: 11px;
		font-weight: 700;
		display: grid;
		place-items: center;
	}

	.standing-main {
		min-width: 0;
	}

	.standing-name {
		font-size: 15px;
		font-weight: 700;
	}

	.standing-meta {
		margin-top: 4px;
		font-size: 12px;
		color: var(--muted);
	}

	.standing-score {
		font-family: "IBM Plex Mono", monospace;
		font-size: 16px;
		font-weight: 700;
	}

	.story-row {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) auto;
		gap: 12px;
		align-items: center;
		padding: 12px 14px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
	}

	.story-row__round {
		font-size: 12px;
		font-weight: 700;
		color: var(--muted);
	}

	.story-row__bar-wrap {
		height: 10px;
		border-radius: 999px;
		background: var(--surface-strong);
		overflow: hidden;
	}

	.story-row__bar {
		height: 100%;
		border-radius: 999px;
	}

	.story-row__scores {
		display: grid;
		justify-items: end;
		gap: 2px;
	}

	.story-row__scores p {
		font-family: "IBM Plex Mono", monospace;
		font-size: 13px;
		font-weight: 700;
	}

	.story-row__scores span {
		font-size: 12px;
		font-weight: 700;
	}

	.summary-actions {
		display: grid;
		gap: 10px;
	}

	@media (min-width: 900px) {
		.summary-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.summary-actions {
			grid-template-columns: repeat(3, minmax(0, 1fr));
		}
	}
</style>
