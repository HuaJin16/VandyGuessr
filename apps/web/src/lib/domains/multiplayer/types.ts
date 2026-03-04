export type MultiplayerGameStatus = "waiting" | "active" | "completed" | "cancelled" | "abandoned";

export type PlayerStatus = "connected" | "disconnected" | "forfeited";

export type Environment = "indoor" | "outdoor" | "any";

export type ConnectionState = "connecting" | "connected" | "disconnected" | "reconnecting";

export type MultiplayerPhase = "lobby" | "playing" | "results" | "game_over";

export type LobbyStatus = "waiting" | "starting" | "cancelled";

export interface MultiplayerMode {
	environment: Environment;
}

export interface MultiplayerPlayer {
	userId: string;
	name: string;
	avatarUrl: string | null;
	totalScore: number;
	status: PlayerStatus;
	joinedAt: string;
}

export interface MultiplayerGuess {
	lat: number;
	lng: number;
	distanceMeters: number;
	score: number;
	submittedAt: string;
}

export interface MultiplayerRound {
	roundId: number;
	imageUrl: string | null;
	actual: { lat: number; lng: number } | null;
	locationName: string | null;
	startedAt: string | null;
	expiresAt: string | null;
	guesses: Record<string, MultiplayerGuess> | null;
}

export interface MultiplayerGame {
	id: string;
	hostId: string;
	inviteCode: string;
	status: MultiplayerGameStatus;
	mode: MultiplayerMode;
	players: MultiplayerPlayer[];
	rounds: MultiplayerRound[];
	currentRound: number;
	createdAt: string;
	startedAt: string | null;
	lastActivityAt: string;
}

export interface CreateMultiplayerRequest {
	environment?: Environment;
}

export interface JoinMultiplayerRequest {
	code: string;
}

export interface RoundPlayerResult {
	userId: string;
	name: string;
	score: number;
	distanceMeters: number | null;
	guess: { lat: number; lng: number } | null;
}

export interface Standing {
	userId: string;
	name: string;
	totalScore: number;
	rank: number;
}

export interface RoundResult {
	round: number;
	results: RoundPlayerResult[];
	actual: { lat: number; lng: number };
	locationName: string | null;
	standings: Standing[];
}

export interface PreviousRound {
	round: number;
	score: number;
	distanceMeters: number | null;
}

export interface GameStatePayload {
	status: MultiplayerGameStatus;
	currentRound: number;
	round: {
		round: number;
		imageUrl: string;
		expiresAt: string | null;
	} | null;
	playersGuessed: string[];
	hasGuessedThisRound: boolean;
	players: Array<{
		userId: string;
		name: string;
		status: PlayerStatus;
		totalScore: number;
	}>;
	previousRounds: PreviousRound[];
}

export enum ClientEvent {
	SubmitGuess = "submit_guess",
	StartGame = "start_game",
	Forfeit = "forfeit",
	RefreshToken = "refresh_token",
	ExtendLobby = "extend_lobby",
	LeaveLobby = "leave_lobby",
}

export enum ServerEvent {
	PlayerJoined = "player_joined",
	PlayerLeft = "player_left",
	GameStarting = "game_starting",
	GameCancelled = "game_cancelled",
	LobbyExpiring = "lobby_expiring",
	RoundStart = "round_start",
	PlayerGuessed = "player_guessed",
	GuessAccepted = "guess_accepted",
	RoundResult = "round_result",
	GameOver = "game_over",
	PlayerDisconnected = "player_disconnected",
	PlayerReconnected = "player_reconnected",
	PlayerForfeited = "player_forfeited",
	GameState = "game_state",
	TokenExpiring = "token_expiring",
	Error = "error",
}

export interface ServerMessage {
	type: ServerEvent;
	[key: string]: unknown;
}

export interface PlayerJoinedMessage {
	type: ServerEvent.PlayerJoined;
	player: { userId: string; name: string; avatarUrl: string | null };
	playerCount: number;
}

export interface PlayerLeftMessage {
	type: ServerEvent.PlayerLeft;
	userId: string;
	playerCount: number;
}

export interface GameStartingMessage {
	type: ServerEvent.GameStarting;
	countdown: number;
}

export interface GameCancelledMessage {
	type: ServerEvent.GameCancelled;
	reason: string;
}

export interface RoundStartMessage {
	type: ServerEvent.RoundStart;
	round: number;
	imageUrl: string;
	expiresAt: string;
}

export interface PlayerGuessedMessage {
	type: ServerEvent.PlayerGuessed;
	userId: string;
	remainingPlayers: number;
}

export interface GuessAcceptedMessage {
	type: ServerEvent.GuessAccepted;
	round: number;
}

export interface RoundResultMessage {
	type: ServerEvent.RoundResult;
	round: number;
	results: RoundPlayerResult[];
	actual: { lat: number; lng: number };
	locationName: string | null;
	standings: Standing[];
}

export interface GameOverRound {
	round: number;
	results: RoundPlayerResult[];
	actual: { lat: number; lng: number };
	locationName: string | null;
}

export interface GameOverMessage {
	type: ServerEvent.GameOver;
	winnerId: string;
	standings: Standing[];
	rounds: GameOverRound[];
}

export interface PlayerDisconnectedMessage {
	type: ServerEvent.PlayerDisconnected;
	userId: string;
	reconnectDeadline: string;
}

export interface PlayerReconnectedMessage {
	type: ServerEvent.PlayerReconnected;
	userId: string;
}

export interface PlayerForfeitedMessage {
	type: ServerEvent.PlayerForfeited;
	userId: string;
}

export interface GameStateMessage {
	type: ServerEvent.GameState;
	status: MultiplayerGameStatus;
	currentRound: number;
	round: { round: number; imageUrl: string; expiresAt: string | null } | null;
	playersGuessed: string[];
	hasGuessedThisRound: boolean;
	players: Array<{
		userId: string;
		name: string;
		status: PlayerStatus;
		totalScore: number;
	}>;
	previousRounds: PreviousRound[];
}

export interface ErrorMessage {
	type: ServerEvent.Error;
	code: string;
	message: string;
}
