import { derived, writable } from "svelte/store";
import type { Game, Round } from "../types";

export type GamePhase = "playing" | "results";

interface GameState {
	game: Game | null;
	phase: GamePhase;
	currentRoundIndex: number;
	guessPosition: { lat: number; lng: number } | null;
	submitting: boolean;
	showEndDialog: boolean;
}

const initial: GameState = {
	game: null,
	phase: "playing",
	currentRoundIndex: 0,
	guessPosition: null,
	submitting: false,
	showEndDialog: false,
};

function createGameStore() {
	const { subscribe, set, update } = writable<GameState>(initial);

	return {
		subscribe,
		setGame(game: Game) {
			update((s) => {
				const idx = game.rounds.findIndex((r) => !r.guess && !r.skipped);
				const lastGuessed = [...game.rounds].reverse().find((r) => r.guess);
				const phase: GamePhase =
					game.status !== "active" || (lastGuessed && idx === -1) ? "results" : "playing";
				return {
					...s,
					game,
					currentRoundIndex: idx === -1 ? game.rounds.length - 1 : idx,
					phase,
					guessPosition: null,
				};
			});
		},
		updateGame(game: Game) {
			update((s) => ({ ...s, game }));
		},
		setPhase(phase: GamePhase) {
			update((s) => ({ ...s, phase }));
		},
		showResults(game: Game, roundIndex: number) {
			update((s) => ({
				...s,
				game,
				phase: "results",
				currentRoundIndex: roundIndex,
				guessPosition: null,
			}));
		},
		nextRound() {
			update((s) => {
				if (!s.game) return s;
				const next = s.currentRoundIndex + 1;
				if (next >= s.game.rounds.length) return s;
				return {
					...s,
					phase: "playing",
					currentRoundIndex: next,
					guessPosition: null,
				};
			});
		},
		setGuessPosition(pos: { lat: number; lng: number } | null) {
			update((s) => ({ ...s, guessPosition: pos }));
		},
		setSubmitting(v: boolean) {
			update((s) => ({ ...s, submitting: v }));
		},
		toggleEndDialog() {
			update((s) => ({ ...s, showEndDialog: !s.showEndDialog }));
		},
		reset() {
			set(initial);
		},
	};
}

export const gameStore = createGameStore();

export const currentRound = derived({ subscribe: gameStore.subscribe }, ($s): Round | null =>
	$s.game ? ($s.game.rounds[$s.currentRoundIndex] ?? null) : null,
);
