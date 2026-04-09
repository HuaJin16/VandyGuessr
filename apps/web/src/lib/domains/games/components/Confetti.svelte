<script lang="ts">
import { onMount } from "svelte";

const PARTICLE_COUNT = 35;
const COLORS = ["#2e933c", "#1f7a2b", "#e8a817", "#b4820d", "#ffffff", "#d6d3d1"];
const DURATION_MS = 3500;

interface Particle {
	x: number;
	delay: number;
	duration: number;
	size: number;
	color: string;
	rotation: number;
	drift: number;
}

let particles: Particle[] = [];
let visible = true;

function createParticles(): Particle[] {
	const result: Particle[] = [];
	for (let i = 0; i < PARTICLE_COUNT; i++) {
		result.push({
			x: Math.random() * 100,
			delay: Math.random() * 800,
			duration: 1800 + Math.random() * 1200,
			size: 6 + Math.random() * 6,
			color: COLORS[Math.floor(Math.random() * COLORS.length)],
			rotation: Math.random() * 360,
			drift: -30 + Math.random() * 60,
		});
	}
	return result;
}

onMount(() => {
	particles = createParticles();
	const timer = setTimeout(() => {
		visible = false;
	}, DURATION_MS);
	return () => clearTimeout(timer);
});
</script>

{#if visible}
	<div class="confetti-container" aria-hidden="true">
		{#each particles as p}
			<div
				class="confetti-particle"
				style="
					left: {p.x}%;
					width: {p.size}px;
					height: {p.size * 0.6}px;
					background: {p.color};
					animation-delay: {p.delay}ms;
					animation-duration: {p.duration}ms;
					--drift: {p.drift}px;
					--rotation: {p.rotation}deg;
				"
			/>
		{/each}
	</div>
{/if}

<style>
	.confetti-container {
		position: fixed;
		inset: 0;
		pointer-events: none;
		z-index: 9999;
		overflow: hidden;
	}

	.confetti-particle {
		position: absolute;
		top: -12px;
		border-radius: 2px;
		animation: confetti-fall var(--duration, 2s) var(--ease, ease-out) forwards;
		animation-fill-mode: forwards;
		opacity: 0;
	}

	@keyframes confetti-fall {
		0% {
			opacity: 1;
			transform: translateY(0) translateX(0) rotate(0deg);
		}
		75% {
			opacity: 1;
		}
		100% {
			opacity: 0;
			transform: translateY(100vh) translateX(var(--drift)) rotate(calc(var(--rotation) + 540deg));
		}
	}
</style>
