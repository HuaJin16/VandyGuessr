/**
 * Auth store for managing authentication state (client-only).
 */

import type { AccountInfo } from "@azure/msal-browser";
import { derived, writable } from "svelte/store";
import { loginRequest } from "./msalConfig";
import { initializeMsal, msalInstance } from "./msalInstance";

interface AuthState {
	isInitialized: boolean;
	isLoading: boolean;
	account: AccountInfo | null;
	error: string | null;
}

const initialState: AuthState = {
	isInitialized: false,
	isLoading: true,
	account: null,
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

				update((state) => ({
					...state,
					account,
					isInitialized: true,
					isLoading: false,
				}));
			} catch {
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
			} catch {
				update((state) => ({
					...state,
					isLoading: false,
					error: "Failed to start login",
				}));
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
export const isAuthenticated = derived(auth, ($auth) => $auth.account !== null);
export const isLoading = derived(auth, ($auth) => $auth.isLoading);
export const authError = derived(auth, ($auth) => $auth.error);
