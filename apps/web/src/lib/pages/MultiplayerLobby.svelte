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
import logo from "../../assets/logo.webp";

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
$: readyPlayers = $lobbyStore.readyPlayers;
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
		case ServerEvent.PlayerReady: {
			const data = msg as unknown as { userId: string };
			lobbyStore.setPlayerReady(data.userId);
			break;
		}
		case ServerEvent.PlayerUnready: {
			const data = msg as unknown as { userId: string };
			lobbyStore.setPlayerUnready(data.userId);
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
		case ServerEvent.Kicked: {
			toast.error("You were removed from the lobby by the host");
			ws?.close();
			navigate("/", { replace: true });
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
				readyPlayers: string[];
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
			lobbyStore.setReadyPlayers(data.readyPlayers ?? []);
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

function toggleReady() {
	const eventType = readyPlayers.includes(currentUserId)
		? ClientEvent.Unready
		: ClientEvent.ReadyUp;
	if (!ws?.send({ type: eventType })) {
		toast.error("Not connected. Try reconnecting.");
	}
}

function kickPlayer(userId: string) {
	if (!ws?.send({ type: ClientEvent.Kick, userId })) {
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
$: currentUserId = $auth.account?.localAccountId ?? "";
$: connectedPlayers = players.filter((player) => player.status === "connected");
$: allConnectedReady =
	connectedPlayers.length >= 2 &&
	connectedPlayers.every((player) => readyPlayers.includes(player.userId));

function getInitials(name: string): string {
	return name
		.split(" ")
		.map((w) => w[0])
		.join("")
		.toUpperCase()
		.slice(0, 2);
}

const PLAYER_COLORS = [
	"var(--p-you)",
	"var(--p-blue)",
	"var(--p-purple)",
	"var(--p-orange)",
	"var(--p-cyan)",
	"var(--p-pink)",
];

function getPlayerColor(player: MultiplayerPlayer, index: number): string {
	if (player.userId === currentUserId) return PLAYER_COLORS[0];
	let opponentIdx = 0;
	for (let i = 0; i < players.length; i++) {
		if (players[i].userId === currentUserId) continue;
		if (players[i].userId === player.userId)
			return PLAYER_COLORS[opponentIdx + 1] ?? PLAYER_COLORS[1];
		opponentIdx++;
	}
	return PLAYER_COLORS[(index + 1) % PLAYER_COLORS.length];
}

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

{#if countdownValue !== null}
	<!-- Countdown Overlay -->
	<div class="countdown-backdrop" />
	<div class="countdown-center">
		<div class="count-wrap">
			<div class="ring" />
			<div class="count-circle">
				<span class="count-num">{countdownValue}</span>
			</div>
		</div>

		<div class="countdown-text">
			<h2 class="text-2xl font-extrabold text-white">Game Starting</h2>
			<p class="mt-1.5 text-sm text-white/55">Get ready to guess!</p>
		</div>

		<div class="player-bar">
			<div class="avatar-stack">
				{#each players as player, i (player.userId)}
					<div class="av" style="background: {getPlayerColor(player, i)};">
						{getInitials(player.name)}
					</div>
				{/each}
			</div>
			<span class="font-mono text-[13px] font-semibold text-[var(--ink)]">
				{players.length} player{players.length !== 1 ? "s" : ""}
			</span>
		</div>
	</div>
{:else}
	<!-- Normal Lobby -->
	{#if $gameQuery.isLoading}
		<div class="flex h-screen items-center justify-center bg-canvas">
			<div class="loading-spinner" />
		</div>
	{:else if $gameQuery.isError || lobbyStatus === "cancelled"}
		<div class="flex h-screen flex-col items-center justify-center gap-4 bg-canvas">
			<p class="text-base font-medium text-[var(--muted)]">
				{lobbyStatus === "cancelled" ? "This game was cancelled" : "Failed to load game"}
			</p>
			<button class="btn-3d" on:click={() => navigate("/", { replace: true })}>Go Home</button>
		</div>
	{:else if game}
		<header class="sticky top-0 z-50 border-b border-line bg-surface">
			<div
				class="mx-auto flex min-h-[56px] items-center justify-between gap-3"
				style="width: min(600px, calc(100% - 32px));"
			>
				<a href="/" class="flex items-center gap-2.5">
					<img src={logo} alt="VandyGuessr" class="h-[34px] w-[34px] rounded-md" />
					<span class="text-lg font-extrabold text-ink">VandyGuessr</span>
				</a>
				<div class="status-indicator">
					<div
						class="status-dot"
						class:connected={connectionState === "connected"}
						class:disconnected={connectionState === "disconnected"}
					/>
					<span class="text-[13px] font-medium text-[var(--muted)]">
						{connectionState === "connected" ? "Connected" : connectionState === "disconnected" ? "Disconnected" : "Connecting..."}
					</span>
				</div>
			</div>
		</header>

		<main
			class="mx-auto my-4 grid gap-3.5 sm:mb-6"
			style="width: min(600px, calc(100% - 32px));"
		>
			<InviteCodeCard code={game.inviteCode} />

			{#if isHost}
				<div class="host-banner">
					<svg class="host-crown" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7z" />
						<path d="M3 20h18" />
					</svg>
					<span>You are the host</span>
				</div>
			{:else}
				{@const hostPlayer = players.find(p => p.userId === game.hostId)}
				{#if hostPlayer}
					<div class="host-banner guest">
						<svg class="host-crown" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7z" />
							<path d="M3 20h18" />
						</svg>
						<span>Hosted by <strong>{hostPlayer.name}</strong></span>
					</div>
				{/if}
			{/if}

			<LobbyPlayerList
				{players}
				hostId={game.hostId}
				{currentUserId}
				{readyPlayers}
				showReadyToggle={connectionState !== "disconnected"}
				on:toggleReady={toggleReady}
				on:kick={(event) => kickPlayer(event.detail.userId)}
			/>

			<!-- Settings -->
			<section class="card">
				<p class="mb-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--muted)]">
					Game Settings
				</p>
				<div class="flex flex-wrap gap-2">
					<span class="settings-pill">
						<svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
						</svg>
						120s per round
					</span>
					<span class="settings-pill">
						<svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
						</svg>
						5 rounds
					</span>
					<span class="settings-pill" class:settings-pill-any={game.mode?.environment === "any"}>
						<svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z" />
							<path d="M2 12h20" />
							<path d="M12 2a15.3 15.3 0 0 1 0 20" />
							<path d="M12 2a15.3 15.3 0 0 0 0 20" />
						</svg>
						{game.mode?.environment === "indoor"
							? "Indoor only"
							: game.mode?.environment === "outdoor"
								? "Outdoor only"
								: "All environments"}
					</span>
				</div>
			</section>

			<!-- Actions -->
			<div class="grid gap-1.5">
				{#if connectionState === "disconnected"}
					<button class="btn-3d w-full text-center" on:click={reconnect}>Reconnect</button>
				{:else if isHost}
					<button
						class="btn-3d w-full text-center"
						disabled={!allConnectedReady}
						on:click={startGame}
					>
						{#if connectedPlayers.length < 2}
							Waiting for players...
						{:else if !allConnectedReady}
							Waiting for ready checks...
						{:else}
							Start Game
						{/if}
					</button>
					{#if connectedPlayers.length >= 2 && !allConnectedReady}
						<p class="py-1 text-center text-xs font-medium text-[var(--muted)]">
							{connectedPlayers.filter((player) => readyPlayers.includes(player.userId)).length}/{connectedPlayers.length} ready
						</p>
					{/if}
					{#if lobbyExpiring}
						<button class="leave-btn" on:click={extendLobby}>Extend Lobby</button>
					{/if}
				{:else}
					<p class="py-2 text-center text-sm text-[var(--muted)]">Waiting for host to start...</p>
				{/if}
				<button class="leave-btn" on:click={leaveLobby}>Leave Lobby</button>
			</div>
		</main>
	{/if}
{/if}

<style>
	.status-indicator {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--muted);
	}

	.status-dot.connected {
		background: var(--brand);
		animation: pulse 2s ease-in-out infinite;
	}

	.status-dot.disconnected {
		background: var(--danger);
	}

	.host-banner {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		padding: 10px 16px;
		border-radius: var(--radius-md);
		background: var(--gold-light);
		border: 1px solid var(--gold);
		color: var(--gold-ink);
		font-size: 13px;
		font-weight: 600;
	}

	.host-banner.guest {
		background: var(--surface);
		border-color: var(--line);
		color: var(--muted);
	}

	.host-crown {
		width: 16px;
		height: 16px;
		flex-shrink: 0;
	}

	.settings-pill {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		font-size: 12px;
		font-weight: 600;
		padding: 6px 12px;
		border-radius: var(--radius-pill);
		background: #f0ede6;
		color: var(--muted);
	}

	.settings-pill-any {
		background: color-mix(in srgb, var(--brand-light) 55%, #f0ede6);
		color: color-mix(in srgb, var(--brand-dark) 75%, var(--muted));
	}

	.leave-btn {
		width: 100%;
		border: none;
		border-radius: var(--radius-md);
		background: transparent;
		color: var(--muted);
		font-size: 14px;
		font-weight: 600;
		padding: 10px 14px;
		cursor: pointer;
		transition: all 120ms var(--ease);
	}

	.leave-btn:hover {
		color: var(--danger);
		background: var(--danger-light);
	}

	.btn-3d:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
	}

	.btn-3d:disabled:active {
		transform: none;
		box-shadow: 0 4px 0 var(--brand-dark);
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 4px solid rgba(24, 24, 27, 0.1);
		border-top-color: var(--brand);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	/* Countdown overlay styles */
	.countdown-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(26, 26, 26, 0.65);
		z-index: 100;
	}

	.countdown-center {
		position: fixed;
		inset: 0;
		z-index: 101;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 24px;
	}

	.count-wrap {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.ring {
		position: absolute;
		width: 140px;
		height: 140px;
		border-radius: 50%;
		border: 3px solid rgba(59, 130, 246, 0.25);
		animation: ringExpand 1.2s ease-out infinite;
	}

	.count-circle {
		width: 140px;
		height: 140px;
		border-radius: 50%;
		background: var(--brand);
		box-shadow: var(--shadow-lg);
		display: grid;
		place-items: center;
		animation: countPop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
	}

	.count-num {
		font-family: "IBM Plex Mono", monospace;
		font-size: 72px;
		font-weight: 600;
		color: #fff;
		line-height: 1;
	}

	.countdown-text {
		text-align: center;
		animation: fadeUp 0.4s ease-out 0.2s both;
	}

	.player-bar {
		display: inline-flex;
		align-items: center;
		gap: 14px;
		background: rgba(255, 255, 255, 0.93);
		border: 1px solid var(--line);
		border-radius: var(--radius-pill);
		padding: 8px 16px 8px 8px;
		box-shadow: var(--shadow-md);
		animation: fadeUp 0.4s ease-out 0.35s both;
	}

	.avatar-stack {
		display: flex;
	}

	.avatar-stack .av {
		width: 32px;
		height: 32px;
		border-radius: 50%;
		color: #fff;
		font-size: 11px;
		font-weight: 700;
		display: grid;
		place-items: center;
		border: 2px solid #fff;
		margin-left: -8px;
	}

	.avatar-stack .av:first-child {
		margin-left: 0;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.4; }
	}

	@keyframes ringExpand {
		0% { transform: scale(0.6); opacity: 0.6; }
		100% { transform: scale(2.2); opacity: 0; }
	}

	@keyframes countPop {
		0% { transform: scale(0.3); opacity: 0; }
		60% { transform: scale(1.12); opacity: 1; }
		100% { transform: scale(1); }
	}

	@keyframes fadeUp {
		0% { transform: translateY(10px); opacity: 0; }
		100% { transform: translateY(0); opacity: 1; }
	}
</style>
