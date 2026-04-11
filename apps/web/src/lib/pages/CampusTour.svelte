<script lang="ts">
import { imageQueries } from "$lib/domains/images/queries/images.queries";
import type { TourImageItem } from "$lib/domains/images/types";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import TogglePills from "$lib/shared/components/TogglePills.svelte";
import type { ToggleOption } from "$lib/shared/components/TogglePills.svelte";
import {
	CAMPUS_BOUNDS,
	CAMPUS_CENTER,
	CAMPUS_ZOOM,
	addCampusBaseLayer,
} from "$lib/shared/maps/leafletTheme";
import Spinner from "$lib/shared/ui/Spinner.svelte";
import StateBlock from "$lib/shared/ui/StateBlock.svelte";
import { createQuery } from "@tanstack/svelte-query";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { onDestroy, onMount } from "svelte";
import { navigate } from "svelte-routing";

interface LocationGroup {
	name: string;
	slug: string;
	lat: number;
	lng: number;
	images: TourImageItem[];
	environments: Set<string>;
}

const environmentOptions = [
	{ value: "any", label: "All" },
	{ value: "indoor", label: "Indoor" },
	{ value: "outdoor", label: "Outdoor" },
] satisfies ToggleOption[];

let environment: "any" | "indoor" | "outdoor" = "any";
let searchTerm = "";
let mapContainer: HTMLDivElement;
let map: L.Map | null = null;
let markerLayer: L.LayerGroup | null = null;
let resizeObserver: ResizeObserver | null = null;

$: tourQuery = createQuery({
	...imageQueries.tour(environment),
	enabled: $auth.isInitialized,
});

$: tourItems = $tourQuery.data ?? [];
$: allLocations = groupByLocation(tourItems);
$: visibleLocations = filterLocations(allLocations, searchTerm);
$: visibleImageCount = visibleLocations.reduce((sum, group) => sum + group.images.length, 0);
$: if (map && markerLayer) renderMarkers(visibleLocations);

function groupByLocation(items: TourImageItem[]): LocationGroup[] {
	const groups = new Map<string, TourImageItem[]>();

	for (const item of items) {
		const key = item.location_name ?? "__other__";
		const list = groups.get(key);
		if (list) {
			list.push(item);
		} else {
			groups.set(key, [item]);
		}
	}

	const result: LocationGroup[] = [];
	for (const [key, images] of groups) {
		const name = key === "__other__" ? "Other" : key;
		const slug = key === "__other__" ? "other" : encodeURIComponent(key);
		const lat = images.reduce((s, i) => s + i.latitude, 0) / images.length;
		const lng = images.reduce((s, i) => s + i.longitude, 0) / images.length;
		const environments = new Set(images.map((i) => i.environment));
		result.push({ name, slug, lat, lng, images, environments });
	}

	result.sort((a, b) => {
		if (a.name === "Other") return 1;
		if (b.name === "Other") return -1;
		return a.name.localeCompare(b.name);
	});

	return result;
}

function filterLocations(groups: LocationGroup[], search: string): LocationGroup[] {
	const query = search.trim().toLowerCase();
	if (!query) return groups;
	return groups.filter((group) => group.name.toLowerCase().includes(query));
}

function goToLocation(group: LocationGroup) {
	navigate(`/tour/${group.slug}`);
}

function renderMarkers(groups: LocationGroup[]) {
	if (!map || !markerLayer) return;
	markerLayer.clearLayers();

	for (const group of groups) {
		const count = group.images.length;
		const icon = L.divIcon({
			className: "tour-pin",
			html: `<div class="tour-pin-body">${count}</div>`,
			iconSize: [32, 32],
			iconAnchor: [16, 16],
		});

		const marker = L.marker([group.lat, group.lng], { icon });
		marker.bindTooltip(group.name, {
			direction: "top",
			offset: [0, -18],
			className: "tour-tooltip",
		});
		marker.on("click", () => goToLocation(group));
		marker.addTo(markerLayer);
	}
}

function formatEnv(envs: Set<string>): string {
	if (envs.size > 1) return "Mixed";
	if (envs.has("indoor")) return "Indoor";
	return "Outdoor";
}

