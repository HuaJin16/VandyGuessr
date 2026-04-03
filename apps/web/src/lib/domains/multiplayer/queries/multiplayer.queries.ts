import { multiplayerService } from "../api/multiplayer.service";

export const multiplayerQueries = {
	byId: (id: string, currentUserOid: string | null) => ({
		queryKey: ["multiplayer", "by-id", currentUserOid, id] as const,
		queryFn: () => multiplayerService.getById(id),
	}),

	active: (currentUserOid: string | null) => ({
		queryKey: ["multiplayer", "active", currentUserOid] as const,
		queryFn: () => multiplayerService.getActive(),
		staleTime: 0,
	}),
};
