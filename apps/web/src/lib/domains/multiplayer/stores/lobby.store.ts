import { derived, writable } from "svelte/store";
import type { LobbyStatus, MultiplayerGame, MultiplayerPlayer } from "../types";

function toLobbyStatus(status: MultiplayerGame["status"]): LobbyStatus {
	if (status === "waiting") return "waiting";
	if (status === "active") return "starting";
	return "cancelled";
}

interface LobbyState {
	game: MultiplayerGame | null;
	players: MultiplayerPlayer[];
	readyPlayers: string[];
	countdown: number | null;
	status: LobbyStatus;
}

const initial: LobbyState = {
	game: null,
	players: [],
	readyPlayers: [],
	countdown: null,
	status: "waiting",
};

function createLobbyStore() {
	const { subscribe, set, update } = writable<LobbyState>(initial);

	return {
		subscribe,
		setGame(game: MultiplayerGame) {
			update((s) => ({
				...s,
				game,
				players: game.players,
				readyPlayers: [],
				status: toLobbyStatus(game.status),
			}));
		},
		setReadyPlayers(readyPlayers: string[]) {
			update((s) => ({ ...s, readyPlayers }));
		},
		setPlayerReady(userId: string) {
			update((s) => ({
				...s,
				readyPlayers: s.readyPlayers.includes(userId)
					? s.readyPlayers
					: [...s.readyPlayers, userId],
			}));
		},
		setPlayerUnready(userId: string) {
			update((s) => ({
				...s,
				readyPlayers: s.readyPlayers.filter((id) => id !== userId),
			}));
		},
		setPlayers(players: MultiplayerPlayer[]) {
			update((s) => ({
				...s,
				players,
				readyPlayers: s.readyPlayers.filter((id) => players.some((p) => p.userId === id)),
				game: s.game ? { ...s.game, players } : s.game,
			}));
		},
		addPlayer(player: MultiplayerPlayer) {
			update((s) => {
				const exists = s.players.some((p) => p.userId === player.userId);
				const players = exists ? s.players : [...s.players, player];
				return {
					...s,
					players,
					game: s.game ? { ...s.game, players } : s.game,
				};
			});
		},
		removePlayer(userId: string) {
			update((s) => {
				const players = s.players.filter((p) => p.userId !== userId);
				return {
					...s,
					players,
					readyPlayers: s.readyPlayers.filter((id) => id !== userId),
					game: s.game ? { ...s.game, players } : s.game,
				};
			});
		},
		updatePlayerStatus(userId: string, status: MultiplayerPlayer["status"]) {
			update((s) => {
				const players = s.players.map((p) => (p.userId === userId ? { ...p, status } : p));
				return {
					...s,
					players,
					game: s.game ? { ...s.game, players } : s.game,
				};
			});
		},
		setCountdown(countdown: number | null) {
			update((s) => ({ ...s, countdown, status: countdown !== null ? "starting" : s.status }));
		},
		setCancelled() {
			update((s) => ({ ...s, status: "cancelled" }));
		},
		reset() {
			set(initial);
		},
	};
}

export const lobbyStore = createLobbyStore();

export const playerCount = derived({ subscribe: lobbyStore.subscribe }, ($s) => $s.players.length);
