<script lang="ts">
import type { LeaderboardMode, LeaderboardTimeframe } from "../types";

export let timeframe: LeaderboardTimeframe;
export let mode: LeaderboardMode;
export let onTimeframeChange: (value: LeaderboardTimeframe) => void;
export let onModeChange: (value: LeaderboardMode) => void;
</script>

<div class="mb-5 flex flex-wrap gap-3 sm:mb-6 sm:gap-4">
	<div class="toggle-group">
		<button
			class={timeframe === "daily" ? "toggle-active" : "toggle-inactive"}
			on:click={() => onTimeframeChange("daily")}
		>Daily</button>
		<button
			class={timeframe === "weekly" ? "toggle-active" : "toggle-inactive"}
			on:click={() => onTimeframeChange("weekly")}
		>Weekly</button>
		<button
			class={timeframe === "alltime" ? "toggle-active" : "toggle-inactive"}
			on:click={() => onTimeframeChange("alltime")}
		>All Time</button>
	</div>

	<div class="toggle-group">
		<button
			class={mode === "all" ? "toggle-active" : "toggle-inactive"}
			on:click={() => onModeChange("all")}
		>All</button>
		<button
			class={mode === "indoor" ? "toggle-active" : "toggle-inactive"}
			on:click={() => onModeChange("indoor")}
		>Indoor</button>
		<button
			class={mode === "outdoor" ? "toggle-active" : "toggle-inactive"}
			on:click={() => onModeChange("outdoor")}
		>Outdoor</button>
	</div>
</div>

<style>
	.toggle-group {
		display: flex;
		border-radius: 9999px;
		padding: 3px;
		border: 1px solid rgba(0, 0, 0, 0.08);
		background: white;
	}

	@media (min-width: 640px) {
		.toggle-group {
			display: inline-flex;
		}
	}

	.toggle-active {
		display: inline-flex;
		flex: 1;
		align-items: center;
		justify-content: center;
		gap: 5px;
		background: #2e933c;
		color: white;
		border-radius: 9999px;
		padding: 7px 16px;
		font-size: 13px;
		font-weight: 600;
		transition: all 0.15s;
	}

	@media (min-width: 640px) {
		.toggle-active {
			flex: none;
		}
	}

	.toggle-inactive {
		display: inline-flex;
		flex: 1;
		align-items: center;
		justify-content: center;
		gap: 5px;
		background: transparent;
		color: #18181b;
		border-radius: 9999px;
		padding: 7px 16px;
		font-size: 13px;
		font-weight: 500;
		transition: all 0.15s;
		cursor: pointer;
	}

	@media (min-width: 640px) {
		.toggle-inactive {
			flex: none;
		}
	}

	.toggle-inactive:hover {
		background: rgba(46, 147, 60, 0.08);
	}
</style>
