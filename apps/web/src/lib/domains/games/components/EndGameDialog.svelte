<script lang="ts">
import { createEventDispatcher } from "svelte";

export let roundsCompleted: number;
export let totalRounds: number;
export let currentScore: number;
export let skippedRounds: number;

const dispatch = createEventDispatcher<{ cancel: undefined; confirm: undefined }>();
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<div class="backdrop" on:click={() => dispatch("cancel")}>
	<div class="dialog" on:click|stopPropagation>
		<div class="icon-circle">
			<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#D95D39" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
				<line x1="12" y1="9" x2="12" y2="13"></line>
				<line x1="12" y1="17" x2="12.01" y2="17"></line>
			</svg>
		</div>

		<h2 class="font-heading text-2xl font-bold text-charcoal text-center">End Game Early?</h2>
		<p class="text-charcoal/60 text-center text-sm mt-2">
			Are you sure you want to end this game? This action cannot be undone.
		</p>

		<div class="stats-block">
			<div class="stat">
				<div class="stat-label">Rounds Completed</div>
				<div class="stat-value font-mono">{roundsCompleted}/{totalRounds}</div>
			</div>
			<div class="stat">
				<div class="stat-label">Current Score</div>
				<div class="stat-value font-mono text-jungle">{currentScore.toLocaleString()}</div>
			</div>
		</div>

		{#if skippedRounds > 0}
			<div class="warning-notice">
				<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<circle cx="12" cy="12" r="10"></circle>
					<line x1="12" y1="16" x2="12" y2="12"></line>
					<line x1="12" y1="8" x2="12.01" y2="8"></line>
				</svg>
				<span>{skippedRounds} remaining round{skippedRounds > 1 ? "s" : ""} will be marked as skipped with a score of 0</span>
			</div>
		{/if}

		<div class="actions">
			<button class="btn-cancel" on:click={() => dispatch("cancel")}>Cancel</button>
			<button class="btn-end" on:click={() => dispatch("confirm")}>
				<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
					<polyline points="16 17 21 12 16 7"></polyline>
					<line x1="21" y1="12" x2="9" y2="12"></line>
				</svg>
				End Game
			</button>
		</div>
	</div>
</div>

<style>
	.backdrop {
		position: fixed;
		inset: 0;
		z-index: 100;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(4px);
	}

	.dialog {
		width: 100%;
		max-width: 28rem;
		margin: 0 16px;
		padding: 32px;
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(24px);
		border-radius: 16px;
		border: 1px solid rgba(255, 255, 255, 0.5);
		box-shadow: 6px 6px 0px 0px rgba(0, 0, 0, 0.15);
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.icon-circle {
		width: 56px;
		height: 56px;
		border-radius: 50%;
		background: rgba(217, 93, 57, 0.1);
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 16px;
	}

	.stats-block {
		width: 100%;
		margin-top: 20px;
		padding: 16px;
		background: rgba(245, 242, 233, 0.5);
		border-radius: 12px;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
	}

	.stat-label {
		font-size: 11px;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: rgba(24, 24, 27, 0.4);
		margin-bottom: 4px;
	}

	.stat-value {
		font-size: 20px;
		font-weight: 700;
		color: #18181b;
	}

	.warning-notice {
		width: 100%;
		margin-top: 16px;
		padding: 12px 16px;
		background: rgba(217, 93, 57, 0.05);
		border: 1px solid rgba(217, 93, 57, 0.2);
		border-radius: 10px;
		display: flex;
		align-items: flex-start;
		gap: 10px;
		font-size: 13px;
		color: #d95d39;
	}

	.actions {
		width: 100%;
		margin-top: 24px;
		display: flex;
		gap: 12px;
	}

	.btn-cancel {
		flex: 1;
		padding: 12px;
		font-size: 14px;
		font-weight: 600;
		color: #18181b;
		background: rgba(255, 255, 255, 0.8);
		border: 2px solid rgba(24, 24, 27, 0.2);
		border-radius: 12px;
		cursor: pointer;
		transition: background 0.15s;
	}

	.btn-cancel:hover {
		background: rgba(24, 24, 27, 0.05);
	}

	.btn-end {
		flex: 1;
		padding: 12px;
		font-size: 14px;
		font-weight: 600;
		color: white;
		background: #d95d39;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		transition: background 0.15s;
	}

	.btn-end:hover {
		background: #c14e2e;
	}
</style>
