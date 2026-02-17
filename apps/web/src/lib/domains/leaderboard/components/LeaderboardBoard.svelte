<script lang="ts">
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

let limit = 0;
let maxRows = 8;
let rowHeight = 64;
let topCount = 0;
let showEllipsis = false;

let mainEl: HTMLElement | undefined;
let tableContainerEl: HTMLElement | undefined;
let tableHeaderEl: HTMLElement | undefined;
let statsEl: HTMLDivElement | undefined;
let rowSizerEl: HTMLDivElement | undefined;
let cleanupResize: (() => void) | null = null;

const fallbackRowHeight = 64;

$: entries = leaderboard.data?.entries ?? [];
$: userEntry = leaderboard.data?.userEntry ?? null;
$: contextEntries = leaderboard.data?.contextEntries ?? [];
$: totalCount = leaderboard.data?.totalCount ?? entries.length;

function initialsFor(name: string) {
	return name
		.split(" ")
		.filter(Boolean)
		.map((w) => w[0])
		.join("")
		.slice(0, 2)
		.toUpperCase();
}

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
	if (!tableContainerEl || !statsEl || !tableHeaderEl) return;

	const viewportHeight = window.innerHeight;
	const tableTop = tableContainerEl.getBoundingClientRect().top;
	const statsRect = statsEl.getBoundingClientRect();
	const statsStyle = getComputedStyle(statsEl);
	const statsMarginTop = Number.parseFloat(statsStyle.marginTop) || 0;
	const mainStyle = mainEl ? getComputedStyle(mainEl) : null;
	const mainPaddingBottom = mainStyle ? Number.parseFloat(mainStyle.paddingBottom) || 0 : 0;
	const headerHeight = tableHeaderEl.getBoundingClientRect().height;
	const rowSize = rowHeight || fallbackRowHeight;
	const bottomBuffer = 8;

	const available =
		viewportHeight -
		tableTop -
		statsRect.height -
		statsMarginTop -
		mainPaddingBottom -
		bottomBuffer;
	const rowsSpace = Math.max(0, available - headerHeight);
	const nextMax = Math.max(1, Math.floor(rowsSpace / rowSize));
	if (nextMax !== maxRows) {
		maxRows = nextMax;
	}
}

