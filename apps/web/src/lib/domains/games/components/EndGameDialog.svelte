<script lang="ts">
import ConfirmDialog from "$lib/shared/components/ConfirmDialog.svelte";
import { createEventDispatcher } from "svelte";

export let roundsCompleted: number;
export let totalRounds: number;
export let currentScore: number;
export let skippedRounds: number;

const dispatch = createEventDispatcher<{ cancel: undefined; confirm: undefined }>();
</script>

<ConfirmDialog
	open={true}
	title="End Game Early?"
	description="Are you sure you want to end this game? This action cannot be undone."
	variant="warning"
	confirmLabel="End Game"
	onConfirm={() => dispatch("confirm")}
	onCancel={() => dispatch("cancel")}
>
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
				<circle cx="12" cy="12" r="10" />
				<line x1="12" y1="16" x2="12" y2="12" />
				<line x1="12" y1="8" x2="12.01" y2="8" />
			</svg>
			<span>{skippedRounds} remaining round{skippedRounds > 1 ? "s" : ""} will be marked as skipped with a score of 0</span>
		</div>
	{/if}
</ConfirmDialog>

<style>
	.stats-block {
		width: 100%;
		margin-top: 20px;
		padding: 16px;
		background: var(--canvas);
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
	}

	.warning-notice {
		width: 100%;
		margin-top: 16px;
		padding: 12px 16px;
		background: var(--danger-light);
		border: 1px solid rgba(220, 74, 58, 0.2);
		border-radius: var(--radius-sm);
		display: flex;
		align-items: flex-start;
		gap: 10px;
		font-size: 13px;
		color: var(--danger);
	}
</style>
