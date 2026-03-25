export interface CrowdSubmissionResponse {
	id: string;
	url: string;
	latitude: number;
	longitude: number;
	environment: "indoor" | "outdoor";
}

export interface PendingSubmissionItem {
	id: string;
	url: string;
	latitude: number;
	longitude: number;
	environment: "indoor" | "outdoor";
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
	environment: "indoor" | "outdoor";
	location_name: string | null;
	created_at: string | null;
}
