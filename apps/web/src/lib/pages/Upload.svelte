<script lang="ts">
import { imagesService } from "$lib/domains/images/api/images.service";
import { preflightUploadFile } from "$lib/domains/images/exifPreflight";
import { submitUploadBatch } from "$lib/domains/images/submissionFlow";
import type {
	BatchSubmissionSummary,
	UploadEnvironment,
	UploadSelectionItem,
} from "$lib/domains/images/types";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import TogglePills from "$lib/shared/components/TogglePills.svelte";
import type { ToggleOption } from "$lib/shared/components/TogglePills.svelte";
import Button from "$lib/shared/ui/Button.svelte";
import Card from "$lib/shared/ui/Card.svelte";
import PageHeader from "$lib/shared/ui/PageHeader.svelte";
import PageShell from "$lib/shared/ui/PageShell.svelte";
import StateBlock from "$lib/shared/ui/StateBlock.svelte";
import { Camera, FileWarning, MapPinned, Upload as UploadIcon } from "lucide-svelte";
import { onDestroy } from "svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

const environmentOptions = [
	{ value: "outdoor", label: "Outdoor" },
	{ value: "indoor", label: "Indoor" },
] satisfies ToggleOption[];

let environment: UploadEnvironment = "outdoor";
let selectedFiles: UploadSelectionItem[] = [];
let preflightPending = false;
let submitting = false;
let submitProgressCurrent = 0;
let submitProgressTotal = 0;
let batchSummary: BatchSubmissionSummary | null = null;
let selectionRunId = 0;
let jobTrackingRunId = 0;

let fileInput: HTMLInputElement;

$: readyFiles = selectedFiles.filter((item) => item.preflightOk === true);
$: rejectedFiles = selectedFiles.filter((item) => item.preflightOk === false);
$: canSubmit = !preflightPending && !submitting && readyFiles.length > 0;
$: trackedJobs = batchSummary?.jobs ?? [];
$: trackedQueued = trackedJobs.filter((job) => job.status === "queued").length;
$: trackedProcessing = trackedJobs.filter((job) => job.status === "processing").length;
$: trackedCompleted = trackedJobs.filter((job) => job.status === "completed").length;
$: trackedFailed = trackedJobs.filter((job) => job.status === "failed").length;
$: totalBatchFailures = (batchSummary?.failures.length ?? 0) + trackedFailed;

