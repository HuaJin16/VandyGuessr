<script lang="ts">
import { createEventDispatcher } from "svelte";
import type { Standing } from "../types";

export let standings: Standing[];
export let winnerId: string;
export let currentUserId: string;

const dispatch = createEventDispatcher<{ home: undefined }>();

$: isWinner = winnerId === currentUserId;
</script>

<div class="summary-container glass-card">
	{#if isWinner}
		<h1 class="title winner-title">You Win!</h1>
	{:else}
		<h1 class="title">Game Over</h1>
	{/if}

	<div class="podium">
		{#each standings as standing (standing.userId)}
			<div
				class="podium-entry"
				class:highlight={standing.userId === currentUserId}
				class:first={standing.rank === 1}
			>
				<span class="podium-rank">#{standing.rank}</span>
				<span class="podium-name">
					{standing.name}
					{#if standing.userId === currentUserId}
						<span class="you-tag">(You)</span>
					{/if}
				</span>
				<span class="podium-score">{standing.totalScore.toLocaleString()}</span>
			</div>
		{/each}
	</div>

	<button class="btn-3d home-btn" on:click={() => dispatch("home")}>
		Back to Home
	</button>
</div>

<style>
	.summary-container {
		padding: 32px 24px;
		max-width: 480px;
		margin: 0 auto;
		text-align: center;
	}
	.title {
		font-family: "Rubik", sans-serif;
		font-weight: 800;
		font-size: 1.75rem;
		color: #18181b;
		margin-bottom: 24px;
	}
	.winner-title {
		color: #f4c430;
	}
	.podium {
		display: flex;
		flex-direction: column;
		gap: 8px;
		margin-bottom: 28px;
	}
	.podium-entry {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 12px 16px;
		border-radius: 12px;
		background: rgba(0, 0, 0, 0.03);
	}
	.podium-entry.first {
		background: rgba(244, 196, 48, 0.1);
		border: 1px solid rgba(244, 196, 48, 0.3);
	}
	.podium-entry.highlight {
		border: 2px solid #2e933c;
	}
	.podium-rank {
		font-family: "Rubik", sans-serif;
		font-weight: 700;
		font-size: 1.125rem;
		color: #f4c430;
		min-width: 32px;
	}
	.podium-name {
		flex: 1;
		text-align: left;
		font-family: "Rubik", sans-serif;
		font-weight: 600;
		font-size: 1rem;
		color: #18181b;
	}
	.you-tag {
		font-weight: 400;
		font-size: 0.8125rem;
		color: #636363;
	}
	.podium-score {
		font-family: "Rubik", sans-serif;
		font-weight: 700;
		font-size: 1rem;
		color: #2e933c;
		font-variant-numeric: tabular-nums;
	}
	.home-btn {
		width: 100%;
	}
</style>
