import { apiClient } from "$lib/shared/api/client";
import type { CreateMultiplayerRequest, JoinMultiplayerRequest, MultiplayerGame } from "../types";

export const multiplayerService = {
	create: (data: CreateMultiplayerRequest) =>
		apiClient.post<MultiplayerGame>("/v1/multiplayer/create", data).then((r) => r.data),

	join: (data: JoinMultiplayerRequest) =>
		apiClient.post<MultiplayerGame>("/v1/multiplayer/join", data).then((r) => r.data),

	getById: (id: string) =>
		apiClient.get<MultiplayerGame>(`/v1/multiplayer/${id}`).then((r) => r.data),

	getActive: () =>
		apiClient.get<MultiplayerGame | null>("/v1/multiplayer/active").then((r) => r.data),
};
