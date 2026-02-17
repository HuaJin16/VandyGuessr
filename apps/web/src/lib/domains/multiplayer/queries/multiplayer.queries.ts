import { multiplayerService } from "../api/multiplayer.service";

export const multiplayerQueries = {
	byId: (id: string) => ({
		queryKey: ["multiplayer", id],
		queryFn: () => multiplayerService.getById(id),
	}),

	active: () => ({
		queryKey: ["multiplayer", "active"],
		queryFn: () => multiplayerService.getActive(),
		staleTime: 0,
	}),
};
