<script lang="ts">
import RoundPreviewOverlay from "$lib/domains/games/components/RoundPreviewOverlay.svelte";
import { imagesService } from "$lib/domains/images/api/images.service";
import { imageQueries } from "$lib/domains/images/queries/images.queries";
import { ApiRequestError } from "$lib/shared/api/types";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import { createQuery, useQueryClient } from "@tanstack/svelte-query";
import { onDestroy } from "svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

const queryClient = useQueryClient();

let previewOpen = false;
let previewUrl = "";

function openPreview(url: string) {
	previewUrl = url;
	previewOpen = true;
}

function closePreview() {
	previewOpen = false;
	previewUrl = "";
}

$: pending = createQuery({
	...imageQueries.pendingModeration(),
	enabled: $auth.isInitialized,
});

let actingId: string | null = null;

async function approve(id: string) {
	actingId = id;
	try {
		await imagesService.approveSubmission(id);
		toast.success("Approved");
		await queryClient.invalidateQueries({ queryKey: ["images", "moderation", "pending"] });
	} catch (e: unknown) {
		const msg = e instanceof ApiRequestError ? e.message : "Could not approve";
		toast.error(msg);
	} finally {
		actingId = null;
	}
}

async function reject(id: string) {
	if (!confirm("Reject this submission? It will not appear in games.")) return;
	actingId = id;
	try {
		await imagesService.rejectSubmission(id);
		toast.warning("Rejected");
		await queryClient.invalidateQueries({ queryKey: ["images", "moderation", "pending"] });
	} catch (e: unknown) {
		const msg = e instanceof ApiRequestError ? e.message : "Could not reject";
		toast.error(msg);
	} finally {
		actingId = null;
	}
}

const unsub = auth.subscribe((a) => {
	if (a.isInitialized && a.account === null) navigate("/login", { replace: true });
});
onDestroy(unsub);
</script>

