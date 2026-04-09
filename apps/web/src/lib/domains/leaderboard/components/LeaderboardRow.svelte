<script lang="ts">
import type { LeaderboardEntry } from "../types";

export let entry: LeaderboardEntry;
export let highlightUser = false;
export let isCurrentUser = false;
export let initialsFor: (name: string) => string;
export let formatScore: (value: number) => string;
export let showMedal = true;
export let isSizer = false;
export let element: HTMLDivElement | undefined = undefined;

function rankBgClass(rank: number): string {
	if (!showMedal) return "rank-n";
	if (rank === 1) return "rank-1";
	if (rank === 2) return "rank-2";
	if (rank === 3) return "rank-3";
	return "rank-n";
}
</script>

<div bind:this={element} aria-hidden={isSizer} class="lb-row {highlightUser ? 'you' : ''} {isSizer ? 'row-sizer' : ''}">
	<span class="rank-badge {rankBgClass(entry.rank)}">{entry.rank}</span>

	<div class="avatar" style:background={isCurrentUser ? "var(--brand)" : undefined}>
		{initialsFor(entry.name)}
	</div>

	<div class="player-info">
		<p class="player-name">
			{entry.name}
			{#if isCurrentUser}
				<span class="you-badge">You</span>
			{/if}
		</p>
		<p class="player-meta">{entry.roundsPlayed} rounds · {entry.totalPoints.toLocaleString()} pts</p>
	</div>

	<span class="player-score">{formatScore(entry.avgScore)}</span>
	<span class="player-games">{entry.gamesPlayed} games</span>
</div>

<style>
	.lb-row {
		display: grid;
		grid-template-columns: 36px 36px minmax(0, 1fr) auto auto;
		align-items: center;
		gap: 12px;
		padding: 14px 20px;
		border-bottom: 1px solid var(--line);
		transition: background 120ms var(--ease);
	}

	.lb-row:last-child {
		border-bottom: none;
	}

	.lb-row:hover {
		background: var(--surface-subtle);
	}

	.lb-row.you {
		background: color-mix(in srgb, var(--brand-quiet) 90%, var(--surface));
	}

	.lb-row.you:hover {
		background: color-mix(in srgb, var(--brand-light) 65%, var(--surface));
	}

	.rank-badge {
		width: 28px;
		height: 28px;
		border-radius: var(--radius-sm);
		display: grid;
		place-items: center;
		font-size: 13px;
		font-weight: 800;
		flex-shrink: 0;
	}

	.rank-1 {
		background: var(--gold);
		color: #fff;
	}

	.rank-2 {
		background: #9ca3af;
		color: #fff;
	}

	.rank-3 {
		background: #b8804a;
		color: #fff;
	}

	.rank-n {
		background: var(--surface-strong);
		color: var(--muted);
	}

	.avatar {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		background: var(--brand);
		color: #fff;
		font-weight: 700;
		display: grid;
		place-items: center;
		font-size: 12px;
		flex-shrink: 0;
	}

	.player-info {
		min-width: 0;
	}

	.player-name,
	.player-meta {
		margin: 0;
	}

	.player-name {
		font-size: 15px;
		font-weight: 700;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.player-meta {
		margin-top: 4px;
		font-size: 12px;
		line-height: 1.4;
		color: var(--muted);
	}

	.you-badge {
		font-size: 10px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--brand-dark);
		background: rgba(46, 147, 60, 0.15);
		border-radius: var(--radius-pill);
		padding: 2px 7px;
		margin-left: 6px;
	}

	.player-score {
		font-family: "IBM Plex Mono", monospace;
		font-size: 15px;
		font-weight: 600;
		color: var(--ink);
		flex-shrink: 0;
	}

	.player-games {
		font-size: 12px;
		color: var(--muted);
		flex-shrink: 0;
		min-width: 64px;
		text-align: right;
	}

	.row-sizer {
		position: absolute;
		top: -9999px;
		left: -9999px;
		visibility: hidden;
		pointer-events: none;
	}

	@media (max-width: 560px) {
		.lb-row {
			grid-template-columns: 28px 32px minmax(0, 1fr) auto;
			gap: 10px;
			padding: 14px 14px;
		}

		.player-games {
			display: none;
		}

		.player-meta {
			display: none;
		}
	}
</style>
