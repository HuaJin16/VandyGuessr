<script lang="ts">
import { getInitials } from "$lib/shared/utils/initials";
import type { QueryObserverResult } from "@tanstack/svelte-query";
import { onMount, tick } from "svelte";
import type { LeaderboardEntry, LeaderboardResponse } from "../types";
import { observeResize } from "../utils/observeResize";
import LeaderboardRow from "./LeaderboardRow.svelte";
import LeaderboardStats from "./LeaderboardStats.svelte";

export let leaderboard: QueryObserverResult<LeaderboardResponse, Error>;
export let currentUserId: string | undefined;
export let currentUserName: string;
export let onSetLimit: (limit: number) => void;
export let offset = 0;
export let onSetOffset: (offset: number) => void = () => {};

let limit = 0;
let maxRows = 8;
let rowHeight = 64;
let topCount = 0;
let showEllipsis = false;

let mainEl: HTMLElement | undefined;
let tableContainerEl: HTMLElement | undefined;
let statsEl: HTMLDivElement | undefined;
let rowSizerEl: HTMLDivElement | undefined;
let cleanupResize: (() => void) | null = null;

const fallbackRowHeight = 64;

$: entries = leaderboard.data?.entries ?? [];
$: userEntry = leaderboard.data?.userEntry ?? null;
$: totalCount = leaderboard.data?.totalCount ?? entries.length;
$: currentPage = limit > 0 ? Math.floor(offset / limit) + 1 : 1;
$: totalPages = limit > 0 ? Math.max(1, Math.ceil(totalCount / limit)) : 1;
$: hasPrev = offset > 0;
$: hasNext = limit > 0 && offset + limit < totalCount;

function isCurrentUser(entry: LeaderboardEntry) {
	return entry.userId === currentUserId;
}

function formatNumber(value: number) {
	return value.toLocaleString();
}

function formatScore(value: number) {
	return formatNumber(Math.round(value));
}

function updateMaxRows() {
	if (!tableContainerEl) return;

	const viewportHeight = window.innerHeight;
	const tableTop = tableContainerEl.getBoundingClientRect().top;
	const mainStyle = mainEl ? getComputedStyle(mainEl) : null;
	const mainPaddingBottom = mainStyle ? Number.parseFloat(mainStyle.paddingBottom) || 0 : 0;
	const rowSize = rowHeight || fallbackRowHeight;
	const bottomBuffer = 8;

	const available = viewportHeight - tableTop - mainPaddingBottom - bottomBuffer;
	const rowsSpace = Math.max(0, available);
	const nextMax = Math.max(1, Math.floor(rowsSpace / rowSize));
	if (nextMax !== maxRows) {
		maxRows = nextMax;
	}
}

onMount(() => {
	const handleResize = () => requestAnimationFrame(updateMaxRows);
	window.addEventListener("resize", handleResize);
	cleanupResize = observeResize([mainEl, tableContainerEl, statsEl], () =>
		requestAnimationFrame(updateMaxRows),
	);
	requestAnimationFrame(updateMaxRows);
	return () => {
		window.removeEventListener("resize", handleResize);
		cleanupResize?.();
	};
});

function setRowSizer(element: HTMLDivElement | undefined) {
	if (!element) return;
	const height = element.getBoundingClientRect().height;
	if (height && Math.abs(height - rowHeight) > 0.5) {
		rowHeight = height;
		updateMaxRows();
	}
}

$: if (tableContainerEl) {
	const style = getComputedStyle(tableContainerEl);
	if (style.position === "static") {
		tableContainerEl.style.position = "relative";
	}
}

$: if (rowSizerEl) {
	setRowSizer(rowSizerEl);
}

$: if (maxRows > 0 && limit !== maxRows) {
	limit = maxRows;
	onSetLimit(limit);
}

$: if (leaderboard.data) {
	tick().then(updateMaxRows);
}

$: showUserFooter = !!userEntry;

$: if (showUserFooter) {
	const available = maxRows - 2;
	topCount = Math.max(0, Math.min(entries.length, available));
	showEllipsis = false;
} else {
	const maxTop = Math.min(entries.length, maxRows);
	const hasMore = totalCount > maxTop;
	if (hasMore && maxRows > 1) {
		showEllipsis = true;
		topCount = Math.min(entries.length, maxRows - 1);
	} else {
		showEllipsis = false;
		topCount = maxTop;
	}
}

$: visibleTopEntries = entries.slice(0, topCount);
</script>

