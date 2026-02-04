/**
 * User types.
 */

export interface User {
	id: string;
	email: string;
	username: string;
	name: string;
	avatar_url: string | null;
}

export interface UpdateProfileDto {
	username?: string;
	name?: string;
	avatar_url?: string | null;
}
