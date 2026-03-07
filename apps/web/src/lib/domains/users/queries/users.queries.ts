/**
 * Users query definitions for Svelte Query.
 */

import { usersService } from "../api/users.service";

export const userQueries = {
	me: () => ({
		queryKey: ["users", "me"] as const,
		queryFn: () => usersService.getMe(),
		staleTime: 5 * 60 * 1000, // 5 minutes
	}),

	byId: (id: string) => ({
		queryKey: ["users", id] as const,
		queryFn: () => usersService.getById(id),
	}),
};