onMount(() => {
	const handleResize = () => requestAnimationFrame(updateMaxRows);
	window.addEventListener("resize", handleResize);
	cleanupResize = observeResize([mainEl, tableContainerEl, tableHeaderEl, statsEl], () =>
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

$: isUserInTop = !!userEntry && entries.some((entry) => entry.userId === userEntry.userId);
$: showUserBlock = !!userEntry && !isUserInTop;
$: contextAboveRaw =
	showUserBlock && userEntry ? contextEntries.filter((entry) => entry.rank < userEntry.rank) : [];
$: contextBelowRaw =
	showUserBlock && userEntry ? contextEntries.filter((entry) => entry.rank > userEntry.rank) : [];
$: contextAbove = [] as LeaderboardEntry[];
$: contextBelow = [] as LeaderboardEntry[];
$: if (showUserBlock && userEntry) {
	const maxContext = Math.max(0, maxRows - 1);
	const above = contextAboveRaw.slice(-1);
	const below = contextBelowRaw.slice(0, 1);
	if (maxContext >= 2) {
		contextAbove = above;
		contextBelow = below;
	} else if (maxContext === 1) {
		contextAbove = above.length ? above : [];
		contextBelow = contextAbove.length ? [] : below;
	} else {
		contextAbove = [];
		contextBelow = [];
	}
} else {
	contextAbove = [];
	contextBelow = [];
}

$: if (showUserBlock) {
	const reservedBase = contextAbove.length + contextBelow.length + 1;
	let available = maxRows - reservedBase;
	const shouldShowEllipsis = available > 0;
	if (shouldShowEllipsis) {
		available -= 1;
	}
	const nextTopCount = Math.max(0, Math.min(entries.length, available));
	showEllipsis = shouldShowEllipsis && nextTopCount > 0;
	topCount = nextTopCount;
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

<main class="mx-auto max-w-4xl px-4 py-5 sm:px-6 sm:py-6" bind:this={mainEl}>
	<slot name="filters" />

	<div class="overflow-hidden rounded-2xl bg-white shadow-hard" bind:this={tableContainerEl}>
		<div class="bg-terrain/50 px-4 py-3 sm:px-6 sm:py-4" bind:this={tableHeaderEl}>
			<div class="grid grid-cols-12 gap-2 text-[10px] font-semibold uppercase tracking-wider text-charcoal/50 sm:gap-4 sm:text-xs">
				<div class="col-span-1 text-center">#</div>
				<div class="col-span-6 sm:col-span-5">Player</div>
				<div class="col-span-3 text-right">Avg Score</div>
				<div class="col-span-2 text-right sm:col-span-3">Games</div>
			</div>
		</div>

		{#if leaderboard.isLoading}
			<div class="flex items-center justify-center px-6 py-10">
				<div class="loading-spinner" />
			</div>
		{:else if leaderboard.isError}
			<div class="flex flex-col items-center gap-3 px-6 py-10 text-center">
				<p class="text-sm text-charcoal/60">Failed to load leaderboard.</p>
				<button class="btn-3d px-4 py-2 text-sm" on:click={() => leaderboard.refetch()}>
					Retry
				</button>
			</div>
		{:else if entries.length === 0}
			<div class="flex flex-col items-center gap-2 px-6 py-10 text-center">
				<p class="text-sm text-charcoal/60">No leaderboard results yet.</p>
				<p class="text-xs text-charcoal/40">Try another timeframe or mode.</p>
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
				}}
				initialsFor={initialsFor}
				formatScore={formatScore}
				showUsername={false}
				showMedal={false}
				isSizer={true}
				bind:element={rowSizerEl}
			/>
			<div class="divide-y divide-gray-50">
				{#if rowSizerEl}
					{#each visibleTopEntries as entry}
						<LeaderboardRow
							{entry}
							initialsFor={initialsFor}
							formatScore={formatScore}
							isCurrentUser={isCurrentUser(entry)}
							highlightUser={isCurrentUser(entry)}
						/>
					{/each}
				{/if}

				{#if showEllipsis}
					<div class="bg-terrain/30 px-4 py-2 text-center sm:px-6 sm:py-3">
						<span class="font-mono text-xs text-charcoal/30 sm:text-sm">• • •</span>
					</div>
				{/if}

				{#if showUserBlock}
					{#each contextAbove as entry}
						<LeaderboardRow
							{entry}
							initialsFor={initialsFor}
							formatScore={formatScore}
							showMedal={false}
						/>
					{/each}

					{#if userEntry}
						<LeaderboardRow
							entry={{
								rank: userEntry.rank,
								userId: userEntry.userId,
								name: userEntry.name || currentUserName,
								username: userEntry.username,
								totalPoints: userEntry.totalPoints,
								avgScore: userEntry.avgScore,
								gamesPlayed: userEntry.gamesPlayed,
							}}
							initialsFor={initialsFor}
							formatScore={formatScore}
							isCurrentUser={true}
							highlightUser={true}
							highlightAvatar={true}
							showMedal={false}
							showUsername={false}
						/>
					{/if}

					{#each contextBelow as entry}
						<LeaderboardRow
							{entry}
							initialsFor={initialsFor}
							formatScore={formatScore}
							showMedal={false}
						/>
					{/each}
				{/if}
			</div>
		{/if}
	</div>

	<LeaderboardStats
		rank={userEntry ? userEntry.rank : null}
		avgScore={userEntry ? userEntry.avgScore : 0}
		gamesPlayed={userEntry ? userEntry.gamesPlayed : 0}
		formatScore={formatScore}
		bind:element={statsEl}
	/>
</main>

<style>
	.loading-spinner {
		width: 36px;
		height: 36px;
		border: 3px solid rgba(24, 24, 27, 0.1);
		border-top-color: #2e933c;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

</style>
