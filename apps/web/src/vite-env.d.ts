/// <reference types="svelte" />
/// <reference types="vite/client" />

interface ImportMetaEnv {
	readonly VITE_API_URL: string;
	readonly VITE_MICROSOFT_CLIENT_ID: string;
	readonly VITE_MICROSOFT_REDIRECT_URI: string;
	readonly VITE_GOOGLE_CLIENT_ID: string;
	readonly VITE_FEATURE_MULTIPLAYER: string;
	readonly VITE_FEATURE_VANDERBILT_RESTRICTED_LOGINS: string;
}

interface ImportMeta {
	readonly env: ImportMetaEnv;
}
