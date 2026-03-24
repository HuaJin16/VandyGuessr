<script lang="ts">
import MapAssembly from "$lib/domains/games/components/MapAssembly.svelte";
import PanoramaViewer from "$lib/domains/games/components/PanoramaViewer.svelte";
import MultiplayerHud from "$lib/domains/multiplayer/components/MultiplayerHud.svelte";
import MultiplayerResultsView from "$lib/domains/multiplayer/components/MultiplayerResultsView.svelte";
import MultiplayerSummary from "$lib/domains/multiplayer/components/MultiplayerSummary.svelte";
import { multiplayerQueries } from "$lib/domains/multiplayer/queries/multiplayer.queries";
import { multiplayerStore, timeRemaining } from "$lib/domains/multiplayer/stores/multiplayer.store";
import {
	ClientEvent,
	type GameOverRound,
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

let hydratedFromQuery = false;

$: if ($gameQuery.data && !hydratedFromQuery) {
	hydratedFromQuery = true;
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
let finalRounds: GameOverRound[] = [];
let timerInterval: ReturnType<typeof setInterval> | null = null;
let displayTime: number | null = null;
let showForfeitDialog = false;
let readySent = false;
let disconnectedPlayers: Array<{ userId: string; name: string; timer: number }> = [];

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
			readySent = false;
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
					distanceMeters: number | null;
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
				rounds: GameOverRound[];
			};
			stopTimerTick();
			winnerId = data.winnerId;
			finalStandings = data.standings;
			finalRounds = data.rounds ?? [];
			multiplayerStore.setGameOver(data.standings, finalRounds);
			break;
		}
		case ServerEvent.PlayerDisconnected: {
			const data = msg as unknown as { userId: string };
			const player = $multiplayerStore.game?.players.find((p) => p.userId === data.userId);
			if (player) {
				disconnectedPlayers = [
					...disconnectedPlayers.filter((p) => p.userId !== data.userId),
					{ userId: data.userId, name: player.name, timer: 30 },
				];
				startDisconnectCountdown(data.userId);
			}
			multiplayerStore.updatePlayerStatus(data.userId, "disconnected");
			break;
		}
		case ServerEvent.PlayerReconnected: {
			const data = msg as unknown as { userId: string };
			disconnectedPlayers = disconnectedPlayers.filter((p) => p.userId !== data.userId);
			multiplayerStore.updatePlayerStatus(data.userId, "connected");
			break;
		}
		case ServerEvent.PlayerForfeited: {
			const data = msg as unknown as { userId: string };
			disconnectedPlayers = disconnectedPlayers.filter((p) => p.userId !== data.userId);
			multiplayerStore.updatePlayerStatus(data.userId, "forfeited");
			if (data.userId === currentUserId) {
				setTimeout(() => navigate("/", { replace: true }), 1200);
			}
			break;
		}
		case ServerEvent.GameState: {
			const data = msg as unknown as {
				status: "waiting" | "active" | "completed" | "cancelled" | "abandoned";
				currentRound: number;
				round: { round: number; imageUrl: string; expiresAt: string | null } | null;
				playersGuessed: string[];
				hasGuessedThisRound: boolean;
				players: Array<{
					userId: string;
					name: string;
					status: "connected" | "disconnected" | "forfeited";
					totalScore: number;
				}>;
			};
			if (data.status === "cancelled" || data.status === "abandoned") {
				toast.error("Game is no longer active");
				setTimeout(() => navigate("/", { replace: true }), 1200);
				break;
			}

			multiplayerStore.applyGameState(data);
			if (data.round?.expiresAt) {
				startTimerTick();
			} else {
				stopTimerTick();
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
			multiplayerStore.setSubmitting(false);
			toast.error(data.message);
			break;
		}
		default:
			break;
	}
}

let disconnectIntervals: Record<string, ReturnType<typeof setInterval>> = {};

function startDisconnectCountdown(userId: string) {
	if (disconnectIntervals[userId]) clearInterval(disconnectIntervals[userId]);
	disconnectIntervals[userId] = setInterval(() => {
		disconnectedPlayers = disconnectedPlayers.map((p) =>
			p.userId === userId ? { ...p, timer: Math.max(0, p.timer - 1) } : p,
		);
		const found = disconnectedPlayers.find((p) => p.userId === userId);
		if (!found || found.timer <= 0) {
			clearInterval(disconnectIntervals[userId]);
			delete disconnectIntervals[userId];
		}
	}, 1000);
}

function dismissDisconnectToast(userId: string) {
	disconnectedPlayers = disconnectedPlayers.filter((p) => p.userId !== userId);
	if (disconnectIntervals[userId]) {
		clearInterval(disconnectIntervals[userId]);
		delete disconnectIntervals[userId];
	}
}

