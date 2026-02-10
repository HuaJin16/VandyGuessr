<script lang="ts">
export let round: number;
export let totalRounds: number;
export let score: number;
export let timer: string | null = null;
export let timerDanger = false;
export let showCheck = false;
</script>

<div class="hud-pill">
	<div class="hud-segment">
		<span class="hud-label">Round</span>
		<span class="hud-value font-mono">{round}/{totalRounds}</span>
	</div>
	<div class="hud-divider" />
	<div class="hud-segment">
		<span class="hud-label">Score</span>
		<span class="hud-value font-mono">{score.toLocaleString()}</span>
	</div>
	{#if timer !== null}
		<div class="hud-divider" />
		<div class="hud-segment">
			{#if showCheck}
				<span class="text-jungle text-xs">&#10003;</span>
			{/if}
			<span class="hud-value font-mono" class:text-clay={timerDanger} class:text-jungle={showCheck && !timerDanger}>
				{timer}
			</span>
		</div>
	{/if}
</div>

<style>
	.hud-pill {
		display: inline-flex;
		align-items: center;
		gap: 12px;
		padding: 8px 20px;
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(12px);
		border-radius: 9999px;
		box-shadow: 4px 4px 0px 0px rgba(0, 0, 0, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.5);
	}

	.hud-segment {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.hud-label {
		font-size: 11px;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: rgba(24, 24, 27, 0.4);
	}

	.hud-value {
		font-size: 16px;
		font-weight: 700;
		color: #18181b;
	}

	.hud-divider {
		width: 1px;
		height: 20px;
		background: rgba(24, 24, 27, 0.1);
	}
</style>
