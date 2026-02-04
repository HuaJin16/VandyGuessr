/**
 * MSAL PublicClientApplication instance.
 */

import { PublicClientApplication } from "@azure/msal-browser";
import { msalConfig } from "./msalConfig";

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
