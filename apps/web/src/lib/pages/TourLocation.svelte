<script lang="ts">
import RoundPreviewOverlay from "$lib/domains/games/components/RoundPreviewOverlay.svelte";
import { imageQueries } from "$lib/domains/images/queries/images.queries";
import type { TourImageItem } from "$lib/domains/images/types";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import Button from "$lib/shared/ui/Button.svelte";
import PageHeader from "$lib/shared/ui/PageHeader.svelte";
import PageShell from "$lib/shared/ui/PageShell.svelte";
import Spinner from "$lib/shared/ui/Spinner.svelte";
import StateBlock from "$lib/shared/ui/StateBlock.svelte";
import { createQuery } from "@tanstack/svelte-query";
import { ArrowLeft } from "lucide-svelte";
import { navigate } from "svelte-routing";

export let locationName: string;

$: decodedName = locationName === "other" ? null : decodeURIComponent(locationName);
$: displayName = decodedName ?? "Other";

$: tourQuery = createQuery({
	...imageQueries.tour("any"),
	enabled: $auth.isInitialized,
});

$: allItems = $tourQuery.data ?? [];
$: locationItems = allItems.filter((item) =>
	decodedName === null ? item.location_name === null : item.location_name === decodedName,
);

let previewImage: TourImageItem | null = null;
let previewOpen = false;

function openPreview(item: TourImageItem) {
	previewImage = item;
	previewOpen = true;
}

function closePreview() {
	previewOpen = false;
}

function formatCoords(item: TourImageItem): string {
	return `${item.latitude.toFixed(4)}, ${item.longitude.toFixed(4)}`;
}

function formatDate(item: TourImageItem): string | null {
	if (!item.created_at) return null;
	return new Date(item.created_at).toLocaleDateString();
}
</script>

<div class="min-h-screen bg-canvas text-ink">
	<Navbar activePage="tour" />

	<PageShell size="wide">
		<div class="back-row">
			<button type="button" class="back-link" on:click={() => navigate("/tour")}>
				<ArrowLeft size={16} />
				Back to map
			</button>
		</div>

		<PageHeader
			eyebrow={displayName}
			title="{locationItems.length} {locationItems.length === 1 ? 'panorama' : 'panoramas'}"
			copy="Click any image to open the full panoramic view."
		/>

		<section class="image-list">
			{#if $tourQuery.isLoading}
				<StateBlock title="Loading images">
					<Spinner />
				</StateBlock>
			{:else if $tourQuery.isError}
				<StateBlock tone="error" title="Couldn't load images" copy="Something went wrong.">
					<Button type="button" on:click={() => $tourQuery.refetch()}>Try again</Button>
				</StateBlock>
			{:else if locationItems.length === 0}
				<StateBlock
					tone="soft"
					title="No images here"
					copy="This location doesn't have any approved panoramas yet."
				>
					<Button variant="outline" on:click={() => navigate("/tour")}>Back to map</Button>
				</StateBlock>
			{:else}
				{#each locationItems as item (item.id)}
					<button type="button" class="image-card" on:click={() => openPreview(item)}>
						<div class="image-card-thumb">
							<img
								src={item.thumbnail_url}
								alt="{displayName} panorama"
								loading="lazy"
								decoding="async"
							/>
							<div class="image-card-overlay">
								<span class="image-card-cta">View Panorama</span>
							</div>
						</div>
						<div class="image-card-meta">
							<span class="image-card-env">{item.environment === "indoor" ? "Indoor" : "Outdoor"}</span>
							<span class="image-card-sep">&middot;</span>
							<span>{formatCoords(item)}</span>
							{#if formatDate(item)}
								<span class="image-card-sep">&middot;</span>
								<span>Added {formatDate(item)}</span>
							{/if}
						</div>
					</button>
				{/each}
			{/if}
		</section>
	</PageShell>
</div>

{#if previewImage}
	<RoundPreviewOverlay
		open={previewOpen}
		imageUrl={previewImage.url}
		imageTiles={previewImage.tiles}
		title={displayName}
		onClose={closePreview}
	/>
{/if}

<style>
	.back-row {
		margin-bottom: 8px;
	}

	.back-link {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 6px 0;
		border: none;
		background: transparent;
		color: var(--muted);
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
		transition: color var(--duration-fast) var(--ease);
	}

	.back-link:hover {
		color: var(--ink);
	}

	.image-list {
		display: grid;
		gap: 12px;
		margin-top: 20px;
		padding-bottom: 40px;
	}

	.image-card {
		display: grid;
		width: 100%;
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		background: var(--surface);
		overflow: hidden;
		cursor: pointer;
		text-align: left;
		transition:
			border-color var(--duration-fast) var(--ease),
			box-shadow var(--duration-fast) var(--ease),
			transform var(--duration-fast) var(--ease);
	}

	.image-card:hover {
		border-color: var(--brand);
		box-shadow: var(--shadow-sm);
		transform: translateY(-1px);
	}

	.image-card:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.image-card-thumb {
		position: relative;
		aspect-ratio: 3 / 1;
		background: var(--surface-strong);
		overflow: hidden;
	}

	.image-card-thumb img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
		transition: transform 300ms var(--ease);
	}

	.image-card:hover .image-card-thumb img {
		transform: scale(1.03);
	}

	.image-card-overlay {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(28, 25, 23, 0);
		transition: background 200ms var(--ease);
	}

	.image-card:hover .image-card-overlay {
		background: rgba(28, 25, 23, 0.35);
	}

	.image-card-cta {
		padding: 8px 16px;
		border-radius: var(--radius-pill);
		background: rgba(255, 255, 255, 0.95);
		font-size: 13px;
		font-weight: 700;
		color: var(--ink);
		opacity: 0;
		transform: translateY(4px);
		transition:
			opacity 200ms var(--ease),
			transform 200ms var(--ease);
	}

	.image-card:hover .image-card-cta {
		opacity: 1;
		transform: translateY(0);
	}

	.image-card-meta {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 12px 16px;
		font-size: 13px;
		color: var(--muted);
	}

	.image-card-env {
		font-weight: 600;
		color: var(--ink);
	}

	.image-card-sep {
		color: var(--line-strong);
	}

	@media (min-width: 640px) {
		.image-card-thumb {
			aspect-ratio: 3.5 / 1;
		}
	}
</style>
