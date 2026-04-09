<script lang="ts">
import { gameQueries } from "$lib/domains/games/queries/games.queries";
import type { GameMode } from "$lib/domains/games/types";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import Button from "$lib/shared/ui/Button.svelte";
import Card from "$lib/shared/ui/Card.svelte";
import PageHeader from "$lib/shared/ui/PageHeader.svelte";
import PageShell from "$lib/shared/ui/PageShell.svelte";
import StateBlock from "$lib/shared/ui/StateBlock.svelte";
import { createQuery } from "@tanstack/svelte-query";
import { ChevronRight, History as HistoryIcon } from "lucide-svelte";
import { navigate } from "svelte-routing";

const listParams = { limit: 50 } as const;

$: historyQuery = createQuery({
	...gameQueries.list(listParams, $auth.currentUserOid),
	enabled: $auth.currentUserOid !== null,
	staleTime: 0,
});

$: pastGames =
	$historyQuery.data
		?.filter((game) => game.status !== "active")
		.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()) ?? [];

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
	return new Date(iso).toLocaleString(undefined, {
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

	<PageShell size="content">
		<PageHeader
			eyebrow="Solo"
			title="Game history"
			copy="Browse completed and abandoned solo runs in a simple ledger. Open any row to revisit the full summary."
		/>

		{#if $historyQuery.isLoading}
			<StateBlock title="Loading game history" copy="Pulling your most recent solo runs now." />
		{:else if $historyQuery.isError}
			<StateBlock tone="error" title="Couldn't load history" copy="Try the request again or head back home.">
				<Button type="button" on:click={() => $historyQuery.refetch()}>Try again</Button>
				<Button variant="outline" type="button" on:click={() => navigate("/")}>Go home</Button>
			</StateBlock>
		{:else if pastGames.length === 0}
			<StateBlock tone="soft" title="No past games yet" copy="Finish a solo run from home, then your scorecards will show up here.">
				<Button type="button" on:click={() => navigate("/")}>Back to home</Button>
			</StateBlock>
		{:else}
			<Card>
				<ul class="history-list" aria-label="Past solo games">
					{#each pastGames as game (game.id)}
						<li>
							<button
								type="button"
								class="history-row"
								on:click={() => navigate(`/game/${game.id}/summary`)}
							>
								<div class="history-row__icon">
									<HistoryIcon size={16} />
								</div>
								<div class="history-row__main">
									<div class="history-row__top">
										<span class={`status-pill ${game.status === "completed" ? "status-pill--done" : "status-pill--abandoned"}`}>
											{game.status === "completed" ? "Completed" : "Abandoned"}
										</span>
										<span class="history-row__date">{formatPlayedAt(game.createdAt)}</span>
									</div>
									<p class="history-row__title">{getSoloModeLabel(game.mode)}</p>
									<p class="history-row__meta">
										{getEnvironmentLabel(game.mode.environment)}
										{#if !game.mode.daily}
											<span class="dot">·</span>
											{game.mode.timed ? "Timer on" : "No timer"}
										{/if}
									</p>
								</div>
								<div class="history-row__score">
									<span class="history-row__points">{game.totalScore.toLocaleString()}</span>
									<span class="history-row__unit">pts</span>
								</div>
								<span class="history-row__chevron" aria-hidden="true"><ChevronRight size={18} /></span>
							</button>
						</li>
					{/each}
				</ul>
			</Card>
		{/if}
	</PageShell>
</div>

<style>
	.history-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 10px;
	}

	.history-row {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) auto auto;
		align-items: center;
		gap: 14px;
		width: 100%;
		padding: 16px 18px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
		text-align: left;
		cursor: pointer;
		transition:
			border-color var(--duration-fast) var(--ease),
			background var(--duration-fast) var(--ease),
			transform var(--duration-fast) var(--ease);
	}

	.history-row:hover {
		border-color: color-mix(in srgb, var(--brand) 30%, var(--line));
		background: var(--surface-subtle);
		transform: translateY(-1px);
	}

	.history-row:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.history-row__icon {
		width: 40px;
		height: 40px;
		display: grid;
		place-items: center;
		border-radius: 999px;
		background: var(--brand-quiet);
		color: var(--brand-dark);
	}

	.history-row__main {
		min-width: 0;
	}

	.history-row__top {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 8px;
	}

	.status-pill {
		display: inline-flex;
		align-items: center;
		padding: 4px 8px;
		border-radius: var(--radius-pill);
		font-size: 10px;
		font-weight: 800;
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	.status-pill--done {
		background: var(--gold-light);
		color: var(--gold-ink);
	}

	.status-pill--abandoned {
		background: color-mix(in srgb, var(--muted) 12%, var(--surface-strong));
		color: var(--muted);
	}

	.history-row__date {
		font-size: 12px;
		font-weight: 600;
		color: var(--muted);
	}

	.history-row__title,
	.history-row__meta,
	.history-row__points,
	.history-row__unit {
		margin: 0;
	}

	.history-row__title {
		margin-top: 6px;
		font-size: 16px;
		font-weight: 800;
	}

	.history-row__meta {
		margin-top: 4px;
		font-size: 13px;
		line-height: 1.45;
		color: var(--muted);
	}

	.dot {
		margin: 0 4px;
	}

	.history-row__score {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 2px;
	}

	.history-row__points {
		font-family: "IBM Plex Mono", monospace;
		font-size: 17px;
		font-weight: 700;
		color: var(--brand-dark);
	}

	.history-row__unit {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.history-row__chevron {
		color: var(--muted);
		display: flex;
	}

	@media (max-width: 640px) {
		.history-row {
			grid-template-columns: auto minmax(0, 1fr) auto;
			grid-template-areas:
				"icon main chevron"
				"score score score";
		}

		.history-row__icon {
			grid-area: icon;
		}

		.history-row__main {
			grid-area: main;
		}

		.history-row__score {
			grid-area: score;
			flex-direction: row;
			justify-content: flex-start;
			align-items: baseline;
			gap: 6px;
			padding-left: 54px;
		}

		.history-row__chevron {
			grid-area: chevron;
		}
	}
</style>
