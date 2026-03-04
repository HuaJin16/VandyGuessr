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

<div
	bind:this={element}
	aria-hidden={isSizer}
	class="lb-row {highlightUser ? 'you' : ''} {isSizer ? 'row-sizer' : ''}"
>
	<span class="rank-badge {rankBgClass(entry.rank)}">
		{entry.rank}
	</span>

	<div class="avatar" style:background={isCurrentUser ? 'var(--brand)' : undefined}>
		{initialsFor(entry.name)}
	</div>

	<div class="player-info">
		<p class="player-name">
			{entry.name}
			{#if isCurrentUser}
				<span class="you-badge">You</span>
			{/if}
		</p>
	</div>

	<span class="player-score">{formatScore(entry.avgScore)}</span>
	<span class="player-games">{entry.gamesPlayed} games</span>
</div>

<style>
	.lb-row {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 12px 16px;
		border-bottom: 1px solid var(--line);
		transition: background 120ms var(--ease);
	}

	.lb-row:last-child {
		border-bottom: none;
	}

	.lb-row:hover {
		background: rgba(0, 0, 0, 0.02);
	}

	.lb-row.you {
		background: var(--brand-light);
	}

	.lb-row.you:hover {
		background: rgba(46, 147, 60, 0.14);
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
		background: rgba(0, 0, 0, 0.05);
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
		flex: 1;
		min-width: 0;
	}

	.player-name {
		margin: 0;
		font-size: 15px;
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
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
		min-width: 50px;
		text-align: right;
	}

	.row-sizer {
		position: absolute;
		top: -9999px;
		left: -9999px;
		visibility: hidden;
		pointer-events: none;
	}

	@media (min-width: 700px) {
		.lb-row {
			padding: 14px 20px;
		}

		.avatar {
			width: 40px;
			height: 40px;
			font-size: 13px;
		}
	}

	@media (max-width: 400px) {
		.lb-row {
			padding: 10px 10px;
			gap: 8px;
		}

		.player-games {
			display: none;
		}

		.player-score {
			font-size: 13px;
		}

		.player-name {
			font-size: 13px;
		}

		.rank-badge {
			width: 24px;
			height: 24px;
			font-size: 11px;
		}

		.avatar {
			width: 30px;
			height: 30px;
			font-size: 10px;
		}
	}
</style>
