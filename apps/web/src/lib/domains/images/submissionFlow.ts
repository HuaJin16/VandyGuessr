import { imagesService } from "./api/images.service";
import { mapServerUploadError } from "./exifPreflight";
import type {
	BatchSubmissionSummary,
	SubmissionFailure,
	UploadEnvironment,
	UploadSelectionItem,
} from "./types";

export interface UploadBatchProgress {
	current: number;
	total: number;
	filename: string;
}

export interface SubmitUploadBatchInput {
	items: UploadSelectionItem[];
	environment: UploadEnvironment;
	onProgress?: (progress: UploadBatchProgress) => void;
}

export async function submitUploadBatch({
	items,
	environment,
	onProgress,
}: SubmitUploadBatchInput): Promise<BatchSubmissionSummary> {
	const failures: SubmissionFailure[] = [];
	let succeeded = 0;

	for (const item of items) {
		if (item.preflightOk === true) continue;
		failures.push({
			id: item.id,
			filename: item.file.name,
			reason: item.preflightError || "Could not validate this photo.",
		});
	}

	const uploadCandidates = items.filter((item) => item.preflightOk === true);

	for (let i = 0; i < uploadCandidates.length; i += 1) {
		const item = uploadCandidates[i];
		onProgress?.({
			current: i + 1,
			total: uploadCandidates.length,
			filename: item.file.name,
		});

		try {
			await imagesService.submitSubmission(item.file, environment);
			succeeded += 1;
		} catch (e: unknown) {
			const reason = e instanceof Error ? mapServerUploadError(e.message) : "Upload failed.";
			failures.push({
				id: item.id,
				filename: item.file.name,
				reason,
			});
		}
	}

	return {
		total: items.length,
		succeeded,
		failed: failures.length,
		failures,
	};
}
