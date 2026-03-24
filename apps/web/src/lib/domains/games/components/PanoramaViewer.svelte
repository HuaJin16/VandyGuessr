<script lang="ts">
import { Viewer } from "@photo-sphere-viewer/core";
import { EquirectangularTilesAdapter } from "@photo-sphere-viewer/equirectangular-tiles-adapter";
import { onDestroy, onMount } from "svelte";
import type { RoundTiles } from "../types";
import "@photo-sphere-viewer/core/index.css";

export let imageUrl: string;
export let imageTiles: RoundTiles | null = null;

let container: HTMLDivElement;
let viewer: Viewer | null = null;
let activePanoramaKey = "";
let activeMode: "tiles" | "image" | null = null;

function toTileUrl(template: string, level: number, col: number, row: number): string {
	return template
		.replace("{level}", String(level))
		.replace("{col}", String(col))
		.replace("{row}", String(row));
}

function isValidTilesConfig(tiles: RoundTiles | null): tiles is RoundTiles {
	if (!tiles || !tiles.baseUrl || !tiles.tileUrlTemplate) return false;
	if (!tiles.levels || tiles.levels.length === 0) return false;
	if (!tiles.basePanoData) return false;
	return tiles.levels.every(
		(level) => level.cols > 0 && level.rows > 0 && level.width > 0 && level.height > 0,
	);
}

function panoramaKey(url: string, tiles: RoundTiles | null): string {
	if (isValidTilesConfig(tiles)) {
		const levelsKey = tiles.levels
			.map((level) => `${level.level}:${level.width}:${level.height}:${level.cols}:${level.rows}`)
			.join("|");

		return [
			"tiles",
			tiles.version,
			tiles.baseUrl,
			tiles.tileUrlTemplate,
			tiles.originalWidth,
			tiles.originalHeight,
			levelsKey,
		].join("::");
	}

	return `image::${url}`;
}

function panoramaPayload(url: string, tiles: RoundTiles | null): string | object {
	if (!isValidTilesConfig(tiles)) {
		return url;
	}

	const basePanoData = tiles.basePanoData;
	return {
		baseUrl: tiles.baseUrl,
		basePanoData: {
			isEquirectangular: true,
			fullWidth: basePanoData.fullWidth,
			fullHeight: basePanoData.fullHeight,
			croppedWidth: basePanoData.croppedWidth,
			croppedHeight: basePanoData.croppedHeight,
			croppedX: basePanoData.croppedX,
			croppedY: basePanoData.croppedY,
		},
		levels: tiles.levels.map((level) => ({
			width: level.width,
			cols: level.cols,
			rows: level.rows,
		})),
		tileUrl: (col: number, row: number, level: number) =>
			toTileUrl(tiles.tileUrlTemplate, level, col, row),
	};
}

function modeFor(tiles: RoundTiles | null): "tiles" | "image" {
	return isValidTilesConfig(tiles) ? "tiles" : "image";
}

function createViewer(mode: "tiles" | "image") {
	const initialPayload = panoramaPayload(imageUrl, imageTiles);
	viewer = new Viewer({
		container,
		adapter: mode === "tiles" ? [EquirectangularTilesAdapter, { baseBlur: true }] : undefined,
		panorama: initialPayload,
		navbar: false,
		defaultZoomLvl: 50,
		touchmoveTwoFingers: false,
		mousewheelCtrlKey: false,
	});

	activeMode = mode;
	activePanoramaKey = panoramaKey(imageUrl, imageTiles);
}

async function syncPanorama() {
	if (!viewer) return;
	const mode = modeFor(imageTiles);
	if (mode !== activeMode) {
		viewer.destroy();
		createViewer(mode);
		return;
	}

	const nextKey = panoramaKey(imageUrl, imageTiles);
	if (nextKey === activePanoramaKey) return;

	try {
		await viewer.setPanorama(panoramaPayload(imageUrl, imageTiles));
		activePanoramaKey = nextKey;
	} catch {
		activePanoramaKey = "";
	}
}

onMount(async () => {
	createViewer(modeFor(imageTiles));
});

$: if (viewer && (imageUrl || imageTiles)) {
	void syncPanorama();
}

onDestroy(() => {
	if (viewer) {
		viewer.destroy();
		viewer = null;
	}
});
</script>

<div bind:this={container} class="panorama-container" />

<style>
	.panorama-container {
		width: 100%;
		height: 100%;
		position: absolute;
		inset: 0;
	}

	.panorama-container :global(.psv-container) {
		width: 100% !important;
		height: 100% !important;
	}

	.panorama-container :global(.psv-loader-container) {
		display: none;
	}
</style>
