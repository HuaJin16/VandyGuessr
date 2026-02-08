/**
 * User types.
 */

export interface UserStats {
	gamesPlayed: number;
	totalPoints: number;
	avgScore: number;
	locationsDiscovered: number;
	rank?: number;
}

export interface User {
	id: string;
	email: string;
	username: string;
	name: string;
	avatar_url: string | null;
	stats?: UserStats;
}

export interface UpdateProfileDto {
	username?: string;
	name?: string;
	avatar_url?: string | null;
}
