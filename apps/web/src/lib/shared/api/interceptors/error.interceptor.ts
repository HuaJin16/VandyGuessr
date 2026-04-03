/**
 * Error interceptor - transforms API errors consistently.
 */

import type { AxiosError } from "axios";
import { get } from "svelte/store";
import { auth } from "../../auth/auth.store";
import { ApiRequestError } from "../types";

interface ApiErrorResponse {
	detail?: string;
	message?: string;
}

export function errorInterceptor(error: AxiosError<ApiErrorResponse>): never {
	const status = error.response?.status || 500;
	const detail = error.response?.data?.detail || error.response?.data?.message;
	const message = detail || error.message || "An unexpected error occurred";

	if (status === 401 && get(auth).currentUserOid !== null) {
		auth.logout();
	}

	throw new ApiRequestError(message, status, detail);
}
