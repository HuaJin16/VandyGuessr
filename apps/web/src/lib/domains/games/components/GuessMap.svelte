<script lang="ts">
import L from "leaflet";
import { createEventDispatcher, onDestroy, onMount } from "svelte";
import "leaflet/dist/leaflet.css";

export let position: { lat: number; lng: number } | null = null;

const dispatch = createEventDispatcher<{ click: { lat: number; lng: number } }>();

const CAMPUS_CENTER: L.LatLngExpression = [36.1453, -86.802];
const CAMPUS_ZOOM = 16;

let mapContainer: HTMLDivElement;
let map: L.Map | null = null;
let marker: L.Marker | null = null;
let resizeObserver: ResizeObserver | null = null;

const pinIcon = L.divIcon({
	className: "guess-pin",
	html: `<div class="pin-dot"></div>`,
	iconSize: [24, 24],
	iconAnchor: [12, 12],
});

onMount(() => {
	map = L.map(mapContainer, {
		center: CAMPUS_CENTER,
		zoom: CAMPUS_ZOOM,
		zoomControl: false,
		attributionControl: false,
		minZoom: 13,
		maxBounds: L.latLngBounds([36.05, -86.92], [36.25, -86.7]),
		maxBoundsViscosity: 1.0,
	});

	L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
		maxZoom: 19,
	}).addTo(map);

	map.on("click", (e: L.LeafletMouseEvent) => {
		const pos = { lat: e.latlng.lat, lng: e.latlng.lng };
		dispatch("click", pos);
	});

	resizeObserver = new ResizeObserver(() => {
		map?.invalidateSize();
	});
	resizeObserver.observe(mapContainer);

	if (position) placeMarker(position);
});

$: if (map && position) placeMarker(position);

function placeMarker(pos: { lat: number; lng: number }) {
	if (!map) return;
	if (marker) {
		marker.setLatLng([pos.lat, pos.lng]);
	} else {
		marker = L.marker([pos.lat, pos.lng], { icon: pinIcon }).addTo(map);
	}
}

onDestroy(() => {
	resizeObserver?.disconnect();
	resizeObserver = null;
	if (map) {
		map.remove();
		map = null;
	}
});
</script>

<div bind:this={mapContainer} class="guess-map" />

<style>
	.guess-map {
		width: 100%;
		height: 100%;
		border-radius: 12px;
		overflow: hidden;
		filter: grayscale(0.5) sepia(0.25) contrast(1.05);
	}

	:global(.guess-pin) {
		background: none !important;
		border: none !important;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	:global(.pin-dot) {
		width: 16px;
		height: 16px;
		background: #2e933c;
		border: 3px solid white;
		border-radius: 50%;
		box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
	}
</style>
