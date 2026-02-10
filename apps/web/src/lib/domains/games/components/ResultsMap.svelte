<script lang="ts">
import L from "leaflet";
import { onDestroy, onMount } from "svelte";
import "leaflet/dist/leaflet.css";

export let guess: { lat: number; lng: number };
export let actual: { lat: number; lng: number };
export let distanceMeters: number;
export let locationName: string | null = null;

let mapContainer: HTMLDivElement;
let map: L.Map | null = null;

const guessPinIcon = L.divIcon({
	className: "results-pin guess",
	html: `<div class="pin-wrapper"><div class="pin-label pin-label-guess">Your Guess</div><span class="material-symbols-outlined pin-icon pin-icon-guess" style="font-variation-settings: 'FILL' 1;">location_on</span></div>`,
	iconSize: [0, 0],
	iconAnchor: [0, 56],
});

function createActualPinIcon(name: string | null) {
	const label = name || "Actual";
	return L.divIcon({
		className: "results-pin actual",
		html: `<div class="pin-wrapper"><div class="pin-label pin-label-actual">${label}</div><span class="material-symbols-outlined pin-icon pin-icon-actual" style="font-variation-settings: 'FILL' 1;">flag</span></div>`,
		iconSize: [0, 0],
		iconAnchor: [0, 56],
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
		maxBounds: L.latLngBounds([36.05, -86.92], [36.25, -86.7]),
		maxBoundsViscosity: 1.0,
	});

	map.fitBounds(bounds.pad(0.6));

	L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
		maxZoom: 19,
	}).addTo(map);

	L.marker([guess.lat, guess.lng], { icon: guessPinIcon, interactive: false }).addTo(map);
	L.marker([actual.lat, actual.lng], {
		icon: createActualPinIcon(locationName),
		interactive: false,
	}).addTo(map);

	const midLat = (guess.lat + actual.lat) / 2;
	const midLng = (guess.lng + actual.lng) / 2;

	const distLabel = L.divIcon({
		className: "distance-label-container",
		html: `<div class="distance-label">${formatDistance(distanceMeters)}</div>`,
		iconSize: [0, 0],
		iconAnchor: [0, 0],
	});
	L.marker([midLat, midLng], { icon: distLabel, interactive: false }).addTo(map);

	L.polyline(
		[
			[guess.lat, guess.lng],
			[actual.lat, actual.lng],
		],
		{
			color: "#18181b",
			weight: 2.5,
			dashArray: "8 6",
			lineCap: "round",
			interactive: false,
		},
	).addTo(map);
});

onDestroy(() => {
	if (map) {
		map.remove();
		map = null;
	}
});
</script>

<div bind:this={mapContainer} class="results-map" />

<style>
	.results-map {
		width: 100%;
		height: 100%;
		position: absolute;
		inset: 0;
		filter: grayscale(0.5) sepia(0.25) contrast(1.05);
	}

	:global(.results-pin) {
		z-index: 500 !important;
	}

	:global(.pin-wrapper) {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
	}

	:global(.pin-icon) {
		font-size: 40px;
		filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
	}

	:global(.pin-icon-guess) {
		color: #2e933c;
	}

	:global(.pin-icon-actual) {
		color: #f4c430;
	}

	:global(.pin-label) {
		font-size: 11px;
		font-weight: 600;
		padding: 2px 8px;
		border-radius: 6px;
		white-space: nowrap;
		box-shadow: 4px 4px 0px 0px rgba(0, 0, 0, 0.1);
	}

	:global(.pin-label-guess) {
		color: white;
		background: #2e933c;
		font-weight: 700;
	}

	:global(.pin-label-actual) {
		color: #18181b;
		background: #f4c430;
		font-weight: 700;
	}

	:global(.distance-label-container) {
		z-index: 600 !important;
		overflow: visible !important;
	}

	:global(.distance-label) {
		font-family: "JetBrains Mono", monospace;
		font-size: 13px;
		font-weight: 700;
		color: white;
		background: rgba(24, 24, 27, 0.9);
		padding: 4px 12px;
		border-radius: 9999px;
		white-space: nowrap;
		width: max-content;
		box-shadow: 4px 4px 0px 0px rgba(0, 0, 0, 0.1);
		transform: translate(-50%, -50%);
	}
</style>
