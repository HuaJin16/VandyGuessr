/**
 * MSAL PublicClientApplication instance and utilities.
 */

import { PublicClientApplication } from "@azure/msal-browser";
import { loginRequest, msalConfig } from "./msalConfig";

export const msalInstance = new PublicClientApplication(msalConfig);

/**
 * Initialize MSAL and handle any redirect responses.
 */
export async function initializeMsal(): Promise<void> {
	await msalInstance.initialize();

	// Handle redirect response if returning from login
	const response = await msalInstance.handleRedirectPromise();
	if (response) {
		msalInstance.setActiveAccount(response.account);
	}

	// Set active account if one exists in cache
	const accounts = msalInstance.getAllAccounts();
	if (accounts.length > 0 && !msalInstance.getActiveAccount()) {
		msalInstance.setActiveAccount(accounts[0]);
	}
}

/**
 * Get the access token for API calls.
 * Returns null if not authenticated.
 */
export async function getAccessToken(): Promise<string | null> {
	const account = msalInstance.getActiveAccount();
	if (!account) {
		return null;
	}

	try {
		const tokenResponse = await msalInstance.acquireTokenSilent({
			...loginRequest,
			account,
		});
		return tokenResponse.idToken;
	} catch {
		// Token acquisition failed - user needs to re-authenticate
		return null;
	}
}
