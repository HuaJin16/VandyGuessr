<script lang="ts">
import { CAMPUS_BOUNDS, addCampusBaseLayer } from "$lib/shared/maps/leafletTheme";
import L from "leaflet";
import { onDestroy, onMount } from "svelte";
import "leaflet/dist/leaflet.css";

export let guess: { lat: number; lng: number };
export let actual: { lat: number; lng: number };
export let distanceMeters: number;
export let locationName: string | null = null;

let mapContainer: HTMLDivElement;
let map: L.Map | null = null;

const guessPinSvg = `<svg width="24" height="32" viewBox="0 0 32 42" fill="none" xmlns="http://www.w3.org/2000/svg">
	<path d="M16 0C7.16 0 0 7.16 0 16c0 12 16 26 16 26s16-14 16-26C32 7.16 24.84 0 16 0z" fill="#2e933c" stroke="#236e2d" stroke-width="1.5"/>
	<circle cx="16" cy="15" r="7" fill="white"/>
</svg>`;

const flagSvg = `<svg width="22" height="30" viewBox="0 0 30 40" fill="none" xmlns="http://www.w3.org/2000/svg">
	<rect x="3" y="0" width="3" height="40" rx="1.5" fill="#6b4c00"/>
	<path d="M6 3h21l-6 8.5 6 8.5H6V3z" fill="#e8a817" stroke="#c48d10" stroke-width="1"/>
	<circle cx="4.5" cy="2" r="2.5" fill="#6b4c00"/>
</svg>`;

const guessPinIcon = L.divIcon({
	className: "results-pin guess",
	html: `<div class="pin-wrapper"><div class="pin-label pin-label-guess">Your Guess</div><div class="pin-svg">${guessPinSvg}</div></div>`,
	iconSize: [0, 0],
	iconAnchor: [0, 48],
});

function createActualPinIcon(name: string | null) {
	const label = name || "Actual";
	return L.divIcon({
		className: "results-pin actual",
		html: `<div class="pin-wrapper"><div class="pin-label pin-label-actual">${label}</div><div class="pin-svg">${flagSvg}</div></div>`,
		iconSize: [0, 0],
		iconAnchor: [-1, 46],
	});
}

function formatDistance(meters: number): string {
	if (meters < 1000) return `${Math.round(meters)}m`;
	return `${(meters / 1000).toFixed(1)}km`;
}

onMount(() => {
	const bounds = L.latLngBounds([guess.lat, guess.lng], [actual.lat, actual.lng]);

	map = L.map(mapContainer, {
		zoomControl: false,
		attributionControl: false,
		dragging: true,
		scrollWheelZoom: true,
		minZoom: 13,
		maxBounds: CAMPUS_BOUNDS,
		maxBoundsViscosity: 1.0,
	});

	map.fitBounds(bounds.pad(0.6));

	addCampusBaseLayer(map);

	L.polyline(
		[
			[guess.lat, guess.lng],
			[actual.lat, actual.lng],
		],
		{
			color: "#5c6370",
			weight: 2.5,
			dashArray: "6 8",
			lineCap: "round",
			interactive: false,
		},
	).addTo(map);

	const midLat = (guess.lat + actual.lat) / 2;
	const midLng = (guess.lng + actual.lng) / 2;

	const distLabel = L.divIcon({
		className: "distance-label-container",
		html: `<div class="distance-label"><svg class="dist-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 20V4M5 11l7-7 7 7"/></svg>${formatDistance(distanceMeters)}</div>`,
		iconSize: [0, 0],
		iconAnchor: [0, 14],
	});
	L.marker([midLat, midLng], { icon: distLabel, interactive: false }).addTo(map);

	L.marker([guess.lat, guess.lng], { icon: guessPinIcon, interactive: false }).addTo(map);
	L.marker([actual.lat, actual.lng], {
		icon: createActualPinIcon(locationName),
		interactive: false,
	}).addTo(map);
});

onDestroy(() => {
	if (map) {
		map.remove();
		map = null;
	}
});
</script>

<div bind:this={mapContainer} class="results-map leaflet-theme" />

<style>
	.results-map {
		width: 100%;
		height: 100%;
		position: absolute;
		inset: 0;
		z-index: 0;
	}

	:global(.results-pin) {
		z-index: 500 !important;
	}

	:global(.pin-wrapper) {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 3px;
	}

	:global(.pin-svg) {
		line-height: 0;
		filter: drop-shadow(2px 2px 0 rgba(0, 0, 0, 0.12));
	}

	:global(.pin-label) {
		font-size: 11px;
		font-weight: 700;
		padding: 3px 10px;
		border-radius: 9999px;
		white-space: nowrap;
		border: 1px solid transparent;
	}

	:global(.pin-label-guess) {
		color: white;
		background: #2e933c;
		border-color: #236e2d;
		box-shadow: 2px 2px 0 0 rgba(0, 0, 0, 0.1);
	}

	:global(.pin-label-actual) {
		color: #6b4c00;
		background: #e8a817;
		border-color: #c48d10;
		box-shadow: 2px 2px 0 0 rgba(0, 0, 0, 0.1);
	}

	:global(.distance-label-container) {
		z-index: 600 !important;
		overflow: visible !important;
	}

	:global(.distance-label) {
		font-family: "IBM Plex Mono", monospace;
		font-size: 12px;
		font-weight: 600;
		color: #1a1a1a;
		background: rgba(255, 255, 255, 0.97);
		border: 1px solid #e5e2db;
		padding: 4px 10px;
		border-radius: 9999px;
		white-space: nowrap;
		width: max-content;
		box-shadow: 2px 2px 0 0 rgba(0, 0, 0, 0.08);
		transform: translate(-50%, -50%);
		display: flex;
		align-items: center;
		gap: 4px;
	}

	:global(.distance-label .dist-icon) {
		flex-shrink: 0;
		opacity: 0.45;
	}
</style>