onMount(() => {
	map = L.map(mapContainer, {
		center: CAMPUS_CENTER,
		zoom: CAMPUS_ZOOM,
		zoomControl: false,
		attributionControl: false,
		minZoom: 13,
		maxBounds: CAMPUS_BOUNDS,
		maxBoundsViscosity: 1.0,
	});

	addCampusBaseLayer(map);
	markerLayer = L.layerGroup().addTo(map);

	resizeObserver = new ResizeObserver(() => {
		map?.invalidateSize();
	});
	resizeObserver.observe(mapContainer);
});

onDestroy(() => {
	resizeObserver?.disconnect();
	resizeObserver = null;
	if (map) {
		map.remove();
		map = null;
	}
});
</script>

<div class="tour-page">
	<Navbar activePage="tour" />

	<div class="tour-layout">
		<div class="map-panel">
			<div bind:this={mapContainer} class="tour-map leaflet-theme" />
		</div>

		<aside class="sidebar">
			<header class="sidebar-header">
				<div class="sidebar-heading">
					<p class="sidebar-eyebrow">Explore</p>
					<h1 class="sidebar-title">Campus Tour</h1>
					<p class="sidebar-copy">
						Browse approved panoramas across Vanderbilt's campus, grouped by building.
					</p>
				</div>
				<div class="sidebar-filter">
					<span class="control-lbl">Environment</span>
					<TogglePills
						ariaLabel="Campus tour environment"
						selected={environment}
						options={environmentOptions}
						on:change={(event) => {
							if (
								event.detail === "any" ||
								event.detail === "indoor" ||
								event.detail === "outdoor"
							) {
								environment = event.detail;
							}
						}}
					/>
				</div>
				<div class="sidebar-search">
					<label class="control-lbl" for="tour-search">Search locations</label>
					<input
						id="tour-search"
						type="search"
						class="search-input"
						placeholder="Search by location name"
						bind:value={searchTerm}
					/>
				</div>
			</header>

			<div class="sidebar-body">
				{#if $tourQuery.isLoading}
					<StateBlock title="Loading locations">
						<Spinner />
					</StateBlock>
				{:else if $tourQuery.isError}
					<StateBlock tone="error" title="Couldn't load the tour" copy="Something went wrong fetching images." />
				{:else if allLocations.length === 0}
					<StateBlock tone="soft" title="No locations found" copy="Try a different environment filter, or upload some panoramas first." />
				{:else if visibleLocations.length === 0}
					<StateBlock tone="soft" title="No matches" copy="No locations match that search with the current environment filter.">
						<button type="button" class="clear-search-btn" on:click={() => (searchTerm = "")}>Clear search</button>
					</StateBlock>
				{:else}
					<p class="sidebar-count">
						{#if searchTerm.trim()}
							Showing {visibleLocations.length} of {allLocations.length} locations &middot; {visibleImageCount} images
						{:else}
							{visibleLocations.length} locations &middot; {visibleImageCount} images
						{/if}
					</p>
					<div class="location-list">
						{#each visibleLocations as group (group.slug)}
							<button
								type="button"
								class="location-row"
								on:click={() => goToLocation(group)}
							>
								<div class="location-thumb">
									<img
										src={group.images[0].thumbnail_url}
										alt={group.name}
										loading="lazy"
										decoding="async"
									/>
								</div>
								<div class="location-info">
									<p class="location-name">{group.name}</p>
									<div class="location-meta">
										<span>{group.images.length} {group.images.length === 1 ? "image" : "images"}</span>
										<span class="location-meta-sep">&middot;</span>
										<span>{formatEnv(group.environments)}</span>
									</div>
								</div>
								<svg class="location-chevron" width="16" height="16" viewBox="0 0 16 16" fill="none">
									<path d="M6 4L10 8L6 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
								</svg>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		</aside>
	</div>
</div>

<style>
	.tour-page {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
		height: 100dvh;
		overflow: hidden;
		background: var(--canvas);
		color: var(--ink);
	}

	.tour-layout {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr;
		grid-template-rows: minmax(240px, 42%) minmax(0, 1fr);
		min-height: 0;
	}

	.map-panel {
		position: relative;
		min-height: 0;
	}

	.tour-map {
		width: 100%;
		height: 100%;
		min-height: 0;
	}

	.sidebar {
		display: flex;
		flex-direction: column;
		min-height: 0;
		border-top: 1px solid var(--line);
		background: var(--surface);
		overflow: hidden;
	}

	.sidebar-header {
		display: grid;
		gap: 16px;
		padding: 20px 20px 16px;
		border-bottom: 1px solid var(--line);
	}

	.sidebar-heading {
		display: grid;
		gap: 4px;
	}

	.sidebar-eyebrow {
		margin: 0;
		font-size: 12px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--muted);
	}

	.sidebar-title {
		margin: 0;
		font-size: 22px;
		font-weight: 700;
		line-height: 1.2;
	}

	.sidebar-copy {
		margin: 4px 0 0;
		font-size: 14px;
		color: var(--muted);
		line-height: 1.4;
	}

	.sidebar-filter {
		display: grid;
		gap: 6px;
	}

	.sidebar-search {
		display: grid;
		gap: 6px;
	}

	.search-input {
		width: 100%;
		height: 44px;
		padding: 0 12px;
		border: 1px solid var(--line);
		border-radius: var(--radius-sm);
		background: var(--surface);
		font-size: 14px;
		color: var(--ink);
	}

	.search-input::placeholder {
		color: var(--muted);
	}

	.search-input:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.control-lbl {
		font-size: 12px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--muted);
	}

	.sidebar-body {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		overscroll-behavior: contain;
		padding: 12px;
	}

	.sidebar-count {
		margin: 0 0 8px 8px;
		font-family: "IBM Plex Mono", monospace;
		font-size: 12px;
		font-weight: 600;
		color: var(--muted);
	}

	.location-list {
		display: grid;
		gap: 4px;
	}

	.location-row {
		display: grid;
		grid-template-columns: 52px 1fr 16px;
		gap: 12px;
		align-items: center;
		width: 100%;
		padding: 10px;
		border: 1px solid transparent;
		border-radius: var(--radius-md);
		background: transparent;
		text-align: left;
		cursor: pointer;
		transition:
			background var(--duration-fast) var(--ease),
			border-color var(--duration-fast) var(--ease);
	}

	.location-row:hover {
		background: var(--surface-subtle);
		border-color: var(--line);
	}

	.location-row:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.location-thumb {
		width: 52px;
		height: 52px;
		border-radius: var(--radius-sm);
		overflow: hidden;
		background: var(--surface-strong);
		flex-shrink: 0;
	}

	.location-thumb img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
	}

	.location-info {
		min-width: 0;
	}

	.location-name {
		margin: 0;
		font-size: 14px;
		font-weight: 600;
		line-height: 1.3;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.location-meta {
		display: flex;
		align-items: center;
		gap: 4px;
		margin-top: 2px;
		font-size: 12px;
		color: var(--muted);
	}

	.location-meta-sep {
		color: var(--line-strong);
	}

	.location-chevron {
		color: var(--muted);
		flex-shrink: 0;
	}

	.clear-search-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		height: 36px;
		padding: 0 14px;
		border: 1px solid var(--line);
		border-radius: var(--radius-sm);
		background: var(--surface);
		font-size: 13px;
		font-weight: 600;
		color: var(--ink);
		cursor: pointer;
		transition:
			background var(--duration-fast) var(--ease),
			border-color var(--duration-fast) var(--ease);
	}

	.clear-search-btn:hover {
		background: var(--surface-subtle);
		border-color: var(--line-strong);
	}

	.clear-search-btn:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	/* Leaflet pin styles */
	:global(.tour-pin) {
		background: none !important;
		border: none !important;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	:global(.tour-pin-body) {
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: "Inter", sans-serif;
		font-size: 13px;
		font-weight: 700;
		color: white;
		background: var(--brand);
		border: 3px solid white;
		border-radius: 50%;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
		cursor: pointer;
		transition: transform 120ms ease;
	}

	:global(.tour-pin-body:hover) {
		transform: scale(1.15);
	}

	:global(.tour-tooltip) {
		font-family: "Inter", sans-serif;
		font-size: 12px;
		font-weight: 600;
		padding: 4px 10px;
		border-radius: 6px;
		border: 1px solid var(--line);
		background: var(--surface);
		color: var(--ink);
		box-shadow: var(--shadow-sm);
	}

	@media (min-width: 768px) {
		.tour-layout {
			grid-template-columns: minmax(0, 1fr) 380px;
			grid-template-rows: minmax(0, 1fr);
		}

		.map-panel {
			min-height: 0;
		}

		.tour-map {
			min-height: 0;
		}

		.sidebar {
			border-top: none;
			border-left: 1px solid var(--line);
		}
	}

	@media (min-width: 1024px) {
		.tour-layout {
			grid-template-columns: minmax(0, 1fr) 420px;
		}
	}
</style>
