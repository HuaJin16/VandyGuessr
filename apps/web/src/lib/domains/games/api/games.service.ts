import { apiClient } from "$lib/shared/api/client";
import type { Game, StartGameRequest } from "../types";

export const gamesService = {
	start: (data: StartGameRequest) =>
		apiClient.post<Game>("/v1/games/start", data).then((r) => r.data),

	getById: (id: string) => apiClient.get<Game>(`/v1/games/${id}`).then((r) => r.data),

	startRound: (gameId: string, roundNumber: number) =>
		apiClient.post<Game>(`/v1/games/${gameId}/round/${roundNumber}/start`).then((r) => r.data),

	getActive: () => apiClient.get<Game | null>("/v1/games/active").then((r) => r.data),

	list: (params?: { status?: string; limit?: number; offset?: number }) =>
		apiClient.get<Game[]>("/v1/games", { params }).then((r) => r.data),

	submitGuess: (gameId: string, roundNumber: number, guess: { lat: number; lng: number }) =>
		apiClient
			.post<Game>(`/v1/games/${gameId}/round/${roundNumber}/guess`, guess)
			.then((r) => r.data),

	end: (gameId: string) => apiClient.post<Game>(`/v1/games/${gameId}/end`).then((r) => r.data),
};
