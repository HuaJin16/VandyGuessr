<script lang="ts">
import { createEventDispatcher } from "svelte";
import logo from "../../../../assets/logo.webp";
import type { GameOverRound, RoundPlayerResult, Standing } from "../types";

export let standings: Standing[];
export let rounds: GameOverRound[] = [];
export let winnerId: string;
export let currentUserId: string;
export let gameId: string;

const dispatch = createEventDispatcher<{ home: undefined }>();

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
	for (const s of standings) {
		if (s.userId === currentUserId) continue;
		if (s.userId === userId) return playerColors[1 + opponentIdx];
		opponentIdx++;
	}
	return playerColors[index % playerColors.length];
}

function getPlayerColorById(userId: string): string {
	if (userId === currentUserId) return playerColors[0];
	let opponentIdx = 0;
	for (const s of standings) {
		if (s.userId === currentUserId) continue;
		if (s.userId === userId) return playerColors[1 + opponentIdx];
		opponentIdx++;
	}
	return "var(--muted)";
}

function getInitials(name: string): string {
	return name
		.split(" ")
		.map((w) => w[0])
		.join("")
		.toUpperCase()
		.slice(0, 2);
}

$: roundBreakdown = rounds.map((round) => {
	const myResult = round.results.find((r: RoundPlayerResult) => r.userId === currentUserId);
	const myScore = myResult?.score ?? 0;
	const bestResult = round.results.reduce(
		(best: RoundPlayerResult, r: RoundPlayerResult) => (r.score > best.score ? r : best),
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
</script>

<div class="min-h-screen bg-canvas">
	<header class="sticky top-0 z-50 border-b border-line bg-surface">
		<div class="mx-auto flex min-h-[48px] items-center justify-between gap-3 px-2 sm:min-h-[52px] sm:px-3" style="width: min(600px, calc(100% - 24px));">
			<div class="flex items-center gap-2.5">
				<img src={logo} alt="VandyGuessr" class="h-[34px] w-[34px] rounded-md" />
				<span class="text-lg font-extrabold text-ink">Game Over</span>
			</div>
			<div class="flex items-center gap-2">
				<a
					href="/"
					class="rounded-sm border border-line bg-surface px-2.5 py-[7px] text-[13px] font-semibold text-ink transition-all hover:border-brand hover:bg-brand-light hover:text-brand"
					style="transition-duration: var(--duration-fast); transition-timing-function: var(--ease);"
				>
					Home
				</a>
				<a
					href="/leaderboard"
					class="rounded-sm border border-line bg-surface px-2.5 py-[7px] text-[13px] font-semibold text-ink transition-all hover:border-brand hover:bg-brand-light hover:text-brand"
					style="transition-duration: var(--duration-fast); transition-timing-function: var(--ease);"
				>
					Leaderboard
				</a>
			</div>
		</div>
	</header>

	<main class="mx-auto my-4 grid gap-3.5 mb-6" style="width: min(700px, calc(100% - 32px));">
		<!-- Final Standings -->
		<section class="card">
			<p class="section-label">Final Standings</p>
			<div class="mt-2.5 grid gap-1">
				{#each standings as standing (standing.userId)}
					{@const isYou = standing.userId === currentUserId}
					{@const isWinner = standing.rank === 1}
					{@const color = getPlayerColor(standing.userId, standing.rank - 1)}
					<div
						class="standing-row"
						class:is-you={isYou}
						class:is-winner={isWinner}
					>
						<!-- Rank badge -->
						<div
							class="standing-rank-badge"
							class:rank-1={standing.rank === 1}
							class:rank-2={standing.rank === 2}
							class:rank-3={standing.rank === 3}
							class:rank-n={standing.rank > 3}
						>
							{#if standing.rank <= 3}
								<svg class="rank-trophy" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
									<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
									<path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
									<path d="M4 22h16" />
									<path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" />
									<path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" />
									<path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" />
								</svg>
							{:else}
								<span class="rank-num">{standing.rank}</span>
							{/if}
						</div>

						<!-- Avatar -->
						<div
							class="standing-av"
							style="background: {color};"
						>
							{getInitials(standing.name)}
						</div>

						<!-- Name -->
						<p class="standing-name">{standing.name}</p>

						<!-- You badge -->
						{#if isYou}
							<span class="you-badge">You</span>
						{/if}

						<!-- Score -->
						<span
							class="standing-pts"
							style={isYou ? "color: var(--brand);" : ""}
						>
							{standing.totalScore.toLocaleString()}{#if isWinner}<span class="standing-pts-unit">pts</span>{/if}
						</span>
					</div>
				{/each}
			</div>
		</section>

		<!-- Round Breakdown -->
		{#if roundBreakdown.length > 0}
			<section class="card">
				<p class="section-label">Round Breakdown</p>
				<div class="breakdown-list">
					{#each roundBreakdown as rb (rb.round)}
						{@const bestColor = getPlayerColorById(rb.bestUserId)}
						<div class="breakdown-row" class:you-won={rb.youWon}>
							<div class="breakdown-num">{rb.round}</div>
							<div class="breakdown-info">
								<span class="breakdown-your-score">{rb.myScore.toLocaleString()}</span>
								<div class="breakdown-bar-wrap">
									<div
										class="breakdown-bar"
										style="width:{rb.barPercent}%;background:{rb.youWon ? 'var(--brand)' : 'var(--line-strong)'};"
									/>
								</div>
							</div>
							<div class="breakdown-best">
								<span class="breakdown-best-score">{rb.bestScore.toLocaleString()}</span>
								<p class="breakdown-best-name" style="color:{bestColor};">{rb.youWon ? "You" : rb.bestName}</p>
							</div>
						</div>
					{/each}
				</div>
			</section>
		{/if}

		<!-- Actions -->
		<div class="grid gap-1.5">
			<a href="/multiplayer/{gameId}/lobby" class="btn-3d block w-full text-center text-[15px] no-underline">
				Rematch
			</a>
			<button
				class="w-full rounded-md border-2 border-line-strong bg-surface py-[11px] px-3.5 text-[15px] font-bold text-ink transition-all hover:border-muted hover:bg-canvas"
				style="transition-duration: var(--duration-fast); transition-timing-function: var(--ease);"
				on:click={() => dispatch("home")}
			>
				Home
			</button>
		</div>
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

	/* Standing rows */
	.standing-row {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 12px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
	}

	.standing-row.is-you {
		background: var(--brand-light);
		border-color: var(--brand);
	}

	.standing-row.is-winner {
		background: var(--gold-light);
		border-color: var(--gold);
		padding: 14px 14px;
		gap: 10px;
	}

	.standing-row.is-winner .standing-rank-badge {
		width: 32px;
		height: 32px;
		border-radius: var(--radius-sm);
	}

	.standing-row.is-winner .rank-trophy {
		width: 17px;
		height: 17px;
	}

	.standing-row.is-winner .standing-av {
		width: 40px;
		height: 40px;
		font-size: 13px;
	}

	.standing-row.is-winner .standing-name {
		font-size: 17px;
		font-weight: 700;
	}

	.standing-row.is-winner .standing-pts {
		font-size: 20px;
		font-weight: 700;
	}

	.standing-pts-unit {
		font-family: "IBM Plex Mono", monospace;
		font-size: 12px;
		font-weight: 600;
		color: var(--muted);
		margin-left: 2px;
	}

	.standing-rank-badge {
		width: 26px;
		height: 26px;
		border-radius: var(--radius-sm);
		display: grid;
		place-items: center;
		flex-shrink: 0;
	}

	.rank-1 { background: var(--gold); }
	.rank-2 { background: #9ca3af; }
	.rank-3 { background: #b8804a; }
	.rank-n { background: rgba(0, 0, 0, 0.05); }

	.rank-trophy {
		width: 14px;
		height: 14px;
	}

	.rank-num {
		font-size: 12px;
		font-weight: 800;
		color: var(--muted);
	}

	.standing-av {
		width: 32px;
		height: 32px;
		border-radius: 50%;
		color: #fff;
		font-size: 11px;
		font-weight: 700;
		display: grid;
		place-items: center;
		flex-shrink: 0;
	}

	.standing-name {
		margin: 0;
		font-size: 14px;
		font-weight: 600;
		flex: 1;
		min-width: 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.you-badge {
		font-size: 9px;
		font-weight: 700;
		padding: 2px 6px;
		border-radius: var(--radius-pill);
		text-transform: uppercase;
		background: var(--brand-light);
		color: var(--brand-dark);
		flex-shrink: 0;
	}

	.standing-pts {
		font-family: "IBM Plex Mono", monospace;
		font-size: 15px;
		font-weight: 600;
		flex-shrink: 0;
	}

	@media (max-width: 500px) {
		.standing-row.is-winner { padding: 10px 10px; }
		.standing-row.is-winner .standing-av { width: 34px; height: 34px; font-size: 11px; }
		.standing-row.is-winner .standing-name { font-size: 15px; }
		.standing-row.is-winner .standing-pts { font-size: 17px; }
		.standing-row { padding: 8px 8px; gap: 6px; }
		.standing-av { width: 28px; height: 28px; font-size: 10px; }
		.standing-pts { font-size: 13px; }
	}

	/* Round Breakdown */
	.breakdown-list {
		display: grid;
		gap: 0;
		margin-top: 10px;
	}

	.breakdown-row {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 10px 4px;
		border-bottom: 1px solid var(--line);
	}

	.breakdown-row:last-child { border-bottom: none; }

	.breakdown-row.you-won { background: rgba(46, 147, 60, 0.03); }

	.breakdown-num {
		width: 26px;
		height: 26px;
		border-radius: var(--radius-sm);
		display: grid;
		place-items: center;
		font-family: "IBM Plex Mono", monospace;
		font-size: 12px;
		font-weight: 600;
		flex-shrink: 0;
		background: #f0ede6;
		color: var(--muted);
	}

	.breakdown-row.you-won .breakdown-num {
		background: var(--brand-light);
		color: var(--brand);
	}

	.breakdown-info {
		flex: 1;
		min-width: 0;
	}

	.breakdown-your-score {
		font-family: "IBM Plex Mono", monospace;
		font-size: 14px;
		font-weight: 600;
	}

	.breakdown-row.you-won .breakdown-your-score {
		color: var(--brand);
	}

	.breakdown-bar-wrap {
		height: 5px;
		background: var(--line);
		border-radius: 3px;
		margin-top: 4px;
		overflow: hidden;
	}

	.breakdown-bar {
		height: 100%;
		border-radius: 3px;
		transition: width 0.6s ease-out;
	}

	.breakdown-best {
		text-align: right;
		flex-shrink: 0;
		width: 90px;
	}

	.breakdown-best-score {
		font-family: "IBM Plex Mono", monospace;
		font-size: 12px;
		font-weight: 600;
		color: var(--muted);
	}

	.breakdown-best-name {
		margin: 0;
		font-size: 11px;
		font-weight: 600;
	}

	@media (max-width: 500px) {
		.breakdown-best { width: 70px; }
		.breakdown-best-score { font-size: 11px; }
		.breakdown-best-name { font-size: 10px; }
		.breakdown-row { gap: 8px; padding: 8px 2px; }
		.breakdown-your-score { font-size: 13px; }
	}
</style>
