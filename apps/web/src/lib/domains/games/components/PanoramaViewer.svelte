<script lang="ts">
import { Viewer } from "@photo-sphere-viewer/core";
import { onDestroy } from "svelte";
import "@photo-sphere-viewer/core/index.css";

export let imageUrl: string;

let container: HTMLDivElement;
let viewer: Viewer | null = null;

function initViewer() {
	if (viewer) viewer.destroy();
	viewer = new Viewer({
		container,
		panorama: imageUrl,
		navbar: false,
		defaultZoomLvl: 50,
		touchmoveTwoFingers: false,
		mousewheelCtrlKey: false,
	});
}

$: if (container && imageUrl) {
	initViewer();
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
