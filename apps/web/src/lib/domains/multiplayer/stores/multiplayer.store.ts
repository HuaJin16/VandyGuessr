import { derived, writable } from "svelte/store";
import type {
	ConnectionState,
	GameOverRound,
	MultiplayerGame,
	MultiplayerGameStatus,
	MultiplayerPhase,
	MultiplayerPlayer,
	RoundResult,
	Standing,
} from "../types";

function statusToPhase(status: MultiplayerGameStatus): MultiplayerPhase {
	if (status === "active") return "playing";
	if (status === "completed") return "game_over";
	if (status === "cancelled" || status === "abandoned") return "lobby";
	return "lobby";
}

interface MultiplayerState {
	connection: ConnectionState;
	game: MultiplayerGame | null;
	phase: MultiplayerPhase;
	currentRound: number;
	imageUrl: string | null;
	expiresAt: string | null;
	guessPosition: { lat: number; lng: number } | null;
	hasGuessedThisRound: boolean;
	playersGuessed: string[];
	roundResult: RoundResult | null;
	standings: Standing[];
	rounds: GameOverRound[];
	submitting: boolean;
}

const initial: MultiplayerState = {
	connection: "connecting",
	game: null,
	phase: "lobby",
	currentRound: 0,
	imageUrl: null,
	expiresAt: null,
	guessPosition: null,
	hasGuessedThisRound: false,
	playersGuessed: [],
	roundResult: null,
	standings: [],
	rounds: [],
	submitting: false,
};

function createMultiplayerStore() {
	const { subscribe, set, update } = writable<MultiplayerState>(initial);

	return {
		subscribe,
		setGame(game: MultiplayerGame) {
			update((s) => ({ ...s, game, phase: statusToPhase(game.status) }));
		},
		setConnection(connection: ConnectionState) {
			update((s) => ({ ...s, connection }));
		},
		setPhase(phase: MultiplayerPhase) {
			update((s) => ({ ...s, phase }));
		},
		startRound(round: number, imageUrl: string, expiresAt: string) {
			update((s) => ({
				...s,
				phase: "playing",
				currentRound: round,
				imageUrl,
				expiresAt,
				guessPosition: null,
				hasGuessedThisRound: false,
				playersGuessed: [],
				roundResult: null,
				submitting: false,
			}));
		},
		setGuessPosition(pos: { lat: number; lng: number } | null) {
			update((s) => ({ ...s, guessPosition: pos }));
		},
		markGuessAccepted() {
			update((s) => ({ ...s, hasGuessedThisRound: true, submitting: false }));
		},
		addPlayerGuessed(userId: string) {
			update((s) => ({
				...s,
				playersGuessed: s.playersGuessed.includes(userId)
					? s.playersGuessed
					: [...s.playersGuessed, userId],
			}));
		},
		setRoundResult(result: RoundResult) {
			update((s) => ({
				...s,
				phase: "results",
				roundResult: result,
				standings: result.standings,
			}));
		},
		setGameOver(standings: Standing[], rounds: GameOverRound[]) {
			update((s) => ({
				...s,
				phase: "game_over",
				standings,
				rounds,
				game: s.game ? { ...s.game, status: "completed" } : s.game,
			}));
		},
		updatePlayerStatus(userId: string, status: MultiplayerPlayer["status"]) {
			update((s) => {
				if (!s.game) return s;
				return {
					...s,
					game: {
						...s.game,
						players: s.game.players.map((player) =>
							player.userId === userId ? { ...player, status } : player,
						),
					},
				};
			});
		},
		setSubmitting(v: boolean) {
			update((s) => ({ ...s, submitting: v }));
		},
		applyGameState(payload: {
			status: MultiplayerGameStatus;
			currentRound: number;
			round: { round: number; imageUrl: string; expiresAt: string | null } | null;
			playersGuessed: string[];
			hasGuessedThisRound: boolean;
			players: Array<{
				userId: string;
				name: string;
				status: MultiplayerPlayer["status"];
				totalScore: number;
			}>;
		}) {
			const standings = [...payload.players]
				.sort((a, b) => b.totalScore - a.totalScore)
				.map((player, index) => ({
					userId: player.userId,
					name: player.name,
					totalScore: player.totalScore,
					rank: index + 1,
				}));

			update((s) => ({
				...s,
				phase: payload.round ? "playing" : statusToPhase(payload.status),
				currentRound: payload.currentRound,
				imageUrl: payload.round?.imageUrl ?? null,
				expiresAt: payload.round?.expiresAt ?? null,
				playersGuessed: payload.playersGuessed,
				hasGuessedThisRound: payload.hasGuessedThisRound,
				standings,
				game: s.game
					? {
							...s.game,
							status: payload.status,
							currentRound: payload.currentRound,
							players: s.game.players.map((player) => {
								const next = payload.players.find((p) => p.userId === player.userId);
								if (!next) return player;
								return {
									...player,
									status: next.status,
									totalScore: next.totalScore,
								};
							}),
						}
					: s.game,
			}));
		},
		reset() {
			set(initial);
		},
	};
}

export const multiplayerStore = createMultiplayerStore();

export const timeRemaining = derived({ subscribe: multiplayerStore.subscribe }, ($s) => {
	if (!$s.expiresAt) return null;
	const remaining = Math.max(0, new Date($s.expiresAt).getTime() - Date.now());
	return Math.ceil(remaining / 1000);
});
