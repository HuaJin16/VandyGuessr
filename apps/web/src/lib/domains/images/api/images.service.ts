/**
 * Crowd image submissions and moderation API.
 */

import { apiClient } from "$lib/shared/api/client";
import { getAuthToken } from "$lib/shared/auth/token";
import type {
	PendingSubmissionItem,
	SubmissionJobAcceptedResponse,
	SubmissionJobStatusResponse,
	TourEnvironment,
	TourImageItem,
	UploadEnvironment,
} from "../types";

const apiBase = () => import.meta.env.VITE_API_URL || "http://localhost:8000";

export const imagesService = {
	submitSubmission: async (
		file: File,
		environment: UploadEnvironment,
	): Promise<SubmissionJobAcceptedResponse> => {
		const token = await getAuthToken();
		const body = new FormData();
		body.append("file", file);
		const url = `${apiBase()}/v1/images/submissions?environment=${environment}`;
		const res = await fetch(url, {
			method: "POST",
			headers: token ? { Authorization: `Bearer ${token}` } : {},
			body,
		});
		const data = (await res.json().catch(() => ({}))) as {
			detail?: string;
		} & Partial<SubmissionJobAcceptedResponse>;
		if (!res.ok) {
			throw new Error(typeof data.detail === "string" ? data.detail : "Upload failed");
		}
		return data as SubmissionJobAcceptedResponse;
	},

	getSubmissionStatus: async (jobId: string): Promise<SubmissionJobStatusResponse> => {
		const token = await getAuthToken();
		const url = `${apiBase()}/v1/images/submissions/${jobId}`;
		const res = await fetch(url, {
			headers: token ? { Authorization: `Bearer ${token}` } : {},
		});
		const data = (await res.json().catch(() => ({}))) as {
			detail?: string;
		} & Partial<SubmissionJobStatusResponse>;
		if (!res.ok) {
			throw new Error(
				typeof data.detail === "string" ? data.detail : "Could not fetch upload status",
			);
		}
		return data as SubmissionJobStatusResponse;
	},

	listPendingModeration: () =>
		apiClient
			.get<{ items: PendingSubmissionItem[] }>("/v1/images/moderation/pending")
			.then((r) => r.data.items),

	listTour: (environment: TourEnvironment) =>
		apiClient
			.get<{ items: TourImageItem[] }>("/v1/images/tour", {
				params: environment === "any" ? undefined : { environment },
			})
			.then((r) => r.data.items),

	approveSubmission: (id: string) => apiClient.post(`/v1/images/moderation/${id}/approve`),

	rejectSubmission: (id: string) => apiClient.post(`/v1/images/moderation/${id}/reject`),
};
