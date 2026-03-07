import { leaderboardService } from "../api/leaderboard.service";
import type { LeaderboardParams } from "../types";

export const leaderboardQueries = {
	leaderboard: (params: LeaderboardParams) => ({
		queryKey: ["leaderboard", params.timeframe, params.mode, params.offset, params.limit] as const,
		queryFn: () => leaderboardService.getLeaderboard(params),
		staleTime: 2 * 60 * 1000,
	}),
};
