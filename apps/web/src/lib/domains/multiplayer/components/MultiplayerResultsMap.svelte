<script lang="ts">
import { CAMPUS_BOUNDS, addCampusBaseLayer } from "$lib/shared/maps/leafletTheme";
import L from "leaflet";
import { onDestroy, onMount } from "svelte";
import "leaflet/dist/leaflet.css";
import type { RoundResult } from "../types";

export let result: RoundResult;
export let currentUserId: string;

const rawColors = ["#2e933c", "#3b82f6", "#8b5cf6", "#f97316", "#06b6d4", "#ec4899"];
const rawColorsDark = ["#236e2d", "#2563eb", "#6d28d9", "#c2410c", "#0891b2", "#be185d"];

function getColorIndex(userId: string): number {
	if (userId === currentUserId) return 0;
	let opponentIdx = 0;
	for (const r of result.results) {
		if (r.userId === currentUserId) continue;
		if (r.userId === userId) return 1 + opponentIdx;
		opponentIdx++;
	}
	return 0;
}

function getRawColor(userId: string): string {
	return rawColors[getColorIndex(userId)];
}

function getDarkColor(userId: string): string {
	return rawColorsDark[getColorIndex(userId)];
}

function getFirstName(name: string): string {
	return name.split(" ")[0];
}

function formatDistance(meters: number | null): string {
	if (meters === null) return "\u2014";
	if (meters < 1000) return `${Math.round(meters)}m`;
	return `${(meters / 1000).toFixed(1)}km`;
}

function createPlayerPinSvg(color: string, strokeColor: string): string {
	return `<svg width="22" height="30" viewBox="0 0 32 42" fill="none" xmlns="http://www.w3.org/2000/svg">
		<path d="M16 0C7.16 0 0 7.16 0 16c0 12 16 26 16 26s16-14 16-26C32 7.16 24.84 0 16 0z" fill="${color}" stroke="${strokeColor}" stroke-width="1.5"/>
		<circle cx="16" cy="15" r="7" fill="white"/>
	</svg>`;
}

const flagSvg = `<svg width="20" height="28" viewBox="0 0 30 40" fill="none" xmlns="http://www.w3.org/2000/svg">
	<rect x="3" y="0" width="3" height="40" rx="1.5" fill="#6b4c00"/>
	<path d="M6 3h21l-6 8.5 6 8.5H6V3z" fill="#e8a817" stroke="#c48d10" stroke-width="1"/>
	<circle cx="4.5" cy="2" r="2.5" fill="#6b4c00"/>
</svg>`;

let mapContainer: HTMLDivElement;
let map: L.Map | null = null;

onMount(() => {
	const allPoints: L.LatLngExpression[] = [[result.actual.lat, result.actual.lng]];
	for (const r of result.results) {
		if (r.guess) allPoints.push([r.guess.lat, r.guess.lng]);
	}

	const bounds = L.latLngBounds(allPoints);

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

	// Player lines (draw first so they're behind markers)
	for (const r of result.results) {
		if (!r.guess) continue;
		const color = getRawColor(r.userId);

		L.polyline(
			[
				[r.guess.lat, r.guess.lng],
				[result.actual.lat, result.actual.lng],
			],
			{
				color,
				weight: 2.5,
				dashArray: "6 8",
				opacity: 0.45,
				lineCap: "round",
				interactive: false,
			},
		).addTo(map);
	}

	// Distance labels
	for (const r of result.results) {
		if (!r.guess || r.distanceMeters === null) continue;
		const midLat = (r.guess.lat + result.actual.lat) / 2;
		const midLng = (r.guess.lng + result.actual.lng) / 2;
		const distIcon = L.divIcon({
			className: "mp-dist-container",
			html: `<div class="mp-dist-label">${formatDistance(r.distanceMeters)}</div>`,
			iconSize: [0, 0],
			iconAnchor: [0, 12],
		});
		L.marker([midLat, midLng], { icon: distIcon, interactive: false }).addTo(map);
	}

	// Actual location flag
	const actualIcon = L.divIcon({
		className: "mp-pin actual",
		html: `<div class="mp-pin-wrap"><div class="mp-pin-label mp-pin-label-actual">${result.locationName ?? "Actual"}</div><div class="mp-pin-svg">${flagSvg}</div></div>`,
		iconSize: [0, 0],
		iconAnchor: [-1, 44],
	});
	L.marker([result.actual.lat, result.actual.lng], { icon: actualIcon, interactive: false }).addTo(
		map,
	);

	// Player pins
	for (const r of result.results) {
		if (!r.guess) continue;
		const color = getRawColor(r.userId);
		const dark = getDarkColor(r.userId);
		const isYou = r.userId === currentUserId;
		const displayName = isYou ? "You" : getFirstName(r.name);

		const playerIcon = L.divIcon({
			className: "mp-pin player",
			html: `<div class="mp-pin-wrap"><div class="mp-pin-label" style="background: ${color}; border-color: ${dark}; color: #fff;">${displayName}</div><div class="mp-pin-svg">${createPlayerPinSvg(color, dark)}</div></div>`,
			iconSize: [0, 0],
			iconAnchor: [0, 46],
		});
		L.marker([r.guess.lat, r.guess.lng], { icon: playerIcon, interactive: false }).addTo(map);
	}
});

onDestroy(() => {
	if (map) {
		map.remove();
		map = null;
	}
});
</script>

<div class="map-container">
	<div bind:this={mapContainer} class="mp-results-map leaflet-theme" />
</div>

<style>
	.map-container {
		position: relative;
		margin-top: 8px;
		height: 300px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		overflow: hidden;
		isolation: isolate;
	}

	.mp-results-map {
		width: 100%;
		height: 100%;
		position: absolute;
		inset: 0;
	}

	:global(.mp-pin) {
		z-index: 500 !important;
	}

	:global(.mp-pin-wrap) {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 3px;
	}

	:global(.mp-pin-svg) {
		line-height: 0;
		filter: drop-shadow(2px 2px 0 rgba(0, 0, 0, 0.12));
	}

	:global(.mp-pin-label) {
		font-size: 11px;
		font-weight: 700;
		padding: 3px 10px;
		border-radius: 9999px;
		white-space: nowrap;
		border: 1px solid transparent;
		box-shadow: 2px 2px 0 0 rgba(0, 0, 0, 0.1);
	}

	:global(.mp-pin-label-actual) {
		color: #6b4c00;
		background: #e8a817;
		border-color: #c48d10;
	}

	:global(.mp-dist-container) {
		z-index: 600 !important;
		overflow: visible !important;
	}

	:global(.mp-dist-label) {
		font-family: "IBM Plex Mono", monospace;
		font-size: 11px;
		font-weight: 600;
		color: #1a1a1a;
		background: rgba(255, 255, 255, 0.97);
		border: 1px solid #e5e2db;
		padding: 3px 8px;
		border-radius: 9999px;
		white-space: nowrap;
		width: max-content;
		box-shadow: 2px 2px 0 0 rgba(0, 0, 0, 0.08);
		transform: translate(-50%, -50%);
	}

	@media (min-width: 700px) {
		.map-container {
			height: 400px;
		}
	}
</style>
