<script lang="ts">
export let rank: number | null;
export let avgScore: number;
export let gamesPlayed: number;
export let roundsPlayed: number;
export let formatScore: (value: number) => string;
export let element: HTMLDivElement | undefined = undefined;
</script>

<div bind:this={element} class="mt-5 grid grid-cols-2 gap-3 sm:mt-6 sm:grid-cols-4 sm:gap-4">
	<div class="stats-card">
		<p class="stats-label">Your Rank</p>
		<p class="stats-value">{rank ? `#${rank}` : "—"}</p>
	</div>
	<div class="stats-card">
		<p class="stats-label">Avg Score</p>
		<p class="stats-value text-jungle">{formatScore(avgScore)}</p>
	</div>
	<div class="stats-card">
		<p class="stats-label">Games</p>
		<p class="stats-value">{gamesPlayed}</p>
	</div>
	<div class="stats-card">
		<p class="stats-label">Rounds</p>
		<p class="stats-value">{roundsPlayed}</p>
	</div>
</div>

<style>
	.stats-card {
		background: white;
		border-radius: 12px;
		padding: 12px;
		box-shadow: 4px 4px 0px 0px rgba(0, 0, 0, 0.1);
		text-align: center;
	}

	.stats-label {
		font-size: 10px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: rgba(24, 24, 27, 0.5);
		margin-bottom: 4px;
	}

	.stats-value {
		font-family: "Rubik", sans-serif;
		font-weight: 700;
		font-size: 20px;
		color: #18181b;
	}

	@media (min-width: 640px) {
		.stats-card {
			padding: 16px;
		}

		.stats-label {
			font-size: 12px;
		}

		.stats-value {
			font-size: 24px;
		}
	}
</style>
