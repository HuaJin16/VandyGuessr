/**
 * MSAL configuration for Microsoft OAuth.
 */

import type { Configuration, RedirectRequest } from "@azure/msal-browser";

export const msalConfig: Configuration = {
	auth: {
		clientId: import.meta.env.VITE_MICROSOFT_CLIENT_ID || "",
		authority: "https://login.microsoftonline.com/common",
		redirectUri: import.meta.env.VITE_MICROSOFT_REDIRECT_URI || "http://localhost:5173",
		postLogoutRedirectUri: import.meta.env.VITE_MICROSOFT_REDIRECT_URI || "http://localhost:5173",
	},
	cache: {
		cacheLocation: "localStorage",
		storeAuthStateInCookie: false,
	},
};

export const loginRequest: RedirectRequest = {
	scopes: ["openid", "profile", "email"],
};
