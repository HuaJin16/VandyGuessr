<script lang="ts">
import { onDestroy } from "svelte";
import { currentRound, gameStore } from "../stores/game.store";
import type { Game } from "../types";
import EndGameDialog from "./EndGameDialog.svelte";
import HudPill from "./HudPill.svelte";
import MapAssembly from "./MapAssembly.svelte";
import PanoramaViewer from "./PanoramaViewer.svelte";

export let game: Game;
export let onGuess: () => void;
export let onTimerExpiry: () => void;
export let onEndGame: () => void;

let timerSeconds = 0;
let timerInterval: ReturnType<typeof setInterval> | null = null;

$: round = $currentRound;
$: roundNumber = $gameStore.currentRoundIndex + 1;
$: isTimed = game.mode.timed;
$: isLastRound = roundNumber >= game.rounds.length;

$: if (isTimed && round?.expiresAt) {
	startTimer(round.expiresAt);
}

function startTimer(expiresAt: string) {
	stopTimer();
	const expiry = new Date(expiresAt).getTime();

	function tick() {
		const remaining = Math.max(0, Math.ceil((expiry - Date.now()) / 1000));
		timerSeconds = remaining;
		if (remaining <= 0) {
			stopTimer();
			onTimerExpiry();
		}
	}

	tick();
	timerInterval = setInterval(tick, 250);
}

function stopTimer() {
	if (timerInterval) {
		clearInterval(timerInterval);
		timerInterval = null;
	}
}

function formatTimer(seconds: number): string {
	const m = Math.floor(seconds / 60);
	const s = seconds % 60;
	return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function handleMapClick(pos: { lat: number; lng: number }) {
	gameStore.setGuessPosition(pos);
}

onDestroy(() => {
	stopTimer();
});
</script>

<div class="gameplay-root">
	{#if round}
		<PanoramaViewer imageUrl={round.imageUrl} />
	{/if}

	<div class="overlay" />

	<div class="hud-bar">
		<HudPill
			round={roundNumber}
			totalRounds={game.rounds.length}
			score={game.totalScore}
			timer={isTimed ? formatTimer(timerSeconds) : null}
			timerDanger={isTimed && timerSeconds < 10}
		/>
	</div>

	{#if !isLastRound}
		<button
			class="end-game-btn"
			title="End Game"
			on:click={() => gameStore.toggleEndDialog()}
		>
			<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<line x1="18" y1="6" x2="6" y2="18" />
				<line x1="6" y1="6" x2="18" y2="18" />
			</svg>
		</button>
	{/if}

	<MapAssembly
		position={$gameStore.guessPosition}
		disabled={$gameStore.submitting}
		onMapClick={handleMapClick}
		{onGuess}
	/>

	{#if $gameStore.showEndDialog}
		<EndGameDialog
			roundsCompleted={$gameStore.currentRoundIndex}
			totalRounds={game.rounds.length}
			currentScore={game.totalScore}
			skippedRounds={game.rounds.length - $gameStore.currentRoundIndex}
			on:cancel={() => gameStore.toggleEndDialog()}
			on:confirm={onEndGame}
		/>
	{/if}
</div>

<style>
	.gameplay-root {
		position: fixed;
		inset: 0;
		background: #000;
		overflow: hidden;
	}

	.overlay {
		position: absolute;
		inset: 0;
		background: rgba(0, 0, 0, 0.05);
		pointer-events: none;
		z-index: 1;
	}

	.hud-bar {
		position: absolute;
		top: 20px;
		left: 50%;
		transform: translateX(-50%);
		z-index: 30;
	}

	.end-game-btn {
		position: absolute;
		bottom: 20px;
		left: 20px;
		z-index: 30;
		width: 44px;
		height: 44px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(255, 255, 255, 0.9);
		backdrop-filter: blur(8px);
		border: 1px solid rgba(255, 255, 255, 0.5);
		border-radius: 12px;
		color: #18181b;
		cursor: pointer;
		box-shadow: 4px 4px 0px 0px rgba(0, 0, 0, 0.1);
		transition: background 0.15s;
	}

	.end-game-btn:hover {
		background: rgba(255, 255, 255, 1);
		color: #d95d39;
	}

	@media (max-width: 640px) {
		.hud-bar {
			top: 12px;
		}

		.end-game-btn {
			bottom: auto;
			top: 12px;
			left: 12px;
		}
	}
</style>
