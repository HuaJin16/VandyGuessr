<script lang="ts">
import { Trophy } from "lucide-svelte";
import type { LeaderboardEntry } from "../types";

export let entry: LeaderboardEntry;
export let showUsername = true;
export let highlightUser = false;
export let highlightAvatar = false;
export let isCurrentUser = false;
export let initialsFor: (name: string) => string;
export let formatScore: (value: number) => string;
export let showMedal = true;
export let isSizer = false;
export let element: HTMLDivElement | undefined = undefined;

function rankIcon(rank: number) {
	if (rank === 1) return "gold";
	if (rank === 2) return "silver";
	if (rank === 3) return "bronze";
	return null;
}
</script>

<div
	bind:this={element}
	aria-hidden={isSizer}
	class={`leaderboard-row px-4 py-3 sm:px-6 sm:py-4 ${
		highlightUser ? "user-row" : ""
	} ${isSizer ? "row-sizer" : ""}`}
>
	<div class="grid grid-cols-12 items-center gap-2 sm:gap-4">
		<div class="col-span-1 rank-cell">
			{#if showMedal && rankIcon(entry.rank)}
				<Trophy size={22} class={`trophy-${rankIcon(entry.rank)}`} />
			{:else}
				<span class={`rank-number ${highlightUser ? "rank-user" : ""}`}>
					{entry.rank}
				</span>
			{/if}
		</div>
		<div class="col-span-6 flex items-center gap-2 sm:col-span-5 sm:gap-3">
			<div
				class={`avatar-initials flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold ${
					highlightAvatar ? "avatar-highlight text-charcoal" : "text-white"
				} sm:h-10 sm:w-10 sm:text-sm`}
			>
				{initialsFor(entry.name)}
			</div>
			<div class="min-w-0">
				<p class="truncate text-sm font-semibold text-charcoal sm:text-base">
					{entry.name}
				</p>
				{#if showUsername}
					<p class="hidden text-[10px] text-charcoal/50 sm:block sm:text-xs">
						@{entry.username}
					</p>
				{/if}
			</div>
			{#if isCurrentUser}
				<span class="ml-1 rounded-full bg-gold/20 px-2 py-0.5 text-[8px] font-semibold text-gold sm:text-xs">
					YOU
				</span>
			{/if}
		</div>
		<div class="col-span-3 text-right">
			<span class="font-mono text-sm font-bold text-charcoal sm:text-lg">
				{formatScore(entry.avgScore)}
			</span>
		</div>
		<div class="col-span-2 text-right sm:col-span-3">
			<span class="font-mono text-xs text-charcoal/70 sm:text-base">
				{entry.gamesPlayed}
			</span>
		</div>
	</div>
</div>

<style>
	.leaderboard-row:hover {
		background: rgba(245, 242, 233, 0.5);
	}

	.user-row {
		background: rgba(244, 196, 48, 0.12);
		box-shadow: inset 4px 0 0 #f4c430;
	}

	.avatar-initials {
		background: linear-gradient(135deg, #2e933c 0%, #236e2d 100%);
	}

	.avatar-highlight {
		background: linear-gradient(135deg, #f4c430 0%, #f59e0b 100%);
	}

	:global(.trophy-gold) {
		fill: #f4c430;
	}

	:global(.trophy-silver) {
		fill: #c0c0c0;
	}

	:global(.trophy-bronze) {
		fill: #cd7f32;
	}

	.rank-number {
		font-family: "JetBrains Mono", monospace;
		font-size: 14px;
		font-weight: 700;
		color: rgba(24, 24, 27, 0.7);
	}

	.rank-user {
		color: #f4c430;
	}

	.rank-cell {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 24px;
	}

	.row-sizer {
		position: absolute;
		top: -9999px;
		left: -9999px;
		padding: 12px 16px;
		visibility: hidden;
		pointer-events: none;
	}

	@media (min-width: 640px) {
		.row-sizer {
			padding: 16px 24px;
		}
	}
</style>
