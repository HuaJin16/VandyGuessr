<script lang="ts">
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

let fileInput: HTMLInputElement;

$: readyFiles = selectedFiles.filter((item) => item.preflightOk === true);
$: rejectedFiles = selectedFiles.filter((item) => item.preflightOk === false);
$: canSubmit = !preflightPending && !submitting && readyFiles.length > 0;

function pluralizePhoto(count: number): string {
	return `${count} photo${count === 1 ? "" : "s"}`;
}

async function onFileSelected(event: Event) {
	const input = event.currentTarget as HTMLInputElement;
	const files = Array.from(input.files ?? []);
	const runId = ++selectionRunId;
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

	for (let i = 0; i < nextFiles.length; i += 1) {
		if (selectionRunId !== runId) return;

		const current = nextFiles[i];
		const result = await preflightUploadFile(current.file);
		if (selectionRunId !== runId) return;

		nextFiles[i] = {
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
		batchSummary = await submitUploadBatch({
			items: filesToSubmit,
			environment,
			onProgress: ({ current, total }) => {
				submitProgressCurrent = current;
				submitProgressTotal = total;
			},
		});

		if (batchSummary.failed === 0) {
			toast.success(
				`Thanks — ${pluralizePhoto(batchSummary.queued)} queued for background processing.`,
			);
		} else if (batchSummary.queued > 0) {
			toast.warning(`${batchSummary.queued} queued, ${batchSummary.failed} failed.`);
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

const unsub = auth.subscribe((a) => {
	if (a.isInitialized && a.account === null) navigate("/login", { replace: true });
});
onDestroy(unsub);
</script>

<div class="min-h-screen bg-canvas font-sans text-ink">
	<Navbar />

	<main class="main">
		<section class="card">
			<p class="section-label">Contribute</p>
			<h1>Upload a campus photo</h1>
			<p class="desc">
				Photos are reviewed before they can appear in rounds. Your image must include embedded GPS
				from when it was taken—enable location in your camera app. Screenshots usually won't work.
				After you submit, uploads are queued and processed in the background.
			</p>

			<div class="toggle-bar" class:toggle-bar--disabled={submitting}>
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
				<label class="file-label" for="photo-upload">Photo files</label>
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

			{#if preflightPending}
				<p class="status status--muted">
					Checking location data in {pluralizePhoto(selectedFiles.length)}…
				</p>
			{:else if selectedFiles.length}
				{#if readyFiles.length > 0}
					<p class="status status--ok">
						{readyFiles.length} ready to upload
						{#if rejectedFiles.length > 0}
							, {rejectedFiles.length} failed pre-check
						{/if}
						.
					</p>
				{:else}
					<p class="status status--err" role="alert">No selected photos are uploadable yet.</p>
				{/if}

				{#if rejectedFiles.length > 0}
					<ul class="status-list" role="alert">
						{#each rejectedFiles as item (item.id)}
							<li>
								<span class="status-file">{item.file.name}</span>{item.preflightError}
							</li>
						{/each}
					</ul>
				{/if}
			{/if}

			{#if batchSummary}
				<section
					class="result-summary"
					data-tone={batchSummary.failed === 0 ? "success" : batchSummary.queued > 0 ? "warn" : "error"}
				>
					<p class="result-title">
						Queueing complete: {batchSummary.queued} queued, {batchSummary.failed} failed out of
						{batchSummary.total}.
					</p>
					{#if batchSummary.failures.length > 0}
						<ul class="status-list">
							{#each batchSummary.failures as failure (failure.id)}
								<li>
									<span class="status-file">{failure.filename}</span>{failure.reason}
								</li>
							{/each}
						</ul>
					{/if}
				</section>
			{/if}

			<button
				class="btn-3d submit-btn"
				type="button"
				disabled={!canSubmit}
				on:click={submit}
			>
				{submitting
					? submitProgressTotal > 0
						? `Queueing ${submitProgressCurrent}/${submitProgressTotal}…`
						: "Queueing…"
					: "Submit for review"}
			</button>
		</section>
	</main>
</div>

<style>
	.main {
		width: min(560px, calc(100% - 32px));
		margin: 16px auto 32px;
	}

	.section-label {
		margin: 0;
		color: var(--muted);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	h1 {
		margin: 8px 0 0;
		font-size: 26px;
		font-weight: 800;
		line-height: 1.15;
	}

	.desc {
		margin: 10px 0 0;
		color: var(--muted);
		font-size: 15px;
		line-height: 1.45;
	}

	.toggle-bar {
		display: flex;
		gap: 10px;
		margin-top: 16px;
		flex-wrap: wrap;
	}

	.toggle-bar--disabled {
		pointer-events: none;
		opacity: 0.65;
	}

	.field {
		margin-top: 18px;
	}

	.file-label {
		display: block;
		font-size: 14px;
		font-weight: 600;
		margin-bottom: 8px;
	}

	.file-input {
		width: 100%;
		font-size: 14px;
	}

	.status {
		margin: 14px 0 0;
		font-size: 14px;
		line-height: 1.45;
	}

	.status-list {
		margin: 8px 0 0;
		padding-left: 18px;
		display: grid;
		gap: 6px;
		font-size: 13px;
		color: var(--muted);
	}

	.status-file {
		font-weight: 600;
		color: var(--ink);
		margin-right: 6px;
	}

	.status--muted {
		color: var(--muted);
	}

	.status--ok {
		color: var(--brand-dark);
		font-weight: 600;
	}

	.status--err {
		color: var(--danger, #b00020);
	}

	.result-summary {
		margin-top: 14px;
		padding: 12px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
	}

	.result-summary[data-tone="success"] {
		border-color: color-mix(in srgb, var(--success) 35%, var(--line));
		background: color-mix(in srgb, var(--success-light) 35%, var(--surface));
	}

	.result-summary[data-tone="warn"] {
		border-color: color-mix(in srgb, var(--warning-ink) 25%, var(--line));
		background: color-mix(in srgb, var(--warning-light) 72%, var(--surface));
	}

	.result-summary[data-tone="error"] {
		border-color: color-mix(in srgb, var(--danger) 35%, var(--line));
		background: color-mix(in srgb, var(--danger-light) 55%, var(--surface));
	}

	.result-title {
		margin: 0;
		font-size: 14px;
		font-weight: 600;
	}

	.submit-btn {
		margin-top: 18px;
		width: 100%;
	}

	:global(.card) {
		padding: 18px;
	}
</style>
