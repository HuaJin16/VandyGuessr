/**
 * Common API types.
 */

export interface ApiError {
	message: string;
	status: number;
	detail?: string;
}

export class ApiRequestError extends Error {
	status: number;
	detail?: string;

	constructor(message: string, status: number, detail?: string) {
		super(message);
		this.name = "ApiRequestError";
		this.status = status;
		this.detail = detail;
	}
}
