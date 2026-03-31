/**
 * User types.
 */

export interface User {
	id: string;
	email: string;
	username: string;
	name: string;
	avatar_url: string | null;
	can_review_submissions: boolean;
}

export interface UpdateProfileRequest {
	name: string;
}
