import { writable } from "svelte/store";
import type { LeaderboardGameType, LeaderboardMode, LeaderboardTimeframe } from "../types";

interface LeaderboardViewState {
	timeframe: LeaderboardTimeframe;
	mode: LeaderboardMode;
	gameType: LeaderboardGameType;
	limit: number;
	offset: number;
}

const initialState: LeaderboardViewState = {
	timeframe: "daily",
	mode: "all",
	gameType: "all",
	limit: 8,
	offset: 0,
};

export function createLeaderboardViewStore() {
	const { subscribe, update } = writable<LeaderboardViewState>(initialState);

	return {
		subscribe,
		setTimeframe(timeframe: LeaderboardTimeframe) {
			update((state) =>
				state.timeframe === timeframe ? state : { ...state, timeframe, offset: 0 },
			);
		},
		setMode(mode: LeaderboardMode) {
			update((state) => (state.mode === mode ? state : { ...state, mode, offset: 0 }));
		},
		setGameType(gameType: LeaderboardGameType) {
			update((state) => (state.gameType === gameType ? state : { ...state, gameType, offset: 0 }));
		},
		setLimit(limit: number) {
			update((state) => (state.limit === limit ? state : { ...state, limit }));
		},
		setOffset(offset: number) {
			update((state) => (state.offset === offset ? state : { ...state, offset }));
		},
	};
}
