<script lang="ts">
import { onDestroy } from "svelte";
import { navigate } from "svelte-routing";
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
	const minutes = Math.floor(seconds / 60);
	const secs = seconds % 60;
	return `${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function handleMapClick(position: { lat: number; lng: number }) {
	gameStore.setGuessPosition(position);
}

onDestroy(() => {
	stopTimer();
});
</script>

<div class="scene">
	{#if round}
		<PanoramaViewer imageUrl={round.imageUrl} imageTiles={round.imageTiles} />
	{/if}
</div>

<main class="shell">
	<div class="topbar">
		<div class="topbar__slot">
			{#if !isLastRound}
				<button class="ghost" aria-label="End game" on:click={() => gameStore.toggleEndDialog()}>
					<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
						<line x1="18" y1="6" x2="6" y2="18" />
						<line x1="6" y1="6" x2="18" y2="18" />
					</svg>
					<span class="ghost-label">End Game</span>
				</button>
			{/if}
		</div>

		<div class="hud-center">
			<HudPill
				round={roundNumber}
				totalRounds={game.rounds.length}
				score={game.totalScore}
				timer={isTimed ? formatTimer(timerSeconds) : null}
				timerDanger={isTimed && timerSeconds < 10}
			/>
		</div>

		<div class="topbar__slot topbar__slot--end">
			<button class="ghost" aria-label="Go home" on:click={() => navigate("/", { replace: true })}>
				<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M3 10.5L12 3l9 7.5" />
					<path d="M5.5 9.5V21h13V9.5" />
				</svg>
				<span class="ghost-label">Home</span>
			</button>
		</div>
	</div>

	<div class="dock-slot">
		<MapAssembly
			position={$gameStore.guessPosition}
			disabled={$gameStore.submitting}
			onMapClick={handleMapClick}
			{onGuess}
		/>
	</div>
</main>

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

<style>
	.scene {
		position: fixed;
		inset: 0;
		background: #1c1917;
	}

	.shell {
		position: relative;
		z-index: 2;
		min-height: 100vh;
		min-height: 100dvh;
		display: grid;
		grid-template-rows: auto minmax(0, 1fr) auto;
		padding: calc(12px + env(safe-area-inset-top)) 12px calc(12px + env(safe-area-inset-bottom));
		gap: 10px;
		pointer-events: none;
	}

	.topbar {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
		align-items: start;
		gap: 12px;
		pointer-events: auto;
	}

	.topbar__slot {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.topbar__slot--end {
		justify-content: flex-end;
	}

	.dock-slot {
		grid-row: 3;
		display: flex;
		align-items: flex-end;
		pointer-events: none;
	}

	.hud-center {
		display: flex;
		justify-content: center;
		pointer-events: none;
	}

	.ghost {
		border: 1px solid rgba(255, 255, 255, 0.42);
		border-radius: var(--radius-pill);
		background: rgba(16, 24, 20, 0.42);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		color: #fff;
		font-size: 13px;
		font-weight: 700;
		padding: 10px 14px;
		display: inline-flex;
		align-items: center;
		gap: 8px;
		cursor: pointer;
		transition: background 120ms var(--ease);
		min-height: 44px;
	}

	.ghost:hover {
		background: rgba(16, 24, 20, 0.58);
	}

	.ghost:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.ghost-label {
		display: none;
	}

	@media (min-width: 1024px) {
		.ghost-label {
			display: inline;
		}
	}

	@media (min-width: 1024px) {
		.shell {
			padding: 16px;
			padding-top: calc(16px + env(safe-area-inset-top));
			padding-bottom: calc(16px + env(safe-area-inset-bottom));
			grid-template-columns: 1fr 360px;
			grid-template-rows: auto minmax(0, 1fr);
			align-items: end;
		}

		.topbar {
			grid-column: 1 / -1;
			grid-row: 1;
		}

		.dock-slot {
			grid-column: 2;
			grid-row: 2;
		}
	}
</style>