<main class="lb-main" bind:this={mainEl}>
	<slot name="filters" />

	<LeaderboardStats
		rank={userEntry ? userEntry.rank : null}
		avgScore={userEntry ? userEntry.avgScore : 0}
		gamesPlayed={userEntry ? userEntry.gamesPlayed : 0}
		roundsPlayed={userEntry ? userEntry.roundsPlayed : 0}
		formatScore={formatScore}
		bind:element={statsEl}
	/>

	<section class="card lb-card" bind:this={tableContainerEl}>
		{#if leaderboard.isLoading}
			<div class="flex items-center justify-center px-6 py-10">
				<div class="loading-spinner" />
			</div>
		{:else if leaderboard.isError}
			<div class="flex flex-col items-center gap-3 px-6 py-10 text-center">
				<p class="text-sm text-muted">Failed to load leaderboard.</p>
				<button class="btn-3d px-4 py-2 text-sm" on:click={() => leaderboard.refetch()}>
					Retry
				</button>
			</div>
		{:else if entries.length === 0}
			<div class="flex flex-col items-center gap-2 px-6 py-10 text-center">
				<p class="text-sm text-muted">No leaderboard results yet.</p>
				<p class="text-xs text-muted opacity-60">Try another timeframe or mode.</p>
			</div>
		{:else}
			<LeaderboardRow
				entry={{
					rank: 1,
					userId: "",
					name: "AA",
					username: "",
					totalPoints: 0,
					avgScore: 0,
					gamesPlayed: 0,
					roundsPlayed: 0,
				}}
				initialsFor={getInitials}
				formatScore={formatScore}
				showMedal={false}
				isSizer={true}
				bind:element={rowSizerEl}
			/>

			{#if rowSizerEl}
				{#each visibleTopEntries as entry}
					<LeaderboardRow
						{entry}
						initialsFor={getInitials}
						formatScore={formatScore}
						isCurrentUser={isCurrentUser(entry)}
						highlightUser={isCurrentUser(entry)}
					/>
				{/each}
			{/if}

			{#if showUserFooter}
				<div class="separator">Your Ranking</div>
			{:else if showEllipsis}
				<div class="separator">&middot; &middot; &middot;</div>
			{/if}

			{#if showUserFooter && userEntry}
				<LeaderboardRow
					entry={{
						rank: userEntry.rank,
						userId: userEntry.userId,
						name: userEntry.name || currentUserName,
						username: userEntry.username,
						totalPoints: userEntry.totalPoints,
						avgScore: userEntry.avgScore,
						gamesPlayed: userEntry.gamesPlayed,
						roundsPlayed: userEntry.roundsPlayed,
					}}
					initialsFor={getInitials}
					formatScore={formatScore}
					isCurrentUser={true}
					highlightUser={true}
					showMedal={false}
				/>
			{/if}
		{/if}
	</section>

	{#if totalPages > 1}
		<nav class="pagination" aria-label="Leaderboard pages">
			<button
				class="page-btn"
				disabled={!hasPrev}
				on:click={() => onSetOffset(Math.max(0, offset - limit))}
			>
				&larr; Previous
			</button>
			<span class="page-info">Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong></span>
			<button
				class="page-btn"
				disabled={!hasNext}
				on:click={() => onSetOffset(offset + limit)}
			>
				Next &rarr;
			</button>
		</nav>
	{/if}
</main>

<style>
	.lb-main {
		width: min(640px, calc(100% - 32px));
		margin: 16px auto 24px;
		display: grid;
		gap: 14px;
	}

	.lb-card {
		padding: 0;
		overflow: hidden;
	}

	.separator {
		padding: 8px 16px;
		border-bottom: 1px solid var(--line);
		background: #faf9f6;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.loading-spinner {
		width: 36px;
		height: 36px;
		border: 3px solid rgba(0, 0, 0, 0.1);
		border-top-color: var(--brand);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	@media (min-width: 700px) {
		.separator {
			padding: 8px 20px;
		}
	}

	.pagination {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		padding: 14px 0 0;
	}

	.page-btn {
		border: 1px solid var(--line);
		border-radius: var(--radius-sm);
		background: var(--surface);
		color: var(--ink);
		font-family: Inter, sans-serif;
		font-size: 13px;
		font-weight: 600;
		padding: 8px 14px;
		cursor: pointer;
		transition: all 120ms var(--ease);
		box-shadow: var(--shadow-sm);
	}

	.page-btn:hover:not(:disabled) {
		border-color: var(--brand);
		color: var(--brand);
		background: var(--brand-light);
	}

	.page-btn:focus-visible { outline: none; box-shadow: var(--ring); }

	.page-btn:disabled {
		opacity: 0.4;
		cursor: default;
		pointer-events: none;
	}

	.page-info {
		font-size: 13px;
		color: var(--muted);
		font-weight: 500;
		padding: 0 4px;
	}

	.page-info :global(strong) {
		color: var(--ink);
	}
</style>
