import type { RoundTiles } from "$lib/domains/games/types";

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

export interface SubmissionJobItem {
	id: string;
	filename: string;
	jobId: string;
	status: "queued" | "processing" | "completed" | "failed";
	processingStage: string | null;
	attempts: number;
	error: string;
}

export interface BatchSubmissionSummary {
	total: number;
	queued: number;
	failed: number;
	failures: SubmissionFailure[];
	jobs: SubmissionJobItem[];
}

export interface SubmissionJobAcceptedResponse {
	jobId: string;
	status: "queued";
}

export interface SubmissionJobStatusResponse {
	jobId: string;
	status: "queued" | "processing" | "completed" | "failed";
	filename: string | null;
	environment: UploadEnvironment;
	error: string | null;
	attempts: number;
	processingStage: string | null;
	imageId: string | null;
	imageUrl: string | null;
	createdAt: string;
	startedAt: string | null;
	heartbeatAt: string | null;
	completedAt: string | null;
	updatedAt: string;
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
	thumbnail_url: string;
	latitude: number;
	longitude: number;
	environment: UploadEnvironment;
	location_name: string | null;
	created_at: string | null;
	tiles: RoundTiles | null;
}
