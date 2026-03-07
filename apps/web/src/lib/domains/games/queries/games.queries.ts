import { gamesService } from "../api/games.service";

export const gameQueries = {
	byId: (id: string) => ({
		queryKey: ["games", id],
		queryFn: () => gamesService.getById(id),
	}),

	active: () => ({
		queryKey: ["games", "active"],
		queryFn: () => gamesService.getActive(),
		staleTime: 0,
	}),

	list: (params?: { status?: string; limit?: number; offset?: number }) => ({
		queryKey: ["games", "list", params],
		queryFn: () => gamesService.list(params),
	}),
};
