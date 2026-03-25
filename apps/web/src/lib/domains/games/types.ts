export type Environment = "indoor" | "outdoor" | "any";
export type Difficulty = "easy" | "medium" | "hard";

export const DEFAULT_DIFFICULTY: Difficulty = "medium";

export interface GameMode {
	timed: boolean;
	environment: Environment;
	daily: boolean;
	difficulty: Difficulty;
}

export interface RoundTileLevel {
	level: number;
	width: number;
	height: number;
	cols: number;
	rows: number;
}

export interface RoundPanoData {
	fullWidth: number;
	fullHeight: number;
	croppedWidth: number;
	croppedHeight: number;
	croppedX: number;
	croppedY: number;
}

export interface RoundTiles {
	version: number;
	baseUrl: string;
	tileUrlTemplate: string;
	originalWidth: number;
	originalHeight: number;
	aspectRatio: number;
	basePanoData: RoundPanoData;
	levels: RoundTileLevel[];
}

export interface Round {
	roundId: number;
	imageId: string;
	imageUrl: string;
	imageTiles: RoundTiles | null;
	actual: { lat: number; lng: number } | null;
	guess: { lat: number; lng: number } | null;
	distanceMeters: number | null;
	score: number | null;
	startedAt: string | null;
	expiresAt: string | null;
	guessedAt: string | null;
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

export interface ScoreDistribution {
	percentile: number;
	histogram: number[];
}
