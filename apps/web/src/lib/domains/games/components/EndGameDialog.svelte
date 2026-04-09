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
	title="End this run early?"
	description="The current game will finish immediately and any remaining rounds will score 0."
	variant="warning"
	confirmLabel="End Game"
	onConfirm={() => dispatch("confirm")}
	onCancel={() => dispatch("cancel")}
>
	<div class="dialog-grid">
		<div class="stat">
			<p class="stat-label">Rounds completed</p>
			<p class="stat-value">{roundsCompleted}/{totalRounds}</p>
		</div>
		<div class="stat">
			<p class="stat-label">Current score</p>
			<p class="stat-value" style="color: var(--brand-dark);">{currentScore.toLocaleString()}</p>
		</div>
	</div>

	{#if skippedRounds > 0}
		<div class="warning-note">
			<p>
				<strong>{skippedRounds}</strong> remaining round{skippedRounds > 1 ? "s" : ""} will be marked as skipped with a score of 0.
			</p>
		</div>
	{/if}
</ConfirmDialog>

<style>
	.dialog-grid {
		width: 100%;
		margin-top: 18px;
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 12px;
	}

	.warning-note {
		margin-top: 14px;
		padding: 12px 14px;
		border-radius: var(--radius-md);
		background: color-mix(in srgb, var(--danger-light) 60%, var(--surface));
		border: 1px solid color-mix(in srgb, var(--danger) 24%, var(--line));
	}

	.warning-note p {
		margin: 0;
		font-size: 13px;
		line-height: 1.5;
		color: var(--danger-ink);
	}
</style>
