<script lang="ts">
import MapAssembly from "$lib/domains/games/components/MapAssembly.svelte";
import MultiplayerHud from "$lib/domains/multiplayer/components/MultiplayerHud.svelte";
import MultiplayerResultsView from "$lib/domains/multiplayer/components/MultiplayerResultsView.svelte";
import MultiplayerSummary from "$lib/domains/multiplayer/components/MultiplayerSummary.svelte";
import { multiplayerQueries } from "$lib/domains/multiplayer/queries/multiplayer.queries";
import { multiplayerStore, timeRemaining } from "$lib/domains/multiplayer/stores/multiplayer.store";
import {
	ClientEvent,
	ServerEvent,
	type ServerMessage,
	type Standing,
} from "$lib/domains/multiplayer/types";
import { createMultiplayerWs } from "$lib/domains/multiplayer/ws/multiplayer.ws";
import { auth } from "$lib/shared/auth/auth.store";
import { createQuery } from "@tanstack/svelte-query";
import { onDestroy, onMount } from "svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

export let id: string;

$: gameQuery = createQuery({
	...multiplayerQueries.byId(id),
	enabled: $auth.isInitialized,
});

$: if ($gameQuery.data) {
	multiplayerStore.setGame($gameQuery.data);
}

$: phase = $multiplayerStore.phase;
$: currentRound = $multiplayerStore.currentRound;
$: imageUrl = $multiplayerStore.imageUrl;
$: hasGuessed = $multiplayerStore.hasGuessedThisRound;
$: guessPosition = $multiplayerStore.guessPosition;
$: roundResult = $multiplayerStore.roundResult;
$: standings = $multiplayerStore.standings;
$: submitting = $multiplayerStore.submitting;
$: remaining = $timeRemaining;

let winnerId = "";
let finalStandings: Standing[] = [];
let timerInterval: ReturnType<typeof setInterval> | null = null;
let displayTime: number | null = null;

function startTimerTick() {
	stopTimerTick();
	displayTime = remaining;
	timerInterval = setInterval(() => {
		if ($multiplayerStore.expiresAt) {
			const ms = Math.max(0, new Date($multiplayerStore.expiresAt).getTime() - Date.now());
			displayTime = Math.ceil(ms / 1000);
			if (displayTime <= 0) {
				stopTimerTick();
				handleTimerExpiry();
			}
		}
	}, 250);
}

function stopTimerTick() {
	if (timerInterval) {
		clearInterval(timerInterval);
		timerInterval = null;
	}
}

function handleMessage(msg: ServerMessage) {
	switch (msg.type) {
		case ServerEvent.RoundStart: {
			const data = msg as unknown as {
				round: number;
				imageUrl: string;
				expiresAt: string;
			};
			multiplayerStore.startRound(data.round, data.imageUrl, data.expiresAt);
			startTimerTick();
			break;
		}
		case ServerEvent.GuessAccepted: {
			multiplayerStore.markGuessAccepted();
			break;
		}
		case ServerEvent.PlayerGuessed: {
			const data = msg as unknown as { userId: string };
			multiplayerStore.addPlayerGuessed(data.userId);
			break;
		}
		case ServerEvent.RoundResult: {
			const data = msg as unknown as {
				round: number;
				results: Array<{
					userId: string;
					name: string;
					score: number;
					distanceMeters: number;
					guess: { lat: number; lng: number } | null;
				}>;
				actual: { lat: number; lng: number };
				locationName: string | null;
				standings: Standing[];
			};
			stopTimerTick();
			multiplayerStore.setRoundResult({
				round: data.round,
				results: data.results,
				actual: data.actual,
				locationName: data.locationName,
				standings: data.standings,
			});
			break;
		}
		case ServerEvent.GameOver: {
			const data = msg as unknown as {
				winnerId: string;
				standings: Standing[];
			};
			stopTimerTick();
			winnerId = data.winnerId;
			finalStandings = data.standings;
			multiplayerStore.setGameOver(data.standings);
			break;
		}
		case ServerEvent.PlayerDisconnected: {
			const data = msg as unknown as { userId: string };
			toast.info("A player disconnected (30s to reconnect)");
			// Update player status on game object if we have it
			void data;
			break;
		}
		case ServerEvent.PlayerReconnected: {
			toast.info("Player reconnected");
			break;
		}
		case ServerEvent.PlayerForfeited: {
			toast.info("A player has left the game");
			break;
		}
		case ServerEvent.GameState: {
			const data = msg as unknown as {
				currentRound: number;
				round: { round: number; imageUrl: string; expiresAt: string } | null;
				playersGuessed: string[];
				hasGuessedThisRound: boolean;
			};
			multiplayerStore.applyGameState(data);
			if (data.round) {
				startTimerTick();
			}
			break;
		}
		case ServerEvent.GameCancelled: {
			const data = msg as unknown as { reason: string };
			toast.error(`Game cancelled: ${data.reason}`);
			setTimeout(() => navigate("/", { replace: true }), 2000);
			break;
		}
		case ServerEvent.TokenExpiring: {
			ws?.refreshToken();
			break;
		}
		case ServerEvent.Error: {
			const data = msg as unknown as { message: string };
			toast.error(data.message);
			break;
		}
		default:
			break;
	}
}

