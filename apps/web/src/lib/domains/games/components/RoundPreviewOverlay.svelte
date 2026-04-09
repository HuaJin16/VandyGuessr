<script lang="ts">
import { onMount, tick } from "svelte";
import type { RoundTiles } from "../types";
import PanoramaViewer from "./PanoramaViewer.svelte";

export let open = false;
export let imageUrl = "";
export let imageTiles: RoundTiles | null = null;
export let title = "How players see this round";
export let onClose: () => void;

let closeBtn: HTMLButtonElement;

$: if (open) {
	tick().then(() => {
		closeBtn?.focus();
	});
}

function onWindowKeydown(e: KeyboardEvent) {
	if (!open || !imageUrl) return;
	if (e.key === "Escape") {
		e.preventDefault();
		onClose();
	}
}

onMount(() => {
	window.addEventListener("keydown", onWindowKeydown);
	return () => window.removeEventListener("keydown", onWindowKeydown);
});
</script>

{#if open && imageUrl}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div class="layer" on:click={onClose} role="presentation">
		<div
			class="panel"
			role="dialog"
			aria-modal="true"
			aria-labelledby="round-preview-title"
			on:click|stopPropagation
		>
			<header class="topbar">
				<h2 id="round-preview-title" class="title">{title}</h2>
				<button bind:this={closeBtn} class="btn-ghost-dark" type="button" on:click={onClose}>
					Close
				</button>
			</header>
			<div class="viewer-wrap">
				<PanoramaViewer imageUrl={imageUrl} {imageTiles} />
			</div>
		</div>
	</div>
{/if}

<style>
	.layer {
		position: fixed;
		inset: 0;
		z-index: 100;
		display: flex;
		align-items: stretch;
		justify-content: center;
		padding: 12px;
		background: rgba(28, 25, 23, 0.78);
		box-sizing: border-box;
	}

	.panel {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-height: 0;
		max-width: min(1200px, 100%);
		margin: 0 auto;
		width: 100%;
		border-radius: var(--radius-lg);
		overflow: hidden;
		background: #1c1917;
		border: 1px solid color-mix(in srgb, var(--line) 60%, transparent);
		box-shadow: var(--shadow-md);
	}

	.topbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		flex-shrink: 0;
		padding: 10px 14px;
		background: rgba(12, 18, 14, 0.92);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.title {
		margin: 0;
		font-family: "Inter", sans-serif;
		font-size: 14px;
		font-weight: 700;
		color: rgba(255, 255, 255, 0.94);
		line-height: 1.3;
		letter-spacing: 0.01em;
	}

	.viewer-wrap {
		flex: 1;
		min-height: min(55vh, 420px);
		position: relative;
		background: #0a100c;
	}
</style>
