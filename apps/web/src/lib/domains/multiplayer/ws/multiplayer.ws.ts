import { auth } from "$lib/shared/auth/auth.store";
import { getAccessToken } from "$lib/shared/auth/msalInstance";
import { writable } from "svelte/store";
import { ClientEvent, type ConnectionState, type ServerMessage } from "../types";

const WS_PROTOCOL_VERSION = 1;
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_BASE_DELAY_MS = 1000;

interface MultiplayerWsOptions {
	gameId: string;
	onMessage: (message: ServerMessage) => void;
	onConnectionChange?: (state: ConnectionState) => void;
}

function buildWsUrl(gameId: string, token: string): string {
	const base = import.meta.env.VITE_API_URL || "http://localhost:8000";
	const wsBase = base.replace(/^http/, "ws");
	return `${wsBase}/v1/multiplayer/${gameId}/ws?token=${encodeURIComponent(token)}&v=${WS_PROTOCOL_VERSION}`;
}

export function createMultiplayerWs(options: MultiplayerWsOptions) {
	const { gameId, onMessage, onConnectionChange } = options;
	let ws: WebSocket | null = null;
	let reconnectAttempts = 0;
	let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
	let intentionalClose = false;

	const connectionState = writable<ConnectionState>("connecting");

	function setConnectionState(state: ConnectionState) {
		connectionState.set(state);
		onConnectionChange?.(state);
	}

	function handleSessionExpired() {
		setConnectionState("disconnected");
		auth.logout();
	}

	async function connect() {
		if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
			return;
		}

		const token = await getAccessToken();
		if (!token) {
			handleSessionExpired();
			return;
		}

		setConnectionState(reconnectAttempts > 0 ? "reconnecting" : "connecting");

		const url = buildWsUrl(gameId, token);
		ws = new WebSocket(url);

		ws.onopen = () => {
			reconnectAttempts = 0;
			setConnectionState("connected");
		};

		ws.onmessage = (event) => {
			try {
				const data = JSON.parse(event.data) as ServerMessage;
				onMessage(data);
			} catch {}
		};

		ws.onclose = (event) => {
			ws = null;
			if (intentionalClose) {
				setConnectionState("disconnected");
				return;
			}

			if (event.code === 4001) {
				handleSessionExpired();
				return;
			}

			// Non-recoverable close codes — don't reconnect
			const noReconnectCodes = [1000, 4003, 4004, 4010, 4011, 4012];
			if (noReconnectCodes.includes(event.code)) {
				setConnectionState("disconnected");
				return;
			}

			if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
				const delay = RECONNECT_BASE_DELAY_MS * 2 ** reconnectAttempts;
				reconnectAttempts++;
				setConnectionState("reconnecting");
				reconnectTimer = setTimeout(() => connect(), delay);
			} else {
				setConnectionState("disconnected");
			}
		};

		ws.onerror = () => {
			// onclose will fire after onerror, handling reconnect there
		};
	}

	function send(message: Record<string, unknown>): boolean {
		if (ws?.readyState === WebSocket.OPEN) {
			ws.send(JSON.stringify(message));
			return true;
		}

		return false;
	}

	function reconnect() {
		intentionalClose = false;
		reconnectAttempts = 0;
		if (reconnectTimer) {
			clearTimeout(reconnectTimer);
			reconnectTimer = null;
		}
		void connect();
	}

	function close() {
		intentionalClose = true;
		if (reconnectTimer) {
			clearTimeout(reconnectTimer);
			reconnectTimer = null;
		}
		ws?.close(1000);
		ws = null;
		setConnectionState("disconnected");
	}

	async function refreshToken() {
		const token = await getAccessToken();
		if (token) {
			send({ type: ClientEvent.RefreshToken, token });
			return;
		}

		handleSessionExpired();
	}

	connect();

	return {
		connectionState: { subscribe: connectionState.subscribe },
		send,
		reconnect,
		close,
		refreshToken,
	};
}
