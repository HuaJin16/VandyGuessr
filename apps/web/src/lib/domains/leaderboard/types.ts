export type LeaderboardTimeframe = "daily" | "weekly" | "alltime";
export type LeaderboardMode = "all" | "indoor" | "outdoor";
export type LeaderboardGameType = "all" | "daily" | "random";

export interface LeaderboardEntry {
	rank: number;
	userId: string;
	name: string;
	username: string;
	totalPoints: number;
	avgScore: number;
	gamesPlayed: number;
	roundsPlayed: number;
}

export interface LeaderboardResponse {
	entries: LeaderboardEntry[];
	userEntry: LeaderboardEntry | null;
	contextEntries: LeaderboardEntry[];
	totalCount: number;
}

export interface LeaderboardParams {
	timeframe: LeaderboardTimeframe;
	mode: LeaderboardMode;
	gameType: LeaderboardGameType;
	limit: number;
	offset: number;
}
