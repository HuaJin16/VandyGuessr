<script lang="ts">
export let total = 5;
export let completed = 0;
export let current = 0;
</script>

<div class="dots">
	{#each Array(total) as _, i}
		<div
			class="dot"
			class:completed={i < completed}
			class:current={i === current}
			class:upcoming={i > current}
		/>
	{/each}
</div>

<style>
	.dots {
		display: flex;
		gap: 8px;
		justify-content: center;
	}

	.dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		transition: all 200ms var(--ease);
	}

	.dot.completed {
		background: var(--brand);
	}

	.dot.current {
		background: var(--gold);
		box-shadow: 0 0 0 3px rgba(232, 168, 23, 0.3);
	}

	.dot.upcoming {
		background: var(--line);
	}
</style>