function sleep(ms: number): Promise<void> {
	return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function stageLabel(status: string, processingStage: string | null, error: string): string {
	if (status === "failed") return error || "Processing failed.";
	if (status === "completed") return "Fully processed and waiting for review.";
	if (status === "queued") return "Queued for worker pickup.";
	if (processingStage === "claimed") return "Worker claimed the upload.";
	if (processingStage === "downloading_temp") return "Downloading the temporary upload.";
	if (processingStage === "validating_image") return "Validating panorama metadata.";
	if (processingStage === "generating_tiles") return "Generating progressive panorama tiles.";
	if (processingStage === "generating_thumbnail") return "Generating the thumbnail preview.";
	if (processingStage === "compressing_original") return "Compressing the stored original.";
	if (processingStage === "uploading_original") return "Uploading the processed original.";
	if (processingStage === "resolving_location") return "Resolving the nearest campus location.";
	if (processingStage === "persisting_image") return "Persisting final image metadata.";
	if (processingStage === "finalizing") return "Finalizing the submission record.";
	return "Processing panorama.";
}

function updateTrackedJob(
	runId: number,
	jobId: string,
	updater: (job: BatchSubmissionSummary["jobs"][number]) => BatchSubmissionSummary["jobs"][number],
) {
	if (jobTrackingRunId !== runId || batchSummary === null) return;
	batchSummary = {
		...batchSummary,
		jobs: batchSummary.jobs.map((job) => (job.jobId === jobId ? updater(job) : job)),
	};
}

async function pollJobStatus(runId: number, jobId: string) {
	while (jobTrackingRunId === runId) {
		try {
			const status = await imagesService.getSubmissionStatus(jobId);
			updateTrackedJob(runId, jobId, (job) => ({
				...job,
				status: status.status,
				processingStage: status.processingStage,
				attempts: status.attempts,
				error: status.error ?? "",
			}));

			if (status.status === "completed" || status.status === "failed") return;
		} catch (error) {
			updateTrackedJob(runId, jobId, (job) => ({
				...job,
				error: error instanceof Error ? error.message : "Could not refresh upload status.",
			}));
		}

		await sleep(2000);
	}
}

async function trackBatchJobs(summary: BatchSubmissionSummary) {
	const runId = ++jobTrackingRunId;
	await Promise.all(summary.jobs.map((job) => pollJobStatus(runId, job.jobId)));
}

function pluralizePhoto(count: number): string {
	return `${count} photo${count === 1 ? "" : "s"}`;
}

async function onFileSelected(event: Event) {
	const input = event.currentTarget as HTMLInputElement;
	const files = Array.from(input.files ?? []);
	const runId = ++selectionRunId;
	jobTrackingRunId += 1;
	batchSummary = null;
	submitProgressCurrent = 0;
	submitProgressTotal = 0;

	if (!files.length) {
		selectedFiles = [];
		preflightPending = false;
		return;
	}

	const nextFiles: UploadSelectionItem[] = files.map((file, index) => ({
		id: `${file.name}-${file.size}-${file.lastModified}-${index}`,
		file,
		preflightOk: null,
		preflightError: "",
	}));

	selectedFiles = nextFiles;
	preflightPending = true;

	for (let index = 0; index < nextFiles.length; index += 1) {
		if (selectionRunId !== runId) return;

		const current = nextFiles[index];
		const result = await preflightUploadFile(current.file);
		if (selectionRunId !== runId) return;

		nextFiles[index] = {
			...current,
			...result,
		};

		selectedFiles = [...nextFiles];
	}

	if (selectionRunId === runId) preflightPending = false;
}

async function submit() {
	if (!canSubmit) return;

	submitting = true;
	batchSummary = null;

	try {
		const filesToSubmit = [...selectedFiles];
		const summary = await submitUploadBatch({
			items: filesToSubmit,
			environment,
			onProgress: ({ current, total }) => {
				submitProgressCurrent = current;
				submitProgressTotal = total;
			},
		});
		batchSummary = summary;
		void trackBatchJobs(summary);

		if (summary.failed === 0) {
			toast.success(`Thanks - ${pluralizePhoto(summary.queued)} queued for processing.`);
		} else if (summary.queued > 0) {
			toast.warning(`${summary.queued} queued, ${summary.failed} failed.`);
		} else {
			toast.error("No photos were queued. See details below.");
		}

		selectedFiles = [];
		preflightPending = false;
		if (fileInput) fileInput.value = "";
	} catch {
		toast.error("Upload failed. Please try again.");
	} finally {
		submitting = false;
		submitProgressCurrent = 0;
		submitProgressTotal = 0;
	}
}

const unsub = auth.subscribe((state) => {
	if (state.isInitialized && state.currentUserOid === null) navigate("/login", { replace: true });
});

onDestroy(unsub);
</script>

<div class="min-h-screen bg-canvas font-sans text-ink">
	<Navbar activePage="upload" />

	<PageShell size="wide">
		<PageHeader
			eyebrow="Contribute"
			title="Upload a campus photo"
			copy="Submit panoramas with GPS metadata so the playable image pool keeps growing. Uploads are reviewed before they appear in rounds."
		/>

		<section class="upload-grid">
			<Card class="upload-main">
				<div class="section-heading section-heading--compact">
					<p class="section-label">Submission</p>
					<h2>Choose files and set the environment</h2>
				</div>

				<div class={`control-wrap ${submitting ? "control-wrap--disabled" : ""}`}>
					<div class="control-group">
						<p class="control-label">Environment</p>
						<TogglePills
							ariaLabel="Photo environment"
							selected={environment}
							options={environmentOptions}
							on:change={(event) => {
								if (submitting) return;
								if (event.detail === "indoor" || event.detail === "outdoor") {
									environment = event.detail;
								}
							}}
						/>
					</div>

					<div class="field">
						<label class="control-label" for="photo-upload">Photo files</label>
						<div class="file-input-wrap">
							<input
								id="photo-upload"
								bind:this={fileInput}
								class="file-input"
								type="file"
								accept="image/jpeg,image/png,image/heic,.heic,.jpg,.jpeg"
								multiple
								disabled={submitting}
								on:change={onFileSelected}
							/>
						</div>
					</div>
				</div>

				{#if preflightPending}
					<StateBlock tone="soft" title="Checking EXIF metadata" copy={`Scanning ${pluralizePhoto(selectedFiles.length)} for location data before queueing.`} />
				{:else if selectedFiles.length}
					<div class="upload-status">
						{#if readyFiles.length > 0}
							<p class="upload-status__summary upload-status__summary--ok">
								{readyFiles.length} ready to upload{#if rejectedFiles.length > 0}, {rejectedFiles.length} failed pre-check{/if}.
							</p>
						{:else}
							<p class="upload-status__summary upload-status__summary--err">No selected photos are uploadable yet.</p>
						{/if}

						<div class="file-list">
							{#each selectedFiles as item (item.id)}
								<div class={`file-row ${item.preflightOk === false ? "file-row--error" : item.preflightOk === true ? "file-row--ready" : ""}`}>
									<div class="file-row__icon">
										{#if item.preflightOk === true}
											<MapPinned size={16} />
										{:else if item.preflightOk === false}
											<FileWarning size={16} />
										{:else}
											<Camera size={16} />
										{/if}
									</div>
									<div class="file-row__copy">
										<p class="file-row__name">{item.file.name}</p>
										<p class="file-row__meta">
											{#if item.preflightOk === true}
												Ready to queue
											{:else if item.preflightOk === false}
												{item.preflightError}
											{:else}
												Waiting for preflight
											{/if}
										</p>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				{#if batchSummary}
					<Card tone="subtle" class="result-card">
						<p class="result-card__title">
							Upload jobs: {trackedCompleted} completed, {trackedProcessing} processing, {trackedQueued} queued, {totalBatchFailures} failed out of {batchSummary.total}.
						</p>
						{#if batchSummary.failures.length > 0}
							<ul class="result-list">
								{#each batchSummary.failures as failure (failure.id)}
									<li>
										<span>{failure.filename}</span>
										{failure.reason}
									</li>
								{/each}
							</ul>
						{/if}
						{#if batchSummary.jobs.length > 0}
							<ul class="result-list result-list--jobs">
								{#each batchSummary.jobs as job (job.jobId)}
									<li>
										<span>{job.filename}</span>
										{job.status}: {stageLabel(job.status, job.processingStage, job.error)}
									</li>
								{/each}
							</ul>
						{/if}
					</Card>
				{/if}

				<Button class="w-full" size="lg" type="button" disabled={!canSubmit} on:click={submit}>
					<UploadIcon size={16} />
					<span>
						{submitting
							? submitProgressTotal > 0
								? `Queueing ${submitProgressCurrent}/${submitProgressTotal}...`
								: "Queueing..."
							: "Submit for review"}
					</span>
				</Button>
			</Card>

			<div class="upload-rail">
				<Card tone="subtle">
					<div class="section-heading section-heading--compact">
						<p class="section-label">Guidelines</p>
						<h2>What makes a good submission</h2>
					</div>
					<ul class="guidelines-list">
						<li>Use original panorama files, not screenshots or exports.</li>
						<li>GPS metadata must be embedded in the image.</li>
						<li>Indoor and outdoor tags should match the scene itself.</li>
						<li>Uploads are queued for background processing after submission.</li>
					</ul>
				</Card>

				<Card tone="subtle">
					<div class="section-heading section-heading--compact">
						<p class="section-label">Before you upload</p>
						<h2>Quick checklist</h2>
					</div>
					<div class="checklist">
						<div class="checklist__item"><span /> Photo opens correctly</div>
						<div class="checklist__item"><span /> GPS was enabled in camera settings</div>
						<div class="checklist__item"><span /> The environment tag is accurate</div>
					</div>
				</Card>
			</div>
		</section>
	</PageShell>
</div>

<style>
	.upload-grid {
		display: grid;
		gap: 20px;
	}

	.upload-main,
	.upload-rail {
		display: grid;
		gap: 18px;
	}

	.section-heading {
		display: grid;
		gap: 10px;
	}

	.section-heading--compact {
		gap: 8px;
	}

	.section-label,
	.control-label {
		margin: 0;
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	h2 {
		margin: 0;
		font-size: 24px;
		font-weight: 800;
		line-height: 1.1;
		letter-spacing: -0.03em;
	}

	.control-wrap {
		display: grid;
		gap: 18px;
	}

	.control-wrap--disabled {
		opacity: 0.7;
		pointer-events: none;
	}

	.control-group,
	.field {
		display: grid;
		gap: 10px;
	}

	.file-input-wrap {
		padding: 16px;
		border: 1px dashed var(--line-strong);
		border-radius: var(--radius-md);
		background: var(--surface-subtle);
	}

	.file-input {
		width: 100%;
		font-size: 14px;
	}

	.upload-status {
		display: grid;
		gap: 12px;
	}

	.upload-status__summary {
		margin: 0;
		font-size: 14px;
		font-weight: 700;
	}

	.upload-status__summary--ok {
		color: var(--brand-dark);
	}

	.upload-status__summary--err {
		color: var(--danger-ink);
	}

	.file-list {
		display: grid;
		gap: 10px;
	}

	.file-row {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr);
		gap: 12px;
		align-items: start;
		padding: 14px 16px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
	}

	.file-row--ready {
		border-color: color-mix(in srgb, var(--brand) 28%, var(--line));
		background: color-mix(in srgb, var(--brand-quiet) 60%, var(--surface));
	}

	.file-row--error {
		border-color: color-mix(in srgb, var(--danger) 28%, var(--line));
		background: color-mix(in srgb, var(--danger-light) 52%, var(--surface));
	}

	.file-row__icon {
		width: 32px;
		height: 32px;
		display: grid;
		place-items: center;
		border-radius: 999px;
		background: var(--surface-subtle);
		color: var(--muted);
	}

	.file-row__name,
	.file-row__meta,
	.result-card__title {
		margin: 0;
	}

	.file-row__name {
		font-size: 14px;
		font-weight: 700;
	}

	.file-row__meta {
		margin-top: 4px;
		font-size: 13px;
		line-height: 1.45;
		color: var(--muted);
	}

	.result-card {
		padding: 18px;
	}

	.result-card__title {
		font-size: 14px;
		font-weight: 700;
		line-height: 1.5;
	}

	.result-list,
	.guidelines-list {
		margin: 0;
		padding-left: 18px;
		display: grid;
		gap: 8px;
		font-size: 14px;
		line-height: 1.55;
		color: var(--muted);
	}

	.result-list--jobs {
		margin-top: 12px;
	}

	.result-list span {
		margin-right: 8px;
		font-weight: 700;
		color: var(--ink);
	}

	.checklist {
		display: grid;
		gap: 10px;
	}

	.checklist__item {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 14px;
		font-weight: 600;
		color: var(--ink);
	}

	.checklist__item span {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--brand);
		flex-shrink: 0;
	}

	@media (min-width: 960px) {
		.upload-grid {
			grid-template-columns: minmax(0, 1.3fr) minmax(300px, 0.8fr);
		}
	}
</style>