let ws: ReturnType<typeof createMultiplayerWs> | null = null;

$: if ($auth.isInitialized && $gameQuery.data) {
	if (!ws) {
		ws = createMultiplayerWs({
			gameId: id,
			onMessage: handleMessage,
			onConnectionChange: (state) => {
				multiplayerStore.setConnection(state);
				if (state === "disconnected") {
					multiplayerStore.setSubmitting(false);
				}
			},
		});
	}
}

function reconnect() {
	ws?.reconnect();
}

function handleMapClick(pos: { lat: number; lng: number }) {
	multiplayerStore.setGuessPosition(pos);
}

function submitGuess() {
	if (!guessPosition || hasGuessed || submitting) return;
	const sent = ws?.send({
		type: ClientEvent.SubmitGuess,
		lat: guessPosition.lat,
		lng: guessPosition.lng,
	});
	if (!sent) {
		toast.error("Connection lost. Reconnect to submit your guess.");
		return;
	}
	multiplayerStore.setSubmitting(true);
}

function handleTimerExpiry() {
	if (guessPosition && !hasGuessed) {
		submitGuess();
	}
}

function sendReadyNext() {
	if (readySent) return;
	ws?.send({ type: ClientEvent.ReadyNext });
	readySent = true;
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
$: totalPlayers =
	$multiplayerStore.game?.players.filter((player) => player.status !== "forfeited").length ?? 0;

$: currentUserScore = (() => {
	const player = $multiplayerStore.game?.players.find((p) => p.userId === currentUserId);
	return player?.totalScore ?? 0;
})();

$: currentUserRank = (() => {
	const myStanding = standings.find((s) => s.userId === currentUserId);
	return myStanding?.rank ?? 0;
})();

function ordinal(n: number): string {
	const s = ["th", "st", "nd", "rd"];
	const v = n % 100;
	return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

onMount(() => {
	return () => {
		stopTimerTick();
	};
});

onDestroy(() => {
	stopTimerTick();
	for (const key of Object.keys(disconnectIntervals)) {
		clearInterval(disconnectIntervals[key]);
	}
	ws?.close();
	ws = null;
	multiplayerStore.reset();
});
</script>

{#if $gameQuery.isLoading}
	<div class="fixed inset-0 flex flex-col items-center justify-center gap-4 bg-canvas p-4">
		<div class="loading-spinner" />
	</div>
{:else if $gameQuery.isError}
	<div class="fixed inset-0 flex flex-col items-center justify-center gap-4 bg-canvas p-4">
		<p class="text-base font-medium text-muted">Failed to load game</p>
		<button class="btn-3d" on:click={goHome}>Go Home</button>
	</div>
{:else if phase === "game_over"}
	<MultiplayerSummary
		standings={finalStandings}
		rounds={finalRounds}
		{winnerId}
		{currentUserId}
		on:home={goHome}
	/>
{:else if phase === "results" && roundResult}
	<MultiplayerResultsView result={roundResult} {currentUserId} {readySent} on:readyNext={sendReadyNext} />
{:else if phase === "playing" && imageUrl}
	<div class="scene">
		<PanoramaViewer imageUrl={imageUrl} />
	</div>

	<!-- Disconnect toasts -->
	{#each disconnectedPlayers as dp (dp.userId)}
		<div class="toast-disconnect">
			<div class="toast-dot" />
			<span class="toast-text"><strong>{dp.name}</strong> disconnected</span>
			<span class="toast-time">{dp.timer}s</span>
			<button class="toast-close" on:click={() => dismissDisconnectToast(dp.userId)}>✕</button>
		</div>
	{/each}

	<main class="shell">
		<div class="topbar">
			<button class="ghost ghost-danger" on:click={() => (showForfeitDialog = true)}>
				<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
					<line x1="4" y1="22" x2="4" y2="15" />
				</svg>
				Forfeit
			</button>
			<div class="hud-center">
				<MultiplayerHud
					{currentRound}
					totalRounds={5}
					timeRemaining={displayTime}
					totalScore={currentUserScore}
					{hasGuessed}
					playersGuessedCount={$multiplayerStore.playersGuessed.length}
					{totalPlayers}
				/>
			</div>
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
				<div class="waiting-dot" />
				<p class="m-0 text-sm font-medium text-muted">Waiting for other players…</p>
			</div>
		{/if}

		{#if $multiplayerStore.connection === "disconnected"}
			<div class="reconnect-bar">
				<span class="text-sm font-medium text-white/80">Connection lost</span>
				<button class="ghost" on:click={reconnect}>Reconnect</button>
			</div>
		{/if}
	</main>

	<!-- Forfeit Dialog -->
	{#if showForfeitDialog}
		<div class="overlay">
			<button class="overlay-bg" on:click={() => (showForfeitDialog = false)} aria-label="Close dialog" />
			<div class="dialog">
				<div class="dialog-icon">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
						<line x1="4" y1="22" x2="4" y2="15" />
					</svg>
				</div>
				<h2 class="m-0 text-center text-xl font-extrabold text-ink">Forfeit Game?</h2>
				<p class="mt-2 mb-0 text-center text-sm leading-relaxed text-muted">Your opponents will continue without you. Remaining rounds score 0.</p>

				<div class="dialog-stats">
					<div class="text-center">
						<p class="dialog-stat-label">Rounds</p>
						<p class="dialog-stat-value">{currentRound}/5</p>
					</div>
					<div class="text-center">
						<p class="dialog-stat-label">Score</p>
						<p class="dialog-stat-value" style="color: var(--brand);">{currentUserScore.toLocaleString()}</p>
					</div>
					<div class="text-center">
						<p class="dialog-stat-label">Rank</p>
						<p class="dialog-stat-value">{ordinal(currentUserRank)}</p>
					</div>
				</div>

				<div class="dialog-warning">
					<svg class="dialog-warning-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
						<line x1="12" y1="9" x2="12" y2="13" />
						<line x1="12" y1="17" x2="12.01" y2="17" />
					</svg>
					<span><strong style="color: var(--danger-ink);">Forfeiting is permanent.</strong> Your final score will still appear on the leaderboard.</span>
				</div>

				<div class="dialog-actions">
					<button class="btn-cancel" on:click={() => (showForfeitDialog = false)}>Cancel</button>
					<button class="btn-forfeit" on:click={forfeit}>
						<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
							<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
							<line x1="4" y1="22" x2="4" y2="15" />
						</svg>
						Forfeit
					</button>
				</div>
			</div>
		</div>
	{/if}
{:else}
	<div class="fixed inset-0 flex flex-col items-center justify-center gap-4 bg-canvas p-4">
		<div class="loading-spinner" />
		<p class="text-sm font-medium text-muted">Waiting for round to start…</p>
		{#if $multiplayerStore.connection === "disconnected"}
			<button class="btn-3d" on:click={reconnect}>Reconnect</button>
		{/if}
	</div>
{/if}

<style>
	.scene {
		position: fixed;
		inset: 0;
		background: #0f1712;
	}

	.shell {
		position: relative;
		z-index: 2;
		min-height: 100vh;
		display: grid;
		grid-template-rows: auto 1fr;
		padding: 10px;
		gap: 6px;
		pointer-events: none;
	}

	.topbar {
		display: flex;
		align-items: center;
		gap: 8px;
		pointer-events: auto;
	}

	.hud-center {
		flex: 1;
		display: flex;
		justify-content: center;
		pointer-events: none;
	}

	.ghost {
		border: 1px solid rgba(255, 255, 255, 0.55);
		border-radius: var(--radius-md);
		background: rgba(17, 25, 20, 0.4);
		backdrop-filter: blur(4px);
		color: #fff;
		font-family: Inter, sans-serif;
		font-size: 13px;
		font-weight: 600;
		padding: 8px 11px;
		display: inline-flex;
		align-items: center;
		gap: 6px;
		cursor: pointer;
		transition: all 120ms var(--ease);
		text-decoration: none;
	}

	.ghost:hover { background: rgba(17, 25, 20, 0.55); }
	.ghost:focus-visible { outline: none; box-shadow: var(--ring); }

	.ghost-danger {
		border-color: rgba(220, 74, 58, 0.5);
		color: rgba(255, 255, 255, 0.85);
	}

	.ghost-danger:hover {
		background: rgba(220, 74, 58, 0.2);
		border-color: rgba(220, 74, 58, 0.7);
	}

	/* Waiting chip after guess */
	.waiting-chip {
		align-self: end;
		pointer-events: auto;
		display: flex;
		align-items: center;
		gap: 10px;
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(6px);
		border: 1px solid rgba(255, 255, 255, 0.55);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md);
		padding: 14px 18px;
	}

	.waiting-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--brand);
		animation: pulse 1.5s ease-in-out infinite;
		flex-shrink: 0;
	}

	/* Reconnect bar */
	.reconnect-bar {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		z-index: 30;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		background: rgba(26, 26, 26, 0.92);
		padding: 10px 16px;
		pointer-events: auto;
	}

	/* Disconnect toast */
	.toast-disconnect {
		position: fixed;
		top: 80px;
		left: 50%;
		transform: translateX(-50%);
		z-index: 20;
		display: flex;
		align-items: center;
		gap: 10px;
		background: rgba(26, 26, 26, 0.92);
		border: 1px solid rgba(255, 255, 255, 0.12);
		border-radius: var(--radius-pill);
		padding: 8px 14px 8px 12px;
		box-shadow: var(--shadow-md);
		max-width: calc(100% - 32px);
	}

	.toast-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #f59e0b;
		flex-shrink: 0;
		animation: toastPulse 1.5s ease-in-out infinite;
	}

	.toast-text {
		font-size: 13px;
		font-weight: 500;
		color: rgba(255, 255, 255, 0.85);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		min-width: 0;
	}

	.toast-text :global(strong) {
		font-weight: 700;
		color: #fff;
	}

	.toast-time {
		font-family: "IBM Plex Mono", monospace;
		font-size: 12px;
		font-weight: 600;
		color: #f59e0b;
	}

	.toast-close {
		border: none;
		background: none;
		color: rgba(255, 255, 255, 0.4);
		font-size: 16px;
		cursor: pointer;
		padding: 0 2px;
		line-height: 1;
	}

	.toast-close:hover { color: rgba(255, 255, 255, 0.7); }

	@keyframes toastPulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.4; }
	}

	/* Forfeit dialog */
	.overlay {
		position: fixed;
		inset: 0;
		z-index: 50;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 16px;
	}

	.overlay-bg {
		position: absolute;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		border: none;
		cursor: default;
	}

	.dialog {
		position: relative;
		width: 100%;
		max-width: 420px;
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-lg);
		padding: 24px;
		color: var(--ink);
	}

	.dialog-icon {
		width: 48px;
		height: 48px;
		border-radius: 50%;
		background: var(--danger-light);
		display: grid;
		place-items: center;
		margin: 0 auto 14px;
	}

	.dialog-stats {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr;
		gap: 8px;
		margin: 18px 0;
		background: #faf9f6;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		padding: 14px;
	}

	.dialog-stat-label {
		margin: 0;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.dialog-stat-value {
		margin: 4px 0 0;
		font-family: "IBM Plex Mono", monospace;
		font-size: 18px;
		font-weight: 600;
	}

	.dialog-warning {
		display: flex;
		align-items: flex-start;
		gap: 10px;
		background: var(--danger-light);
		border: 1px solid rgba(220, 74, 58, 0.2);
		border-radius: var(--radius-md);
		padding: 12px 14px;
		margin-bottom: 18px;
		font-size: 13px;
		line-height: 1.45;
		color: var(--danger-ink);
	}

	.dialog-warning-icon {
		flex-shrink: 0;
		width: 16px;
		height: 16px;
		margin-top: 1px;
	}

	.dialog-actions {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px;
	}

	.btn-cancel {
		border: 2px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
		color: var(--ink);
		font-family: Inter, sans-serif;
		font-size: 14px;
		font-weight: 700;
		padding: 11px 14px;
		cursor: pointer;
		transition: all 120ms var(--ease);
	}

	.btn-cancel:hover { background: rgba(0, 0, 0, 0.04); }

	.btn-forfeit {
		border: none;
		border-radius: var(--radius-md);
		background: var(--danger);
		color: #fff;
		font-family: Inter, sans-serif;
		font-size: 14px;
		font-weight: 700;
		padding: 11px 14px;
		box-shadow: 0 4px 0 var(--danger-dark);
		cursor: pointer;
		transition: all 120ms var(--ease);
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
	}

	.btn-forfeit:hover { background: #c94031; }
	.btn-forfeit:active { transform: translateY(4px); box-shadow: 0 0 0 var(--danger-dark); }

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 4px solid rgba(24, 24, 27, 0.1);
		border-top-color: var(--brand);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.4; }
	}

	@media (max-width: 400px) {
		.ghost { font-size: 12px; padding: 7px 9px; }
		.dialog { padding: 18px; }
		.dialog-stats { grid-template-columns: 1fr; gap: 6px; padding: 10px; }
		.dialog-stat-value { font-size: 15px; }
		.dialog-actions { grid-template-columns: 1fr; }
	}

	@media (min-width: 880px) {
		.shell {
			padding: 14px;
			gap: 6px;
			grid-template-rows: auto 1fr;
			grid-template-columns: 1fr 360px;
			align-items: end;
		}

		.topbar {
			grid-column: 1 / -1;
			grid-row: 1;
			align-items: start;
		}

		.waiting-chip {
			grid-column: 2;
			grid-row: 2;
		}
	}
</style>
