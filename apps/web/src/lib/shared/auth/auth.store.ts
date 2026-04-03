/**
 * Auth store for managing authentication state (client-only).
 */

import { queryClient } from "$lib/shared/api/queryClient";
import type { AccountInfo } from "@azure/msal-browser";
import { derived, writable } from "svelte/store";
import {
	clearGoogleToken,
	decodeGoogleIdToken,
	getStoredGoogleToken,
	isGoogleTokenExpired,
	storeGoogleToken,
} from "./googleIdentity";
import { loginRequest } from "./msalConfig";
import { initializeMsal, msalInstance } from "./msalInstance";

type AuthProvider = "microsoft" | "google" | null;
type AuthFlow = "microsoft" | "google" | null;

interface AuthState {
	isInitialized: boolean;
	isLoading: boolean;
	activeAuthFlow: AuthFlow;
	provider: AuthProvider;
	account: AccountInfo | null;
	currentUserOid: string | null;
	error: string | null;
}

const initialState: AuthState = {
	isInitialized: false,
	isLoading: true,
	activeAuthFlow: null,
	provider: null,
	account: null,
	currentUserOid: null,
	error: null,
};

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(initialState);

	return {
		subscribe,

		/** Initialize MSAL and restore session if available */
		async initialize() {
			const isVanderbiltRestricted =
				import.meta.env.VITE_FEATURE_VANDERBILT_RESTRICTED_LOGINS !== "false";

			try {
				await initializeMsal();
				const microsoftAccount = msalInstance.getActiveAccount();

				if (microsoftAccount) {
					update((state) => ({
						...state,
						provider: "microsoft",
						account: microsoftAccount,
						currentUserOid: microsoftAccount.localAccountId,
						isInitialized: true,
						isLoading: false,
					}));
					return;
				}

				if (!isVanderbiltRestricted) {
					const googleToken = getStoredGoogleToken();
					if (googleToken && !isGoogleTokenExpired(googleToken)) {
						const decoded = decodeGoogleIdToken(googleToken);
						if (decoded?.sub) {
							update((state) => ({
								...state,
								provider: "google",
								account: null,
								currentUserOid: `google:${decoded.sub}`,
								isInitialized: true,
								isLoading: false,
							}));
							return;
						}
					}
				}

				clearGoogleToken();

				update((state) => ({
					...state,
					provider: null,
					account: null,
					currentUserOid: null,
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

		/** Start the Microsoft login redirect flow */
		async loginWithMicrosoft() {
			update((state) => ({ ...state, activeAuthFlow: "microsoft", error: null }));

			try {
				await msalInstance.loginRedirect(loginRequest);
			} catch {
				update((state) => ({
					...state,
					activeAuthFlow: null,
					error: "Failed to start login",
				}));
			}
		},

		async completeGoogleLogin(token: string) {
			update((state) => ({ ...state, activeAuthFlow: "google", error: null }));

			try {
				const decoded = decodeGoogleIdToken(token);
				if (!decoded?.sub) {
					throw new Error("Google sign-in returned an invalid token");
				}

				storeGoogleToken(token);
				update((state) => ({
					...state,
					activeAuthFlow: null,
					provider: "google",
					account: null,
					currentUserOid: `google:${decoded.sub}`,
					error: null,
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : "Failed to start Google login";
				update((state) => ({
					...state,
					activeAuthFlow: null,
					error: message,
				}));
			}
		},

		failGoogleLogin(message: string) {
			update((state) => ({
				...state,
				activeAuthFlow: null,
				error: message,
			}));
		},

		/** Clear local auth state (logout from app only) */
		logout() {
			clearGoogleToken();

			const accounts = msalInstance.getAllAccounts();
			for (const account of accounts) {
				msalInstance.clearCache({
					account,
				});
			}
			msalInstance.setActiveAccount(null);
			queryClient.clear();

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
export const isAuthenticated = derived(auth, ($auth) => $auth.currentUserOid !== null);
export const isLoading = derived(auth, ($auth) => $auth.isLoading);
export const isAuthFlowLoading = derived(auth, ($auth) => $auth.activeAuthFlow !== null);
export const isMicrosoftLoading = derived(auth, ($auth) => $auth.activeAuthFlow === "microsoft");
export const isGoogleLoading = derived(auth, ($auth) => $auth.activeAuthFlow === "google");
export const authError = derived(auth, ($auth) => $auth.error);
