<script lang="ts">
export let size = 40;

$: borderWidth = size <= 36 ? 3 : 4;
</script>

<div
	class="spinner"
	style="width: {size}px; height: {size}px; border-width: {borderWidth}px;"
	role="status"
	aria-label="Loading"
/>

<style>
	.spinner {
		border-style: solid;
		border-color: var(--line);
		border-top-color: var(--brand);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
