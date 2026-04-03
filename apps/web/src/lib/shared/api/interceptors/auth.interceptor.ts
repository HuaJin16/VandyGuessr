/**
 * Auth interceptor - attaches Bearer token to requests.
 */

import { getAuthToken } from "$lib/shared/auth/token";
import type { InternalAxiosRequestConfig } from "axios";

export async function authInterceptor(
	config: InternalAxiosRequestConfig,
): Promise<InternalAxiosRequestConfig> {
	try {
		const token = await getAuthToken();
		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
		}
	} catch {
		// If we can't get the token, continue without it
		// The API will return 401 if auth is required
	}
	return config;
}
