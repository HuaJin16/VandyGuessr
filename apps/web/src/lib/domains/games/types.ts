export type Environment = "indoor" | "outdoor" | "any";

export interface GameMode {
	timed: boolean;
	environment: Environment;
	daily: boolean;
}

export interface Round {
	roundId: number;
	imageId: string;
	imageUrl: string;
	actual: { lat: number; lng: number } | null;
	guess: { lat: number; lng: number } | null;
	distanceMeters: number | null;
	score: number | null;
	startedAt: string | null;
	expiresAt: string | null;
	skipped: boolean;
	location_name: string | null;
}

export type GameStatus = "active" | "completed" | "abandoned";

export interface Game {
	id: string;
	userId: string;
	mode: GameMode;
	status: GameStatus;
	rounds: Round[];
	totalScore: number;
	createdAt: string;
	lastActivityAt: string;
}

export interface StartGameRequest {
	mode: GameMode;
}
