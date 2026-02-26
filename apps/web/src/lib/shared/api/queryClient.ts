/**
 * Svelte Query client configuration.
 */

import { QueryClient } from "@tanstack/svelte-query";
import { ApiRequestError } from "./types";

function queryRetry(failureCount: number, error: unknown): boolean {
	if (error instanceof ApiRequestError && error.status === 401) {
		return false;
	}

	return failureCount < 1;
}

export const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			staleTime: 5 * 60 * 1000, // 5 minutes
			retry: queryRetry,
			refetchOnWindowFocus: false,
		},
	},
});
