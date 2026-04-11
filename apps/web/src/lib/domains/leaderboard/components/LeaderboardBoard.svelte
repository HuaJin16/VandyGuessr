<script lang="ts">
import Button from "$lib/shared/ui/Button.svelte";
import Card from "$lib/shared/ui/Card.svelte";
import Spinner from "$lib/shared/ui/Spinner.svelte";
import { getInitials } from "$lib/shared/utils/initials";
import type { QueryObserverResult } from "@tanstack/svelte-query";
import { onMount, tick } from "svelte";
import type { LeaderboardEntry, LeaderboardResponse } from "../types";
import { observeResize } from "../utils/observeResize";
import LeaderboardRow from "./LeaderboardRow.svelte";

export let leaderboard: QueryObserverResult<LeaderboardResponse, Error>;
export let currentUserId: string | undefined;
export let currentUserName: string;
export let onSetLimit: (limit: number) => void;
export let offset = 0;
export let onSetOffset: (offset: number) => void = () => {};

let limit = 0;
let maxRows = 8;
let rowHeight = 72;
let topCount = 0;
let showEllipsis = false;

let mainEl: HTMLElement | undefined;
let tableContainerEl: HTMLElement | undefined;
let rowSizerEl: HTMLDivElement | undefined;
let cleanupResize: (() => void) | null = null;

const fallbackRowHeight = 72;

$: entries = leaderboard.data?.entries ?? [];
$: userEntry = leaderboard.data?.userEntry ?? null;
$: totalCount = leaderboard.data?.totalCount ?? entries.length;
$: currentPage = pageStep > 0 ? Math.floor(offset / pageStep) + 1 : 1;
$: totalPages = pageStep > 0 ? Math.max(1, Math.ceil(totalCount / pageStep)) : 1;
$: hasPrev = offset > 0;
$: hasNext = pageStep > 0 && offset + pageStep < totalCount;

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
	cleanupResize = observeResize([mainEl, tableContainerEl], () =>
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

$: if (leaderboard.data) {
	tick().then(updateMaxRows);
}

$: showUserFooter = !!userEntry;

$: if (maxRows > 0 && limit !== maxRows) {
	limit = maxRows;
	onSetLimit(limit);
}

$: if (showUserFooter) {
	topCount = Math.max(0, Math.min(entries.length, maxRows - 2));
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

$: pageStep = showUserFooter ? Math.max(1, maxRows - 2) : showEllipsis ? maxRows - 1 : maxRows;

$: visibleTopEntries = entries.slice(0, topCount);
</script>

<main class="lb-main" bind:this={mainEl}>
	<div bind:this={tableContainerEl}>
		<Card class="lb-card">
		{#if leaderboard.isLoading}
			<div class="table-state">
				<Spinner size={36} />
			</div>
		{:else if leaderboard.isError}
			<div class="table-state table-state--error">
				<p class="table-state__copy">Failed to load leaderboard.</p>
				<Button type="button" on:click={() => leaderboard.refetch()}>Retry</Button>
			</div>
		{:else if entries.length === 0}
			<div class="table-state table-state--empty">
				<p class="table-state__copy">No leaderboard results for this filter yet. "Today" is a CST time window, and Game Type controls Daily Challenge vs Random Drop.</p>
			</div>
		{:else}
			<div class="lb-columns" aria-hidden="true">
				<span>Rank</span>
				<span>Player</span>
				<span>Avg score</span>
				<span>Games</span>
			</div>

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
				<div class="separator">Your ranking</div>
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
		</Card>
	</div>

	{#if totalPages > 1}
		<nav class="pagination" aria-label="Leaderboard pages">
			<Button variant="outline" size="sm" disabled={!hasPrev} on:click={() => onSetOffset(Math.max(0, offset - pageStep))}>
				&larr; Previous
			</Button>
			<span class="page-info">Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong></span>
			<Button variant="outline" size="sm" disabled={!hasNext} on:click={() => onSetOffset(offset + pageStep)}>
				Next &rarr;
			</Button>
		</nav>
	{/if}
</main>

<style>
	.lb-main {
		display: grid;
		gap: 18px;
	}

	:global(.lb-card) {
		padding: 0;
		overflow: hidden;
	}

	.lb-columns {
		display: grid;
		grid-template-columns: 36px 36px minmax(0, 1fr) auto auto;
		gap: 12px;
		padding: 10px 20px;
		border-bottom: 1px solid var(--line);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.lb-columns span:nth-child(1) {
		grid-column: 1 / span 2;
	}

	.separator {
		padding: 8px 20px;
		border-bottom: 1px solid var(--line);
		background: var(--surface-subtle);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.table-state {
		display: grid;
		justify-items: center;
		gap: 12px;
		padding: 32px 20px;
		text-align: center;
	}

	.table-state__copy {
		margin: 0;
		font-size: 14px;
		line-height: 1.5;
		color: var(--muted);
	}

	.pagination {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 10px;
		padding: 4px 0 0;
		flex-wrap: wrap;
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

	@media (max-width: 560px) {
		.lb-columns {
			display: none;
		}
	}
</style>
