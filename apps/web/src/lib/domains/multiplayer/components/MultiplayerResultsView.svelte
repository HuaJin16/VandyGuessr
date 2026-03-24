<script lang="ts">
import Navbar from "$lib/shared/components/Navbar.svelte";
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
	for (let i = 0; i < result.results.length; i++) {
		if (result.results[i].userId === currentUserId) continue;
		if (result.results[i].userId === userId) return playerColors[1 + opponentIdx];
		opponentIdx++;
	}
	return playerColors[index % playerColors.length];
}

function getInitials(name: string): string {
	return name
		.split(" ")
		.map((w) => w[0])
		.join("")
		.toUpperCase()
		.slice(0, 2);
}

function formatDistance(meters: number | null): string {
	if (meters === null) return "—";
	return `${Math.round(meters)}m`;
}

function ordinalRank(rank: number): string {
	const s = ["th", "st", "nd", "rd"];
	const v = rank % 100;
	return rank + (s[(v - 20) % 10] || s[v] || s[0]);
}

$: sortedResults = [...result.results].sort((a, b) => b.score - a.score);

$: roundDots = Array.from({ length: 5 }, (_, i) => {
	if (i + 1 < result.round) return "done" as const;
	if (i + 1 === result.round) return "current" as const;
	return "pending" as const;
});
</script>

<div class="min-h-screen bg-canvas">
	<Navbar />

	<main class="mx-auto my-4 grid gap-3.5 mb-6" style="width: min(700px, calc(100% - 32px));">
		<!-- Map card -->
		<section class="card">
			<p class="section-label">Map Debrief</p>

			<MultiplayerResultsMap {result} {currentUserId} />

			<div class="mt-2.5 flex flex-wrap items-center gap-3 text-xs text-muted">
				{#each sortedResults as entry, i (entry.userId)}
					<span class="flex items-center gap-1">
						<span
							class="inline-block h-2 w-2 rounded-full"
							style="background: {getPlayerColor(entry.userId, i)};"
						/>
						{entry.userId === currentUserId ? "You" : entry.name.split(" ")[0]}
					</span>
				{/each}
				<span class="flex items-center gap-1">
					<svg width="10" height="10" viewBox="0 0 24 24" fill="var(--gold)" stroke="var(--gold-ink)" stroke-width="2">
						<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
					</svg>
					Actual
				</span>
			</div>
		</section>

		<!-- Score table card -->
		<section class="card">
			<div class="flex justify-center gap-2 mb-3.5">
				{#each roundDots as dot}
					<div
						class="h-2.5 w-2.5 rounded-full"
						class:bg-brand={dot === "done" || dot === "current"}
						class:bg-line={dot === "pending"}
						style={dot === "current" ? "box-shadow: 0 0 0 3px rgba(46,147,60,0.25);" : ""}
					/>
				{/each}
			</div>

			<p class="section-label">Round {result.round} of 5</p>
			<h2 class="mt-1.5 mb-0 text-[22px] font-extrabold leading-tight text-ink">
				{result.locationName ?? "Unknown Location"}
			</h2>

			<div class="mt-3.5 grid gap-1">
				{#each sortedResults as entry, i (entry.userId)}
					{@const isYou = entry.userId === currentUserId}
					{@const color = getPlayerColor(entry.userId, i)}
					<div
						class="flex items-center gap-2 rounded-md border px-2.5 py-2"
						class:border-brand={isYou}
						class:bg-brand-light={isYou}
						class:border-line={!isYou}
						class:bg-surface={!isYou}
					>
						<span class="w-5 flex-shrink-0 text-center font-mono text-xs font-semibold text-muted">
							#{i + 1}
						</span>
						<div
							class="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
							style="background: {color};"
						>
							{getInitials(entry.name)}
						</div>
						<p class="m-0 flex-1 min-w-0 truncate text-[13px] font-semibold text-ink">
							{entry.name}
						</p>
						{#if isYou}
							<span class="flex-shrink-0 rounded-full bg-brand-light px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-brand-dark">
								You
							</span>
						{/if}
						<span
							class="flex-shrink-0 font-mono text-sm font-semibold"
							style={isYou ? "color: var(--brand);" : ""}
						>
							{entry.score.toLocaleString()}
						</span>
						<span class="score-dist">
							{entry.guess ? formatDistance(entry.distanceMeters) : "No guess"}
						</span>
					</div>
				{/each}
			</div>
		</section>

		<!-- Overall standings card -->
		<section class="card">
			<div class="mb-2 flex items-center gap-1.5">
				<svg class="h-4 w-4 text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M18 20V10" />
					<path d="M12 20V4" />
					<path d="M6 20v-6" />
				</svg>
				<p class="m-0 text-[11px] font-semibold uppercase tracking-widest text-muted">Overall Standings</p>
			</div>

			<div class="grid gap-1">
				{#each result.standings as standing (standing.userId)}
					{@const isYou = standing.userId === currentUserId}
					{@const color = getPlayerColor(standing.userId, standing.rank - 1)}
					<div
						class="flex items-center gap-2 rounded-md border px-2.5 py-2"
						class:border-brand={isYou}
						class:bg-brand-light={isYou}
						class:border-line={!isYou}
						class:bg-surface={!isYou}
					>
						<span class="w-6 flex-shrink-0 font-mono text-[11px] font-semibold text-muted">
							{ordinalRank(standing.rank)}
						</span>
						<div
							class="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-[9px] font-bold text-white"
							style="background: {color};"
						>
							{getInitials(standing.name)}
						</div>
						<p class="m-0 flex-1 min-w-0 truncate text-[13px] font-semibold text-ink">
							{standing.name}
						</p>
						<span
							class="flex-shrink-0 font-mono text-[13px] font-semibold"
							style={isYou ? "color: var(--brand);" : ""}
						>
							{standing.totalScore.toLocaleString()}
						</span>
					</div>
				{/each}
			</div>

		<button
			class="btn-3d mt-3.5 w-full text-[15px]"
			disabled={readySent}
			on:click={() => dispatch("readyNext")}
		>
			{readySent ? "Waiting for others…" : "Next Round"}
		</button>
		</section>
	</main>
</div>

<style>
	.section-label {
		margin: 0;
		color: var(--muted);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.score-dist {
		font-family: "IBM Plex Mono", monospace;
		font-size: 11px;
		font-weight: 500;
		color: var(--muted);
		background: rgba(0, 0, 0, 0.04);
		border-radius: var(--radius-pill);
		padding: 2px 8px;
		flex-shrink: 0;
	}

	@media (max-width: 500px) {
		.score-dist { display: none; }
	}
</style>
