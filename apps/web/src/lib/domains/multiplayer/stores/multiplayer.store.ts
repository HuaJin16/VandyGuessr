import { derived, writable } from "svelte/store";
import type {
	ConnectionState,
	MultiplayerGame,
	MultiplayerPhase,
	RoundResult,
	Standing,
} from "../types";

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
	submitting: false,
};

function createMultiplayerStore() {
	const { subscribe, set, update } = writable<MultiplayerState>(initial);

	return {
		subscribe,
		setGame(game: MultiplayerGame) {
			update((s) => ({ ...s, game }));
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
		setGameOver(standings: Standing[]) {
			update((s) => ({
				...s,
				phase: "game_over",
				standings,
			}));
		},
		setSubmitting(v: boolean) {
			update((s) => ({ ...s, submitting: v }));
		},
		applyGameState(payload: {
			currentRound: number;
			round: { round: number; imageUrl: string; expiresAt: string } | null;
			playersGuessed: string[];
			hasGuessedThisRound: boolean;
		}) {
			update((s) => ({
				...s,
				phase: payload.round ? "playing" : s.phase,
				currentRound: payload.currentRound,
				imageUrl: payload.round?.imageUrl ?? s.imageUrl,
				expiresAt: payload.round?.expiresAt ?? s.expiresAt,
				playersGuessed: payload.playersGuessed,
				hasGuessedThisRound: payload.hasGuessedThisRound,
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
