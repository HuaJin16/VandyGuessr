<script lang="ts">
import { gameQueries } from "$lib/domains/games/queries/games.queries";
import type { GameMode } from "$lib/domains/games/types";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import { createQuery } from "@tanstack/svelte-query";
import { ChevronRight } from "lucide-svelte";
import { navigate } from "svelte-routing";

const listParams = { limit: 50 } as const;

$: historyQuery = createQuery({
	...gameQueries.list(listParams),
	enabled: $auth.isInitialized,
	staleTime: 0,
});

$: pastGames =
	$historyQuery.data
		?.filter((g) => g.status !== "active")
		.sort((a, b) => {
			const ta = new Date(a.createdAt).getTime();
			const tb = new Date(b.createdAt).getTime();
			return tb - ta;
		}) ?? [];

function getSoloModeLabel(mode: GameMode): string {
	if (mode.daily) return "Daily Challenge";
	return mode.timed ? "Timed Random Drop" : "Random Drop";
}

function getEnvironmentLabel(value: GameMode["environment"]): string {
	if (value === "indoor") return "Indoor";
	if (value === "outdoor") return "Outdoor";
	return "All campus";
}

function formatPlayedAt(iso: string): string {
	const d = new Date(iso);
	return d.toLocaleString(undefined, {
		month: "short",
		day: "numeric",
		year: "numeric",
		hour: "numeric",
		minute: "2-digit",
	});
}
</script>

<div class="min-h-screen bg-canvas font-sans text-ink">
	<Navbar activePage="history" />

	<main class="main">
		<section class="card">
			<p class="section-label">Solo</p>
			<h1>Game history</h1>
			<p class="desc">Completed and abandoned games. Open a row to see the full summary.</p>

			{#if $historyQuery.isLoading}
				<div class="state-wrap">
					<div class="loading-spinner" />
				</div>
			{:else if $historyQuery.isError}
				<div class="state-wrap state-error">
					<p class="state-title">Couldn't load history</p>
					<button class="btn-3d" type="button" on:click={() => $historyQuery.refetch()}>Try again</button>
				</div>
			{:else if pastGames.length === 0}
				<div class="empty">
					<p class="empty-title">No past games yet</p>
					<p class="empty-copy">Finish a solo round from home, then your scores show up here.</p>
					<button class="btn-3d" type="button" on:click={() => navigate("/")}>Back to home</button>
				</div>
			{:else}
				<ul class="history-list" aria-label="Past games">
					{#each pastGames as game (game.id)}
						<li>
							<button
								type="button"
								class="history-row"
								on:click={() => navigate(`/game/${game.id}/summary`)}
							>
								<div class="history-main">
									<div class="history-top">
										<span class="history-date">{formatPlayedAt(game.createdAt)}</span>
										<span
											class="status-pill"
											class:status-pill--done={game.status === "completed"}
											class:status-pill--abandoned={game.status === "abandoned"}
										>
											{game.status === "completed" ? "Completed" : "Abandoned"}
										</span>
									</div>
									<p class="history-mode">{getSoloModeLabel(game.mode)}</p>
									<p class="history-meta">
										{getEnvironmentLabel(game.mode.environment)}
										{#if !game.mode.daily}
											<span class="dot">·</span>
											{game.mode.timed ? "Timer on" : "No timer"}
										{/if}
									</p>
								</div>
								<div class="history-score">
									<span class="score-val">{game.totalScore.toLocaleString()}</span>
									<span class="score-unit">pts</span>
								</div>
								<span class="history-chevron" aria-hidden="true"><ChevronRight size={20} /></span>
							</button>
						</li>
					{/each}
				</ul>
			{/if}
		</section>
	</main>
</div>

<style>
	.main {
		width: min(700px, calc(100% - 24px));
		margin: 16px auto 32px;
	}

	.section-label {
		margin: 0;
		color: var(--muted);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	h1 {
		margin: 8px 0 0;
		font-size: 24px;
		font-weight: 800;
		line-height: 1.15;
	}

	.desc {
		margin: 8px 0 0;
		color: var(--muted);
		font-size: 15px;
		line-height: 1.45;
	}

	.state-wrap {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 14px;
		min-height: 160px;
		margin-top: 20px;
	}

	.state-error {
		text-align: center;
	}

	.state-title {
		margin: 0;
		font-size: 15px;
		font-weight: 600;
		color: var(--ink);
	}

	.empty {
		margin-top: 20px;
		padding: 20px 16px;
		border: 1px dashed var(--line);
		border-radius: var(--radius-lg);
		background: color-mix(in srgb, var(--brand-light) 35%, var(--surface));
		text-align: center;
	}

	.empty-title {
		margin: 0;
		font-size: 15px;
		font-weight: 700;
	}

	.empty-copy {
		margin: 8px 0 16px;
		font-size: 14px;
		line-height: 1.45;
		color: var(--muted);
	}

	.history-list {
		list-style: none;
		margin: 18px 0 0;
		padding: 0;
		display: grid;
		gap: 10px;
	}

	.history-row {
		display: grid;
		grid-template-columns: 1fr auto auto;
		align-items: center;
		gap: 10px 12px;
		width: 100%;
		padding: 14px 14px;
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		background: linear-gradient(180deg, color-mix(in srgb, var(--surface) 88%, white), var(--surface));
		text-align: left;
		cursor: pointer;
		font: inherit;
		color: inherit;
		transition:
			border-color 140ms var(--ease),
			background 140ms var(--ease),
			transform 140ms var(--ease);
	}

	.history-row:hover {
		border-color: var(--brand);
		background: var(--brand-light);
		transform: translateX(2px);
	}

	.history-row:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.history-main {
		min-width: 0;
	}

	.history-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		flex-wrap: wrap;
	}

	.history-date {
		font-size: 13px;
		font-weight: 600;
		color: var(--muted);
	}

	.status-pill {
		padding: 3px 8px;
		border-radius: 999px;
		font-size: 10px;
		font-weight: 800;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		flex-shrink: 0;
	}

	.status-pill--done {
		background: var(--gold-light);
		color: var(--gold-dark);
	}

	.status-pill--abandoned {
		background: color-mix(in srgb, var(--muted) 22%, var(--surface));
		color: var(--muted);
	}

	.history-mode {
		margin: 6px 0 0;
		font-size: 15px;
		font-weight: 800;
		line-height: 1.2;
	}

	.history-meta {
		margin: 4px 0 0;
		font-size: 13px;
		color: var(--muted);
		line-height: 1.4;
	}

	.dot {
		margin: 0 4px;
	}

	.history-score {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 0;
		flex-shrink: 0;
	}

	.score-val {
		font-size: 17px;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
		color: var(--brand-dark);
	}

	.score-unit {
		font-size: 11px;
		font-weight: 600;
		color: var(--muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.history-chevron {
		color: var(--muted);
		display: flex;
		transition: color 140ms var(--ease), transform 140ms var(--ease);
	}

	.history-row:hover .history-chevron {
		color: var(--brand);
		transform: translateX(3px);
	}

	@media (max-width: 520px) {
		h1 {
			font-size: 20px;
		}

		.history-row {
			grid-template-columns: 1fr auto;
			grid-template-rows: auto auto;
		}

		.history-chevron {
			grid-column: 2;
			grid-row: 1 / span 2;
			align-self: center;
		}

		.history-score {
			grid-column: 1;
			flex-direction: row;
			align-items: baseline;
			gap: 6px;
		}
	}
</style>
