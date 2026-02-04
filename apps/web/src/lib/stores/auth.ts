/**
 * Auth store for managing authentication state.
 */

import type { AccountInfo } from "@azure/msal-browser";
import { derived, writable } from "svelte/store";
import { loginRequest } from "../auth/msalConfig";
import { initializeMsal, msalInstance } from "../auth/msalInstance";

/** User profile from the API */
export interface User {
	id: string;
	email: string;
	username: string;
	name: string;
	avatar_url: string | null;
}

interface AuthState {
	isInitialized: boolean;
	isLoading: boolean;
	account: AccountInfo | null;
	user: User | null;
	error: string | null;
}

const initialState: AuthState = {
	isInitialized: false,
	isLoading: true,
	account: null,
	user: null,
	error: null,
};

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(initialState);

	return {
		subscribe,

		/** Initialize MSAL and restore session if available */
		async initialize() {
			try {
				await initializeMsal();
				const account = msalInstance.getActiveAccount();

				if (account) {
					update((state) => ({ ...state, account, isLoading: true }));
					await this.fetchUser();
				}

				update((state) => ({
					...state,
					isInitialized: true,
					isLoading: false,
				}));
			} catch (error) {
				update((state) => ({
					...state,
					isInitialized: true,
					isLoading: false,
					error: "Failed to initialize authentication",
				}));
			}
		},

		/** Start the login redirect flow */
		async login() {
			update((state) => ({ ...state, isLoading: true, error: null }));

			try {
				await msalInstance.loginRedirect(loginRequest);
			} catch (error) {
				update((state) => ({
					...state,
					isLoading: false,
					error: "Failed to start login",
				}));
			}
		},

		/** Fetch the user profile from the API */
		async fetchUser() {
			const account = msalInstance.getActiveAccount();
			if (!account) return;

			try {
				const tokenResponse = await msalInstance.acquireTokenSilent({
					...loginRequest,
					account,
				});

				const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

				const response = await fetch(`${apiUrl}/v1/users/me`, {
					headers: {
						Authorization: `Bearer ${tokenResponse.accessToken}`,
					},
				});

				if (!response.ok) {
					const errorData = await response.json().catch(() => ({}));
					throw new Error(errorData.detail || "Failed to fetch user");
				}

				const user = await response.json();
				update((state) => ({ ...state, user, error: null }));
			} catch (error) {
				const message = error instanceof Error ? error.message : "Failed to fetch user";
				update((state) => ({ ...state, error: message }));
			}
		},

		/** Clear local auth state (logout from app only) */
		logout() {
			const accounts = msalInstance.getAllAccounts();
			for (const account of accounts) {
				msalInstance.clearCache({
					account,
				});
			}
			msalInstance.setActiveAccount(null);

			set({ ...initialState, isInitialized: true, isLoading: false });
		},

		/** Clear any error message */
		clearError() {
			update((state) => ({ ...state, error: null }));
		},
	};
}

export const auth = createAuthStore();

// Derived stores for convenience
export const isAuthenticated = derived(auth, ($auth) => $auth.user !== null);
export const isLoading = derived(auth, ($auth) => $auth.isLoading);
export const currentUser = derived(auth, ($auth) => $auth.user);
export const authError = derived(auth, ($auth) => $auth.error);
