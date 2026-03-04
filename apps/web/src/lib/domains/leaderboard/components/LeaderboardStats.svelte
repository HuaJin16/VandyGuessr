<script lang="ts">
export let rank: number | null;
export let avgScore: number;
export let gamesPlayed: number;
export let roundsPlayed: number;
export let formatScore: (value: number) => string;
export let element: HTMLDivElement | undefined = undefined;
</script>

<div bind:this={element} class="stats-grid">
	<article class="stat">
		<p class="stat-label">Your Rank</p>
		<p class="stat-value">{rank ? `#${rank}` : "\u2014"}</p>
	</article>
	<article class="stat">
		<p class="stat-label">Avg Score</p>
		<p class="stat-value" style="color: var(--brand);">{formatScore(avgScore)}</p>
	</article>
	<article class="stat">
		<p class="stat-label">Games</p>
		<p class="stat-value">{gamesPlayed}</p>
	</article>
	<article class="stat">
		<p class="stat-label">Rounds</p>
		<p class="stat-value">{roundsPlayed}</p>
	</article>
</div>

<style>
	.stats-grid {
		margin-bottom: 0;
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 8px;
	}

	@media (min-width: 640px) {
		.stats-grid {
			grid-template-columns: repeat(4, 1fr);
		}
	}
</style>
