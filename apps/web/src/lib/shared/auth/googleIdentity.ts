const GOOGLE_SCRIPT_SRC = "https://accounts.google.com/gsi/client";
const GOOGLE_TOKEN_STORAGE_KEY = "vandyguessr.google.id_token";

type GoogleApi = {
	accounts?: {
		id?: {
			initialize: (options: GoogleInitializeOptions) => void;
			renderButton: (parent: HTMLElement, options: GoogleRenderOptions) => void;
		};
	};
};

type GoogleInitializeOptions = {
	client_id: string;
	callback: (response: GoogleCredentialResponse) => void;
	ux_mode?: "popup" | "redirect";
	auto_select?: boolean;
	cancel_on_tap_outside?: boolean;
};

type GoogleRenderOptions = {
	type?: "standard" | "icon";
	theme?: "outline" | "filled_blue" | "filled_black";
	size?: "large" | "medium" | "small";
	text?: "signin_with" | "signup_with" | "continue_with" | "signin";
	shape?: "rectangular" | "pill" | "circle" | "square";
	logo_alignment?: "left" | "center";
	width?: number;
};

type GoogleCredentialResponse = {
	credential?: string;
};

type RenderGoogleButtonOptions = {
	container: HTMLElement;
	clientId: string;
	onSuccess: (token: string) => void;
	onError: (message: string) => void;
};

let scriptPromise: Promise<void> | null = null;

function base64UrlDecode(segment: string): string {
	const normalized = segment.replace(/-/g, "+").replace(/_/g, "/");
	const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
	return atob(padded);
}

export type DecodedGoogleToken = {
	sub: string;
	email?: string;
	name?: string;
	exp?: number;
};

export function decodeGoogleIdToken(token: string): DecodedGoogleToken | null {
	const parts = token.split(".");
	if (parts.length < 2) {
		return null;
	}

	try {
		const payload = JSON.parse(base64UrlDecode(parts[1])) as DecodedGoogleToken;
		if (!payload.sub) {
			return null;
		}
		return payload;
	} catch {
		return null;
	}
}

export function getStoredGoogleToken(): string | null {
	return localStorage.getItem(GOOGLE_TOKEN_STORAGE_KEY);
}

export function storeGoogleToken(token: string): void {
	localStorage.setItem(GOOGLE_TOKEN_STORAGE_KEY, token);
}

export function clearGoogleToken(): void {
	localStorage.removeItem(GOOGLE_TOKEN_STORAGE_KEY);
}

export function isGoogleTokenExpired(token: string): boolean {
	const decoded = decodeGoogleIdToken(token);
	if (!decoded?.exp) {
		return true;
	}
	return decoded.exp * 1000 <= Date.now();
}

function loadGoogleScript(): Promise<void> {
	if ((window as Window & { google?: GoogleApi }).google?.accounts?.id) {
		return Promise.resolve();
	}

	if (scriptPromise) {
		return scriptPromise;
	}

	scriptPromise = new Promise((resolve, reject) => {
		const windowWithGoogle = window as Window & { google?: GoogleApi };
		const existing = document.querySelector<HTMLScriptElement>(
			`script[src="${GOOGLE_SCRIPT_SRC}"]`,
		);
		const script = existing ?? document.createElement("script");
		const timeoutId = window.setTimeout(() => {
			cleanup();
			reject(new Error("Failed to load Google sign-in"));
		}, 10000);

		const cleanup = () => {
			window.clearTimeout(timeoutId);
			script.removeEventListener("load", onLoad);
			script.removeEventListener("error", onError);
		};

		const onLoad = () => {
			cleanup();
			if (windowWithGoogle.google?.accounts?.id) {
				resolve();
				return;
			}
			reject(new Error("Google sign-in is unavailable"));
		};

		const onError = () => {
			cleanup();
			reject(new Error("Failed to load Google sign-in"));
		};

		script.addEventListener("load", onLoad);
		script.addEventListener("error", onError);

		script.src = GOOGLE_SCRIPT_SRC;
		script.async = true;
		script.defer = true;

		if (!existing) {
			document.head.appendChild(script);
			return;
		}

		window.setTimeout(() => {
			if (windowWithGoogle.google?.accounts?.id) {
				onLoad();
			}
		}, 0);
	});

	return scriptPromise;
}

export async function renderGoogleSignInButton({
	container,
	clientId,
	onSuccess,
	onError,
}: RenderGoogleButtonOptions): Promise<void> {
	await loadGoogleScript();

	const google = (window as Window & { google?: GoogleApi }).google?.accounts?.id;
	if (!google) {
		throw new Error("Google sign-in is unavailable");
	}

	google.initialize({
		client_id: clientId,
		callback: (response: GoogleCredentialResponse) => {
			const credential = response.credential;
			if (!credential) {
				onError("Google sign-in did not return a token");
				return;
			}
			onSuccess(credential);
		},
		ux_mode: "popup",
		auto_select: false,
		cancel_on_tap_outside: true,
	});

	const width = Math.round(container.getBoundingClientRect().width || 320);
	container.replaceChildren();
	google.renderButton(container, {
		type: "standard",
		theme: "outline",
		size: "large",
		text: "continue_with",
		shape: "rectangular",
		logo_alignment: "left",
		width,
	});
}
