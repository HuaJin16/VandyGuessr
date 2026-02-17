import { derived, writable } from "svelte/store";
import type { LobbyStatus, MultiplayerGame, MultiplayerPlayer } from "../types";

interface LobbyState {
	game: MultiplayerGame | null;
	players: MultiplayerPlayer[];
	countdown: number | null;
	status: LobbyStatus;
}

const initial: LobbyState = {
	game: null,
	players: [],
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
				status: game.status === "waiting" ? "waiting" : s.status,
			}));
		},
		addPlayer(player: MultiplayerPlayer) {
			update((s) => {
				const exists = s.players.some((p) => p.userId === player.userId);
				return {
					...s,
					players: exists ? s.players : [...s.players, player],
				};
			});
		},
		removePlayer(userId: string) {
			update((s) => ({
				...s,
				players: s.players.filter((p) => p.userId !== userId),
			}));
		},
		updatePlayerStatus(userId: string, status: MultiplayerPlayer["status"]) {
			update((s) => ({
				...s,
				players: s.players.map((p) => (p.userId === userId ? { ...p, status } : p)),
			}));
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
