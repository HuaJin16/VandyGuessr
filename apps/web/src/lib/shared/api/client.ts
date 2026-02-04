/**
 * Axios client instance with interceptors.
 */

import axios from "axios";
import { authInterceptor } from "./interceptors/auth.interceptor";
import { errorInterceptor } from "./interceptors/error.interceptor";

export const apiClient = axios.create({
	baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
	headers: {
		"Content-Type": "application/json",
	},
});

// Attach auth token to all requests
apiClient.interceptors.request.use(authInterceptor);

// Transform errors consistently
apiClient.interceptors.response.use((response) => response, errorInterceptor);
