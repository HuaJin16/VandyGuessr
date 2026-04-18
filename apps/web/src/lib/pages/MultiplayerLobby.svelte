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
import Navbar from "$lib/shared/components/Navbar.svelte";
import Button from "$lib/shared/ui/Button.svelte";
import Card from "$lib/shared/ui/Card.svelte";
import PageHeader from "$lib/shared/ui/PageHeader.svelte";
import PageShell from "$lib/shared/ui/PageShell.svelte";
import Spinner from "$lib/shared/ui/Spinner.svelte";
import { createQuery } from "@tanstack/svelte-query";
import { onDestroy } from "svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

export let id: string;

$: gameQuery = createQuery({
	...multiplayerQueries.byId(id, $auth.currentUserOid),
	enabled: $auth.currentUserOid !== null,
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
					const existing = players.find((candidate) => candidate.userId === player.userId);
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

$: if ($auth.currentUserOid !== null && $gameQuery.data) {
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
		countdownValue -= 1;
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

$: currentUserId = $auth.currentUserOid ?? "";
$: isHost = game?.hostId === currentUserId;
$: connectedPlayers = players.filter((player) => player.status === "connected");
$: allConnectedReady =
	connectedPlayers.length >= 2 &&
	connectedPlayers.every((player) => readyPlayers.includes(player.userId));

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
	<div class="countdown-backdrop" />
	<div class="countdown-center">
		<div class="count-wrap">
			<div class="ring" />
			<div class="count-circle">
				<span class="count-num">{countdownValue}</span>
			</div>
		</div>

		<div class="countdown-text">
			<h2>Match starting</h2>
			<p>Get ready to place your pin.</p>
		</div>
	</div>
{:else if $gameQuery.isLoading}
	<div class="state-screen">
		<Spinner />
	</div>
{:else if $gameQuery.isError || lobbyStatus === "cancelled"}
	<div class="state-screen state-screen--stacked">
		<p class="state-copy">{lobbyStatus === "cancelled" ? "This lobby was cancelled" : "Failed to load lobby"}</p>
		<Button on:click={() => navigate("/", { replace: true })}>Go Home</Button>
	</div>
{:else if game}
	<div class="min-h-screen bg-canvas font-sans text-ink">
		<Navbar />

		<PageShell size="content">
			<PageHeader
				eyebrow="Multiplayer"
				title="Match lobby"
				copy="Get everyone into the room, ready the roster, and start the match once the connected players are set."
				split
			>
				<div slot="actions" class="lobby-actions-top">
					<div class="status-indicator">
						<div class="status-dot" class:connected={connectionState === "connected"} class:disconnected={connectionState === "disconnected"} />
						<span>
							{connectionState === "connected" ? "Connected" : connectionState === "disconnected" ? "Disconnected" : "Connecting..."}
						</span>
					</div>
				</div>
			</PageHeader>

			<div class="lobby-grid">
				<Card class="lobby-left">
					<InviteCodeCard code={game.inviteCode} />

					<Card tone="subtle" class="host-card">
						<p class="section-label">Host status</p>
						<p class="host-card__copy">
							{#if isHost}
								You are the host for this lobby.
							{:else}
								{@const hostPlayer = players.find((player) => player.userId === game.hostId)}
								Hosted by <strong>{hostPlayer?.name ?? "the lobby host"}</strong>.
							{/if}
						</p>

						<div class="settings-pills">
							<span class="settings-pill">120s per round</span>
							<span class="settings-pill">5 rounds</span>
							<span class="settings-pill">
								{game.mode?.environment === "indoor"
									? "Indoor only"
									: game.mode?.environment === "outdoor"
										? "Outdoor only"
										: "All environments"}
							</span>
						</div>
					</Card>

					<div class="action-stack">
						{#if connectionState === "disconnected"}
							<Button size="lg" on:click={reconnect}>Reconnect</Button>
						{:else if isHost}
							<Button size="lg" disabled={!allConnectedReady} on:click={startGame}>
								{#if connectedPlayers.length < 2}
									Waiting for players...
								{:else if !allConnectedReady}
									Waiting for ready checks...
								{:else}
									Start Match
								{/if}
							</Button>
							{#if connectedPlayers.length >= 2 && !allConnectedReady}
								<p class="lobby-helper">{connectedPlayers.filter((player) => readyPlayers.includes(player.userId)).length}/{connectedPlayers.length} connected players ready</p>
							{/if}
							{#if lobbyExpiring}
								<Button variant="secondary" size="lg" on:click={extendLobby}>Extend Lobby</Button>
							{/if}
						{:else}
							<p class="lobby-helper">Waiting for the host to start the match.</p>
						{/if}

						<Button variant="outline" size="lg" on:click={leaveLobby}>Leave Lobby</Button>
					</div>
				</Card>

				<Card class="lobby-right">
					<LobbyPlayerList
						{players}
						hostId={game.hostId}
						{currentUserId}
						{readyPlayers}
						showReadyToggle={connectionState !== "disconnected"}
						on:toggleReady={toggleReady}
						on:kick={(event) => kickPlayer(event.detail.userId)}
					/>
				</Card>
			</div>
		</PageShell>
	</div>
{/if}

<style>
	.lobby-actions-top {
		display: flex;
		justify-content: stretch;
	}

	.status-indicator {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		width: 100%;
		padding: 10px 12px;
		border-radius: var(--radius-pill);
		border: 1px solid var(--line);
		background: var(--surface);
		font-size: 13px;
		font-weight: 700;
		color: var(--muted);
	}

	:global(.action-stack > button) {
		width: 100%;
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

	.lobby-grid {
		display: grid;
		gap: 20px;
	}

	:global(.lobby-left),
	:global(.lobby-right),
	:global(.host-card),
	.action-stack {
		display: grid;
		gap: 16px;
	}

	.section-label,
	.host-card__copy,
	.lobby-helper,
	.state-copy {
		margin: 0;
	}

	.section-label {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.host-card__copy,
	.lobby-helper,
	.state-copy {
		font-size: 14px;
		line-height: 1.55;
		color: var(--muted);
	}

	.settings-pills {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.settings-pill {
		display: inline-flex;
		align-items: center;
		padding: 6px 10px;
		border-radius: var(--radius-pill);
		background: var(--surface);
		border: 1px solid var(--line);
		font-size: 12px;
		font-weight: 700;
		color: var(--muted);
	}

	.state-screen {
		min-height: 100vh;
		display: grid;
		place-items: center;
		background: var(--canvas);
	}

	.state-screen--stacked {
		gap: 16px;
	}

	.countdown-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(28, 25, 23, 0.72);
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
		gap: 22px;
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
	}

	.count-num {
		font-family: "IBM Plex Mono", monospace;
		font-size: 72px;
		font-weight: 700;
		color: #fff;
		line-height: 1;
	}

	.countdown-text {
		text-align: center;
	}

	.countdown-text h2,
	.countdown-text p {
		margin: 0;
	}

	.countdown-text h2 {
		font-size: 32px;
		font-weight: 800;
		color: #fff;
	}

	.countdown-text p {
		margin-top: 8px;
		font-size: 14px;
		color: rgba(255, 255, 255, 0.72);
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.4; }
	}

	@keyframes ringExpand {
		0% { transform: scale(0.6); opacity: 0.6; }
		100% { transform: scale(2.2); opacity: 0; }
	}

	@media (min-width: 640px) {
		.lobby-actions-top {
			justify-content: flex-end;
		}

		.status-indicator {
			width: auto;
		}
	}

	@media (min-width: 1024px) {
		.lobby-grid {
			grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
		}
	}
</style>
