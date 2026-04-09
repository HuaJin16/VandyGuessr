<script lang="ts">
import RoundPreviewOverlay from "$lib/domains/games/components/RoundPreviewOverlay.svelte";
import { imagesService } from "$lib/domains/images/api/images.service";
import { imageQueries } from "$lib/domains/images/queries/images.queries";
import { ApiRequestError } from "$lib/shared/api/types";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import Button from "$lib/shared/ui/Button.svelte";
import Card from "$lib/shared/ui/Card.svelte";
import PageHeader from "$lib/shared/ui/PageHeader.svelte";
import PageShell from "$lib/shared/ui/PageShell.svelte";
import StateBlock from "$lib/shared/ui/StateBlock.svelte";
import { createQuery, useQueryClient } from "@tanstack/svelte-query";
import { Eye, ShieldCheck } from "lucide-svelte";
import { onDestroy } from "svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

const queryClient = useQueryClient();

let previewOpen = false;
let previewUrl = "";
let actingId: string | null = null;

function openPreview(url: string) {
	previewUrl = url;
	previewOpen = true;
}

function closePreview() {
	previewOpen = false;
	previewUrl = "";
}

$: pending = createQuery({
	...imageQueries.pendingModeration($auth.currentUserOid),
	enabled: $auth.currentUserOid !== null,
});

async function approve(id: string) {
	actingId = id;
	try {
		await imagesService.approveSubmission(id);
		toast.success("Approved");
		await queryClient.invalidateQueries({ queryKey: ["images", "moderation", "pending"] });
	} catch (error: unknown) {
		const message = error instanceof ApiRequestError ? error.message : "Could not approve";
		toast.error(message);
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
	} catch (error: unknown) {
		const message = error instanceof ApiRequestError ? error.message : "Could not reject";
		toast.error(message);
	} finally {
		actingId = null;
	}
}

const unsub = auth.subscribe((state) => {
	if (state.isInitialized && state.currentUserOid === null) navigate("/login", { replace: true });
});

onDestroy(unsub);
</script>

<div class="min-h-screen bg-canvas font-sans text-ink">
	<Navbar activePage="review" />
	<RoundPreviewOverlay open={previewOpen} imageUrl={previewUrl} onClose={closePreview} />

	<PageShell size="content">
		<PageHeader
			eyebrow="Moderation"
			title="Review submissions"
			copy="Approve or reject queued panoramas so the solo, daily, and multiplayer image pools stay strong."
		>
			<div slot="actions">
				<div class="review-badge">
					<ShieldCheck size={15} />
					<span>Reviewer only</span>
				</div>
			</div>
		</PageHeader>

		{#if $pending.isPending}
			<StateBlock title="Loading submissions" copy="Pulling the moderation queue now." />
		{:else if $pending.isError}
			<StateBlock
				tone="error"
				title={$pending.error instanceof ApiRequestError && $pending.error.status === 403
					? "You don't have access to this page"
					: "Could not load submissions"}
				copy={$pending.error instanceof ApiRequestError && $pending.error.status === 403
					? "Only reviewers on the allowlist can see the moderation queue."
					: "Try the request again or head back home."}
			>
				{#if !($pending.error instanceof ApiRequestError && $pending.error.status === 403)}
					<Button type="button" on:click={() => $pending.refetch()}>Retry</Button>
				{/if}
				<Button variant="outline" type="button" on:click={() => navigate("/")}>Go home</Button>
			</StateBlock>
		{:else if !$pending.data?.length}
			<StateBlock tone="soft" title="No pending submissions" copy="You're all caught up. New uploads will appear here after they are queued and processed." />
		{:else}
			<ul class="review-list">
				{#each $pending.data as item (item.id)}
					<li>
						<Card class="review-row">
							<button
								type="button"
								class="review-thumb"
								aria-label="Preview how this photo appears in a round"
								on:click={() => openPreview(item.url)}
							>
								<img class="review-thumb__image" src={item.url} alt="" loading="lazy" />
							</button>

							<div class="review-row__content">
								<div class="review-row__meta">
									<p class={`env-pill env-pill--${item.environment}`}>
										{item.environment === "outdoor" ? "Outdoor" : "Indoor"}
									</p>
									{#if item.location_name}
										<p class="review-row__title">{item.location_name}</p>
									{/if}
									<p class="review-row__copy">
										{item.submitter_name || "Unknown"}
										{#if item.submitter_email}
											<span> · {item.submitter_email}</span>
										{/if}
									</p>
									<p class="review-row__copy">{new Date(item.created_at).toLocaleString()}</p>
								</div>

								<div class="review-row__actions">
									<Button variant="outline" type="button" disabled={actingId !== null} on:click={() => openPreview(item.url)}>
										<Eye size={15} />
										<span>Preview as round</span>
									</Button>
									<Button type="button" disabled={actingId !== null} on:click={() => approve(item.id)}>
										{actingId === item.id ? "Approving..." : "Approve"}
									</Button>
									<Button variant="danger" type="button" disabled={actingId !== null} on:click={() => reject(item.id)}>
										Reject
									</Button>
								</div>
							</div>
						</Card>
					</li>
				{/each}
			</ul>
		{/if}
	</PageShell>
</div>

<style>
	.review-badge {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding: 10px 12px;
		border-radius: var(--radius-pill);
		background: var(--surface-subtle);
		border: 1px solid var(--line);
		font-size: 13px;
		font-weight: 700;
		color: var(--muted);
	}

	.review-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 14px;
	}

	.review-row {
		display: grid;
		gap: 18px;
	}

	.review-thumb {
		padding: 0;
		margin: 0;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		overflow: hidden;
		background: var(--surface);
		aspect-ratio: 4 / 3;
		cursor: pointer;
	}

	.review-thumb:hover {
		border-color: color-mix(in srgb, var(--brand) 35%, var(--line));
	}

	.review-thumb:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.review-thumb__image {
		width: 100%;
		height: 100%;
		display: block;
		object-fit: cover;
	}

	.review-row__content {
		display: grid;
		gap: 16px;
	}

	.review-row__meta {
		display: grid;
		gap: 8px;
	}

	.env-pill {
		margin: 0;
		display: inline-flex;
		width: fit-content;
		align-items: center;
		padding: 4px 10px;
		border-radius: var(--radius-pill);
		font-size: 10px;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.env-pill--outdoor {
		background: var(--success-light);
		color: var(--success-ink);
	}

	.env-pill--indoor {
		background: var(--brand-light);
		color: var(--brand-dark);
	}

	.review-row__title,
	.review-row__copy {
		margin: 0;
	}

	.review-row__title {
		font-size: 18px;
		font-weight: 800;
		line-height: 1.2;
	}

	.review-row__copy {
		font-size: 14px;
		line-height: 1.55;
		color: var(--muted);
	}

	.review-row__actions {
		display: flex;
		flex-wrap: wrap;
		gap: 10px;
	}

	@media (min-width: 760px) {
		.review-row {
			grid-template-columns: 220px minmax(0, 1fr);
			align-items: start;
		}
	}
</style>
