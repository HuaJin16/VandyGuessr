<script lang="ts">
import InviteCodeCard from "$lib/domains/multiplayer/components/InviteCodeCard.svelte";
import LobbyPlayerList from "$lib/domains/multiplayer/components/LobbyPlayerList.svelte";
import { multiplayerQueries } from "$lib/domains/multiplayer/queries/multiplayer.queries";
import { lobbyStore } from "$lib/domains/multiplayer/stores/lobby.store";
import {
	ClientEvent,
	type ConnectionState,
	type MultiplayerPlayer,
	ServerEvent,
	type ServerMessage,
} from "$lib/domains/multiplayer/types";
import { createMultiplayerWs } from "$lib/domains/multiplayer/ws/multiplayer.ws";
import { auth } from "$lib/shared/auth/auth.store";
import { createQuery } from "@tanstack/svelte-query";
import { onDestroy } from "svelte";
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
	lobbyStore.setGame($gameQuery.data);
}

$: game = $lobbyStore.game;
$: players = $lobbyStore.players;
$: lobbyStatus = $lobbyStore.status;

$: if (game?.status === "active") {
	navigate(`/multiplayer/${id}`, { replace: true });
}

$: if (game && (game.status === "cancelled" || game.status === "abandoned")) {
	lobbyStore.setCancelled();
}

function handleMessage(msg: ServerMessage) {
	switch (msg.type) {
		case ServerEvent.PlayerJoined: {
			const data = msg as unknown as {
				player: { userId: string; name: string; avatarUrl: string | null };
				playerCount: number;
			};
			lobbyStore.addPlayer({
				userId: data.player.userId,
				name: data.player.name,
				avatarUrl: data.player.avatarUrl,
				totalScore: 0,
				status: "connected",
				joinedAt: new Date().toISOString(),
			} as MultiplayerPlayer);
			break;
		}
		case ServerEvent.PlayerLeft: {
			const data = msg as unknown as { userId: string };
			lobbyStore.removePlayer(data.userId);
			break;
		}
		case ServerEvent.PlayerDisconnected: {
			const data = msg as unknown as { userId: string };
			lobbyStore.updatePlayerStatus(data.userId, "disconnected");
			break;
		}
		case ServerEvent.PlayerReconnected: {
			const data = msg as unknown as { userId: string };
			lobbyStore.updatePlayerStatus(data.userId, "connected");
			break;
		}
		case ServerEvent.GameStarting: {
			const data = msg as unknown as { countdown: number };
			lobbyStore.setCountdown(data.countdown);
			runCountdown(data.countdown);
			break;
		}
		case ServerEvent.GameCancelled: {
			const data = msg as unknown as { reason: string };
			lobbyStore.setCancelled();
			toast.error(`Game cancelled: ${data.reason}`);
			setTimeout(() => navigate("/", { replace: true }), 2000);
			break;
		}
		case ServerEvent.GameState: {
			const data = msg as unknown as {
				status: "waiting" | "active" | "completed" | "cancelled" | "abandoned";
				players: Array<{
					userId: string;
					name: string;
					status: MultiplayerPlayer["status"];
					totalScore: number;
				}>;
			};

			if (data.status === "active") {
				navigate(`/multiplayer/${id}`, { replace: true });
				break;
			}

			if (data.status === "cancelled" || data.status === "abandoned") {
				lobbyStore.setCancelled();
				break;
			}

			lobbyStore.setPlayers(
				data.players.map((player) => {
					const existing = players.find((p) => p.userId === player.userId);
					return {
						userId: player.userId,
						name: player.name,
						avatarUrl: existing?.avatarUrl ?? null,
						totalScore: player.totalScore,
						status: player.status,
						joinedAt: existing?.joinedAt ?? new Date().toISOString(),
					};
				}),
			);
			break;
		}
		case ServerEvent.LobbyExpiring: {
			lobbyExpiring = true;
			toast.info("Lobby is about to expire. Extend or start the game.");
			break;
		}
		case ServerEvent.RoundStart: {
			navigate(`/multiplayer/${id}`, { replace: true });
			break;
		}
		case ServerEvent.Error: {
			const data = msg as unknown as { message: string };
			toast.error(data.message);
			break;
		}
		case ServerEvent.TokenExpiring: {
			ws?.refreshToken();
			break;
		}
		default:
			break;
	}
}

let ws: ReturnType<typeof createMultiplayerWs> | null = null;
let connectionState: ConnectionState = "connecting";

$: if ($auth.isInitialized && $gameQuery.data) {
	if (!ws) {
		ws = createMultiplayerWs({
			gameId: id,
			onMessage: handleMessage,
			onConnectionChange: (state) => {
				connectionState = state;
			},
		});
	}
}

let countdownValue: number | null = null;
let countdownInterval: ReturnType<typeof setInterval> | null = null;
let lobbyExpiring = false;

