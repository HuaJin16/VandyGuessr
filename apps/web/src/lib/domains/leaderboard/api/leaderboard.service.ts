import { apiClient } from "$lib/shared/api/client";
import type { LeaderboardParams, LeaderboardResponse } from "../types";

export const leaderboardService = {
	getLeaderboard: (params: LeaderboardParams) =>
		apiClient.get<LeaderboardResponse>("/v1/leaderboard", { params }).then((r) => r.data),
};
