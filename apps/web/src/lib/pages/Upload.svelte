<script lang="ts">
import { imagesService } from "$lib/domains/images/api/images.service";
import {
	MISSING_GPS_MESSAGE,
	fileHasGpsExif,
	mapServerUploadError,
} from "$lib/domains/images/exifPreflight";
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

let environment: "indoor" | "outdoor" = "outdoor";
let selectedFile: File | null = null;
let preflightOk: boolean | null = null;
let preflightPending = false;
let preflightError = "";
let submitting = false;

let fileInput: HTMLInputElement;

async function onFileSelected(event: Event) {
	const input = event.currentTarget as HTMLInputElement;
	const file = input.files?.[0];
	preflightError = "";
	preflightOk = null;
	selectedFile = null;

	if (!file) return;

	const ext = file.name.includes(".") ? `.${file.name.split(".").pop()?.toLowerCase()}` : "";
	const allowed = [".jpg", ".jpeg", ".png", ".heic"];
	if (!allowed.includes(ext)) {
		preflightError = "Use a JPEG, PNG, or HEIC photo.";
		input.value = "";
		return;
	}

	selectedFile = file;
	preflightPending = true;
	try {
		const ok = await fileHasGpsExif(file);
		preflightOk = ok;
		if (!ok) preflightError = MISSING_GPS_MESSAGE;
	} catch {
		preflightOk = false;
		preflightError = "Could not read this file. Try another photo.";
	} finally {
		preflightPending = false;
	}
}

async function submit() {
	if (!selectedFile || !preflightOk || submitting) return;
	submitting = true;
	try {
		await imagesService.submitSubmission(selectedFile, environment);
		toast.success("Thanks — we'll review your photo before it appears in games.");
		selectedFile = null;
		preflightOk = null;
		preflightError = "";
		if (fileInput) fileInput.value = "";
	} catch (e: unknown) {
		const msg = e instanceof Error ? mapServerUploadError(e.message) : "Upload failed.";
		toast.error(msg);
	} finally {
		submitting = false;
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
			</p>

			<div class="toggle-bar">
				<TogglePills
					ariaLabel="Photo environment"
					selected={environment}
					options={environmentOptions}
					on:change={(event) => {
						if (event.detail === "indoor" || event.detail === "outdoor") {
							environment = event.detail;
						}
					}}
				/>
			</div>

			<div class="field">
				<label class="file-label" for="photo-upload">Photo file</label>
				<input
					id="photo-upload"
					bind:this={fileInput}
					class="file-input"
					type="file"
					accept="image/jpeg,image/png,image/heic,.heic,.jpg,.jpeg"
					on:change={onFileSelected}
				/>
			</div>

			{#if preflightPending}
				<p class="status status--muted">Checking location data in your photo…</p>
			{:else if preflightOk === true && selectedFile}
				<p class="status status--ok">Location data found. Ready to upload.</p>
			{:else if preflightError}
				<p class="status status--err" role="alert">{preflightError}</p>
			{/if}

			<button
				class="btn-3d submit-btn"
				type="button"
				disabled={!selectedFile || preflightOk !== true || submitting}
				on:click={submit}
			>
				{submitting ? "Uploading…" : "Submit for review"}
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

	.submit-btn {
		margin-top: 18px;
		width: 100%;
	}

	:global(.card) {
		padding: 18px;
	}
</style>