function runCountdown(from: number) {
	if (countdownInterval) {
		clearInterval(countdownInterval);
		countdownInterval = null;
	}

	countdownValue = from;
	countdownInterval = setInterval(() => {
		if (countdownValue === null || countdownValue <= 1) {
			if (countdownInterval) {
				clearInterval(countdownInterval);
				countdownInterval = null;
			}
			countdownValue = null;
			return;
		}
		countdownValue--;
	}, 1000);
}

function startGame() {
	if (!ws?.send({ type: ClientEvent.StartGame })) {
		toast.error("Not connected. Try reconnecting.");
	}
}

function extendLobby() {
	if (!ws?.send({ type: ClientEvent.ExtendLobby })) {
		toast.error("Not connected. Try reconnecting.");
	}
}

function leaveLobby() {
	ws?.send({ type: ClientEvent.LeaveLobby });
	ws?.close();
	navigate("/", { replace: true });
}

function reconnect() {
	ws?.reconnect();
}

$: isHost = game?.hostId === $auth.account?.localAccountId;

onDestroy(() => {
	if (countdownInterval) {
		clearInterval(countdownInterval);
		countdownInterval = null;
	}
	ws?.close();
	ws = null;
	lobbyStore.reset();
});
</script>

<div class="lobby-screen">
	{#if $gameQuery.isLoading}
		<div class="loading-spinner" />
	{:else if $gameQuery.isError}
		<div class="error-container">
			<p class="error-text">Failed to load game</p>
			<button class="btn-3d" on:click={() => navigate("/", { replace: true })}>Go Home</button>
		</div>
	{:else if game && lobbyStatus !== "cancelled"}
		<div class="lobby-content glass-card">
			{#if countdownValue !== null}
				<div class="countdown-overlay">
					<span class="countdown-number">{countdownValue}</span>
				</div>
			{:else}
				<h1 class="lobby-title">Multiplayer Lobby</h1>

				<InviteCodeCard code={game.inviteCode} />

				<div class="player-section">
					<h3 class="section-label">Players ({players.length}/5)</h3>
					<LobbyPlayerList {players} hostId={game.hostId} />
				</div>

				<div class="lobby-actions">
					{#if connectionState === "disconnected"}
						<button class="extend-btn" on:click={reconnect}>Reconnect</button>
					{/if}

					{#if isHost}
						<button
							class="btn-3d start-btn"
							disabled={players.length < 2}
							on:click={startGame}
						>
							{players.length < 2
								? "Waiting for players..."
								: `Start Game (${players.length} players)`}
						</button>
					{#if lobbyExpiring}
						<button class="extend-btn" on:click={extendLobby}>
							Extend Lobby
						</button>
					{/if}
					{:else}
						<p class="waiting-text">Waiting for host to start...</p>
						<button class="leave-btn" on:click={leaveLobby}>
							Leave Lobby
						</button>
					{/if}
				</div>
			{/if}
		</div>
	{:else if lobbyStatus === "cancelled"}
		<div class="error-container">
			<p class="error-text">This game was cancelled</p>
			<button class="btn-3d" on:click={() => navigate("/", { replace: true })}>Go Home</button>
		</div>
	{/if}
</div>

<style>
	.lobby-screen {
		position: fixed;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #f5f2e9;
		padding: 16px;
	}
	.lobby-content {
		width: 100%;
		max-width: 420px;
		padding: 32px 24px;
		display: flex;
		flex-direction: column;
		gap: 24px;
	}
	.lobby-title {
		font-family: "Rubik", sans-serif;
		font-weight: 800;
		font-size: 1.5rem;
		color: #18181b;
		text-align: center;
	}
	.section-label {
		font-family: "Rubik", sans-serif;
		font-weight: 600;
		font-size: 0.8125rem;
		color: #636363;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 10px;
	}
	.lobby-actions {
		display: flex;
		flex-direction: column;
		gap: 10px;
		align-items: center;
	}
	.start-btn {
		width: 100%;
		text-align: center;
	}
	.start-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
		box-shadow: 0 6px 0 #236e2d;
	}
	.extend-btn, .leave-btn {
		background: none;
		border: none;
		font-family: "Rubik", sans-serif;
		font-weight: 500;
		font-size: 0.875rem;
		color: #636363;
		cursor: pointer;
		padding: 4px 8px;
	}
	.extend-btn:hover, .leave-btn:hover {
		color: #18181b;
	}
	.leave-btn {
		color: #d95d39;
	}
	.leave-btn:hover {
		color: #b84a2f;
	}
	.waiting-text {
		font-size: 0.875rem;
		color: #636363;
	}
	.countdown-overlay {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 200px;
	}
	.countdown-number {
		font-family: "Rubik Mono One", monospace;
		font-size: 5rem;
		color: #2e933c;
		animation: pop 1s ease-in-out infinite;
	}
	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 4px solid rgba(24, 24, 27, 0.1);
		border-top-color: #2e933c;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	.error-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 16px;
	}
	.error-text {
		font-size: 16px;
		font-weight: 500;
		color: rgba(24, 24, 27, 0.6);
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}
	@keyframes pop {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.15); }
	}
</style>
