/**
 * Error interceptor - transforms API errors consistently.
 */

import type { AxiosError } from "axios";
import { ApiRequestError } from "../types";

interface ApiErrorResponse {
	detail?: string;
	message?: string;
}

export function errorInterceptor(error: AxiosError<ApiErrorResponse>): never {
	const status = error.response?.status || 500;
	const detail = error.response?.data?.detail || error.response?.data?.message;
	const message = detail || error.message || "An unexpected error occurred";

	throw new ApiRequestError(message, status, detail);
}
