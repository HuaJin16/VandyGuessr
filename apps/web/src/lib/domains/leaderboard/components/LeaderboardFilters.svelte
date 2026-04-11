<script lang="ts">
import TogglePills from "$lib/shared/components/TogglePills.svelte";
import type { LeaderboardGameType, LeaderboardMode, LeaderboardTimeframe } from "../types";

export let timeframe: LeaderboardTimeframe;
export let mode: LeaderboardMode;
export let gameType: LeaderboardGameType;
export let onTimeframeChange: (value: LeaderboardTimeframe) => void;
export let onModeChange: (value: LeaderboardMode) => void;
export let onGameTypeChange: (value: LeaderboardGameType) => void;
</script>

<div class="filters">
	<div class="filter-group">
		<p class="filter-label">Timeframe</p>
		<TogglePills
			ariaLabel="Leaderboard timeframe"
			selected={timeframe}
			options={[
				{ value: "daily", label: "Today" },
				{ value: "weekly", label: "Weekly" },
				{ value: "alltime", label: "All Time" },
			]}
			on:change={(event) => {
				if (
					event.detail === "daily" ||
					event.detail === "weekly" ||
					event.detail === "alltime"
				) {
					onTimeframeChange(event.detail);
				}
			}}
		/>
	</div>

	<div class="filter-group">
		<p class="filter-label">Game Type</p>
		<TogglePills
			ariaLabel="Leaderboard game type"
			selected={gameType}
			options={[
				{ value: "all", label: "All" },
				{ value: "daily", label: "Daily Challenge" },
				{ value: "random", label: "Random Drop" },
			]}
			on:change={(event) => {
				if (
					event.detail === "all" ||
					event.detail === "daily" ||
					event.detail === "random"
				) {
					onGameTypeChange(event.detail);
				}
			}}
		/>
	</div>

	<div class="filter-group">
		<p class="filter-label">Environment</p>
		<TogglePills
			ariaLabel="Leaderboard mode"
			selected={mode}
			options={[
				{ value: "all", label: "All" },
				{ value: "indoor", label: "Indoor" },
				{ value: "outdoor", label: "Outdoor" },
			]}
			on:change={(event) => {
				if (
					event.detail === "all" ||
					event.detail === "indoor" ||
					event.detail === "outdoor"
				) {
					onModeChange(event.detail);
				}
			}}
		/>
	</div>
</div>

<style>
	.filters {
		display: flex;
		flex-wrap: wrap;
		justify-content: flex-end;
		gap: 14px;
	}

	.filter-group {
		display: grid;
		gap: 8px;
	}

	.filter-label {
		margin: 0;
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}
</style>