<div class="min-h-screen bg-canvas font-sans text-ink">
	<Navbar activePage="review" />

	<RoundPreviewOverlay open={previewOpen} imageUrl={previewUrl} onClose={closePreview} />

	<main class="main">
		<section class="card header-card">
			<p class="section-label">Moderation</p>
			<h1>Review submissions</h1>
			<p class="desc">Approve photos to add them to random, daily, and multiplayer pools.</p>
		</section>

		{#if $pending.isPending}
			<section class="card state-card">
				<p class="muted state-msg">Loading submissions…</p>
			</section>
		{:else if $pending.isError}
			<section class="card state-card state-card--error" role="alert">
				<p class="err state-msg">
					{$pending.error instanceof ApiRequestError && $pending.error.status === 403
						? "You don't have access to this page."
						: "Could not load submissions."}
				</p>
			</section>
		{:else if !$pending.data?.length}
			<section class="card empty-card">
				<p class="empty-title">No pending submissions</p>
				<p class="muted">You're all caught up.</p>
			</section>
		{:else}
			<ul class="list">
				{#each $pending.data as item (item.id)}
					<li class="card item-card">
						<button
							type="button"
							class="thumb-wrap"
							aria-label="Preview how this photo appears in a round"
							on:click={() => openPreview(item.url)}
						>
							<img class="thumb" src={item.url} alt="" loading="lazy" />
						</button>
						<div class="meta">
							<p class="env-pill" data-env={item.environment}>
								{item.environment === "outdoor" ? "Outdoor" : "Indoor"}
							</p>
							{#if item.location_name}
								<p class="loc">{item.location_name}</p>
							{/if}
							{#if item.submitter_name || item.submitter_email}
								<p class="submitter">
									{item.submitter_name || "Unknown"}
									{#if item.submitter_email}
										<span class="email"> · {item.submitter_email}</span>
									{/if}
								</p>
							{/if}
							<p class="date">
								{new Date(item.created_at).toLocaleString()}
							</p>
							<div class="actions">
								<button
									type="button"
									class="btn-ghost action-preview"
									disabled={actingId !== null}
									on:click={() => openPreview(item.url)}
								>
									Preview as round
								</button>
								<div class="actions-primary">
									<button
										type="button"
										class="btn-3d btn-approve"
										disabled={actingId !== null}
										on:click={() => approve(item.id)}
									>
										{actingId === item.id ? "…" : "Approve"}
									</button>
									<button
										type="button"
										class="btn-3d btn-3d--danger btn-reject"
										disabled={actingId !== null}
										on:click={() => reject(item.id)}
									>
										Reject
									</button>
								</div>
							</div>
						</div>
					</li>
				{/each}
			</ul>
		{/if}
	</main>
</div>

<style>
	.main {
		width: min(720px, calc(100% - 32px));
		margin: 16px auto 32px;
		display: grid;
		gap: 14px;
	}

	.state-card {
		margin: 0;
	}

	.state-msg {
		margin: 0;
		text-align: center;
		padding: 8px 0;
	}

	.state-card--error {
		border-color: color-mix(in srgb, var(--danger) 35%, var(--line));
		background: color-mix(in srgb, var(--danger-light) 55%, var(--surface));
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
		margin: 8px 0 0;
		color: var(--muted);
		font-size: 15px;
		line-height: 1.45;
	}

	.muted {
		margin: 0;
		color: var(--muted);
		font-size: 15px;
	}

	.err {
		margin: 0;
		color: var(--danger-ink);
		font-size: 15px;
	}

	.empty-title {
		margin: 0;
		font-weight: 700;
		font-size: 16px;
	}

	.list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 14px;
	}

	.item-card {
		display: grid;
		grid-template-columns: minmax(0, 140px) 1fr;
		gap: 14px;
		align-items: start;
	}

	@media (max-width: 520px) {
		.item-card {
			grid-template-columns: 1fr;
		}
	}

	.thumb-wrap {
		display: block;
		width: 100%;
		padding: 0;
		margin: 0;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		overflow: hidden;
		background: var(--surface);
		aspect-ratio: 4 / 3;
		cursor: pointer;
		text-align: left;
		font: inherit;
		color: inherit;
	}

	.thumb-wrap:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.thumb-wrap:hover {
		border-color: var(--brand);
	}

	.thumb {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
	}

	.meta {
		min-width: 0;
	}

	.env-pill {
		margin: 0;
		display: inline-flex;
		align-items: center;
		width: fit-content;
		padding: 4px 10px;
		border-radius: var(--radius-pill);
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.env-pill[data-env="outdoor"] {
		background: var(--success-light);
		color: var(--success-ink);
	}

	.env-pill[data-env="indoor"] {
		background: var(--brand-light);
		color: var(--brand-dark);
	}

	.loc {
		margin: 4px 0 0;
		font-weight: 600;
		font-size: 15px;
	}

	.submitter {
		margin: 6px 0 0;
		font-size: 14px;
	}

	.email {
		color: var(--muted);
	}

	.date {
		margin: 4px 0 0;
		font-size: 13px;
		color: var(--muted);
	}

	.actions {
		display: flex;
		flex-wrap: wrap;
		align-items: stretch;
		gap: 10px;
		margin-top: 14px;
	}

	.action-preview {
		flex: 0 0 auto;
		padding: 12px 18px;
		font-size: 14px;
		align-self: center;
	}

	.actions-primary {
		display: flex;
		flex: 1 1 200px;
		gap: 10px;
		min-width: 0;
	}

	.btn-approve,
	.btn-reject {
		flex: 1;
		min-width: 0;
		padding: 12px 16px;
		font-size: 14px;
	}

	:global(.header-card),
	:global(.empty-card),
	:global(.item-card) {
		padding: 18px;
	}

	:global(.header-card) {
		border-color: color-mix(in srgb, var(--brand) 28%, var(--line));
	}
</style>
