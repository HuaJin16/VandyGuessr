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
		transition: all 0.2s;
	}

	.dot.completed {
		background: #2e933c;
	}

	.dot.current {
		background: #f4c430;
		box-shadow: 0 0 0 3px rgba(244, 196, 48, 0.3);
	}

	.dot.upcoming {
		background: rgba(24, 24, 27, 0.15);
	}
</style>
