import { get } from "svelte/store";
import { auth } from "./auth.store";
import { getStoredGoogleToken, isGoogleTokenExpired } from "./googleIdentity";
import { getAccessToken as getMicrosoftToken } from "./msalInstance";

export async function getAuthToken(): Promise<string | null> {
	const state = get(auth);

	if (state.provider === "microsoft") {
		return await getMicrosoftToken();
	}

	if (state.provider === "google") {
		const token = getStoredGoogleToken();
		if (!token || isGoogleTokenExpired(token)) {
			auth.logout();
			return null;
		}
		return token;
	}

	return null;
}
