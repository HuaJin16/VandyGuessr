import { gamesService } from "../api/games.service";

export const gameQueries = {
	byId: (id: string, currentUserOid: string | null) => ({
		queryKey: ["games", "by-id", currentUserOid, id] as const,
		queryFn: () => gamesService.getById(id),
	}),

	active: (currentUserOid: string | null) => ({
		queryKey: ["games", "active", currentUserOid] as const,
		queryFn: () => gamesService.getActive(),
		staleTime: 0,
	}),

	list: (
		params: { status?: string; limit?: number; offset?: number } | undefined,
		currentUserOid: string | null,
	) => ({
		queryKey: ["games", "list", currentUserOid, params] as const,
		queryFn: () => gamesService.list(params),
	}),
};
