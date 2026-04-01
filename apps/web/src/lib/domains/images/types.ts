export type UploadEnvironment = "indoor" | "outdoor";
export type TourEnvironment = UploadEnvironment | "any";

export interface UploadSelectionItem {
	id: string;
	file: File;
	preflightOk: boolean | null;
	preflightError: string;
}

export interface UploadFilePreflightResult {
	preflightOk: boolean;
	preflightError: string;
}

export interface SubmissionFailure {
	id: string;
	filename: string;
	reason: string;
}

export interface BatchSubmissionSummary {
	total: number;
	queued: number;
	failed: number;
	failures: SubmissionFailure[];
}

export interface SubmissionJobAcceptedResponse {
	jobId: string;
	status: "queued";
}

export interface PendingSubmissionItem {
	id: string;
	url: string;
	latitude: number;
	longitude: number;
	environment: UploadEnvironment;
	location_name: string | null;
	original_filename: string | null;
	created_at: string;
	submitter_name: string | null;
	submitter_email: string | null;
}

export interface TourImageItem {
	id: string;
	url: string;
	latitude: number;
	longitude: number;
	environment: UploadEnvironment;
	location_name: string | null;
	created_at: string | null;
}
