/**
 * Users query definitions for Svelte Query.
 */

import { usersService } from "../api/users.service";

export const userQueries = {
	me: (currentUserOid: string | null) => ({
		queryKey: ["users", "me", currentUserOid] as const,
		queryFn: () => usersService.getMe(),
		staleTime: 5 * 60 * 1000, // 5 minutes
	}),
};