let ws: ReturnType<typeof createMultiplayerWs> | null = null;

$: if ($auth.isInitialized && $gameQuery.data) {
	if (!ws) {
		ws = createMultiplayerWs({
			gameId: id,
			onMessage: handleMessage,
			onConnectionChange: (state) => multiplayerStore.setConnection(state),
		});
	}
}

function handleMapClick(pos: { lat: number; lng: number }) {
	multiplayerStore.setGuessPosition(pos);
}

function submitGuess() {
	if (!guessPosition || hasGuessed || submitting) return;
	multiplayerStore.setSubmitting(true);
	ws?.send({
		type: ClientEvent.SubmitGuess,
		lat: guessPosition.lat,
		lng: guessPosition.lng,
	});
}

function handleTimerExpiry() {
	if (guessPosition && !hasGuessed) {
		submitGuess();
	}
}

function forfeit() {
	ws?.send({ type: ClientEvent.Forfeit });
	ws?.close();
	navigate("/", { replace: true });
}

function goHome() {
	navigate("/", { replace: true });
}

$: currentUserId = $auth.account?.localAccountId ?? "";
$: totalPlayers = $multiplayerStore.game?.players.length ?? 0;

onMount(() => {
	return () => {
		stopTimerTick();
	};
});

onDestroy(() => {
	stopTimerTick();
	ws?.close();
	ws = null;
	multiplayerStore.reset();
});
</script>

<div class="game-screen">
	{#if $gameQuery.isLoading}
		<div class="center-content">
			<div class="loading-spinner" />
		</div>
	{:else if $gameQuery.isError}
		<div class="center-content">
			<p class="error-text">Failed to load game</p>
			<button class="btn-3d" on:click={goHome}>Go Home</button>
		</div>
	{:else if phase === "game_over"}
		<div class="center-content">
			<MultiplayerSummary
				standings={finalStandings}
				{winnerId}
				{currentUserId}
				on:home={goHome}
			/>
		</div>
	{:else if phase === "results" && roundResult}
		<div class="center-content">
			<MultiplayerResultsView
				result={roundResult}
				totalRounds={5}
				isLastRound={roundResult.round >= 5}
			/>
		</div>
	{:else if phase === "playing" && imageUrl}
		<div class="gameplay-layer">
			<div class="panorama-container">
				<img src={imageUrl} alt="Round {currentRound}" class="panorama-image" />
			</div>

			<div class="hud-layer">
				<MultiplayerHud
					{currentRound}
					totalRounds={5}
					timeRemaining={displayTime}
					{standings}
					{hasGuessed}
					playersGuessedCount={$multiplayerStore.playersGuessed.length}
					{totalPlayers}
				/>
			</div>

			{#if !hasGuessed}
				<MapAssembly
					position={guessPosition}
					disabled={submitting}
					onMapClick={handleMapClick}
					onGuess={submitGuess}
				/>
			{:else}
				<div class="waiting-chip">
					<p class="waiting-text">Waiting for other players...</p>
				</div>
			{/if}

			<button class="forfeit-btn" on:click={forfeit}>Forfeit</button>
		</div>
	{:else}
		<div class="center-content">
			<div class="loading-spinner" />
			<p class="waiting-text">Waiting for round to start...</p>
		</div>
	{/if}
</div>

<style>
	.game-screen {
		position: fixed;
		inset: 0;
		background: #f5f2e9;
	}
	.center-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		gap: 16px;
		padding: 16px;
	}
	.gameplay-layer {
		position: relative;
		width: 100%;
		height: 100%;
	}
	.panorama-container {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #18181b;
		overflow: hidden;
	}
	.panorama-image {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	.hud-layer {
		position: absolute;
		top: 16px;
		left: 50%;
		transform: translateX(-50%);
		z-index: 10;
		pointer-events: none;
	}
	.waiting-chip {
		position: fixed;
		bottom: 20px;
		right: 20px;
		z-index: 40;
		background: rgba(255, 255, 255, 0.9);
		backdrop-filter: blur(8px);
		padding: 12px 24px;
		border-radius: 12px;
	}
	.forfeit-btn {
		position: fixed;
		bottom: 24px;
		left: 20px;
		z-index: 40;
		background: none;
		border: none;
		font-family: "Rubik", sans-serif;
		font-weight: 500;
		font-size: 0.8125rem;
		color: rgba(255, 255, 255, 0.6);
		cursor: pointer;
		padding: 4px 8px;
	}
	.forfeit-btn:hover {
		color: #d95d39;
	}
	.waiting-text {
		font-size: 0.875rem;
		color: #636363;
	}
	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 4px solid rgba(24, 24, 27, 0.1);
		border-top-color: #2e933c;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	.error-text {
		font-size: 16px;
		font-weight: 500;
		color: rgba(24, 24, 27, 0.6);
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}
</style>
