<script lang="ts">
import TogglePills from "$lib/shared/components/TogglePills.svelte";
import type { LeaderboardMode, LeaderboardTimeframe } from "../types";

export let timeframe: LeaderboardTimeframe;
export let mode: LeaderboardMode;
export let onTimeframeChange: (value: LeaderboardTimeframe) => void;
export let onModeChange: (value: LeaderboardMode) => void;
</script>

<div class="filters">
	<TogglePills
		ariaLabel="Leaderboard timeframe"
		selected={timeframe}
		options={[
			{ value: "daily", label: "Daily" },
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

<style>
	.filters {
		display: flex;
		gap: 10px;
		flex-wrap: wrap;
	}
</style>
