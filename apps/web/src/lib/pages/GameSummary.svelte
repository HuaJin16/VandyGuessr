<script lang="ts">
import Confetti from "$lib/domains/games/components/Confetti.svelte";
import ResultsMap from "$lib/domains/games/components/ResultsMap.svelte";
import { gameQueries } from "$lib/domains/games/queries/games.queries";
import {
	computeTimeTaken,
	formatDistance,
	getBarColor,
	getGameQuality,
	getRoundQuality,
} from "$lib/domains/games/score-quality";
import { buildGameShareText, getRoundShareEmoji } from "$lib/domains/games/share";
import type { Game, Round } from "$lib/domains/games/types";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import Button from "$lib/shared/ui/Button.svelte";
import Spinner from "$lib/shared/ui/Spinner.svelte";
import { createQuery } from "@tanstack/svelte-query";
import { onMount } from "svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

export let id: string;

$: gameQuery = createQuery({
	...gameQueries.byId(id, $auth.currentUserOid),
	enabled: $auth.currentUserOid !== null,
});
$: game = $gameQuery.data as Game | undefined;

$: playedRounds = game?.rounds.filter((r) => r.guess && !r.skipped) ?? [];
$: maxScore = game ? game.rounds.length * 5000 : 25000;
$: quality = game ? getGameQuality(game.totalScore, game.rounds.length) : null;
$: emojiGrid = game ? game.rounds.map(getRoundShareEmoji).join("") : "";

$: avgScore =
	playedRounds.length > 0
		? Math.round(playedRounds.reduce((sum, r) => sum + (r.score ?? 0), 0) / playedRounds.length)
		: 0;

$: bestRound =
	playedRounds.length > 0
		? playedRounds.reduce((b, r) => ((r.score ?? 0) > (b.score ?? 0) ? r : b))
		: null;

$: worstRound =
	playedRounds.length > 0
		? playedRounds.reduce((w, r) => ((r.score ?? 0) < (w.score ?? 0) ? r : w))
		: null;

$: maxRoundScore =
	playedRounds.length > 0 ? Math.max(...playedRounds.map((r) => r.score ?? 0), 1) : 5000;

let showQuality = false;

onMount(() => {
	requestAnimationFrame(() => {
		showQuality = true;
	});
});

function formatDifficultyLabel(d: Game["mode"]["difficulty"]): string {
	return d.charAt(0).toUpperCase() + d.slice(1);
}

function modeTags(value: Game): string[] {
	const tags = [value.mode.timed ? "Timed" : "Untimed"];
	if (value.mode.environment === "indoor") tags.push("Indoor");
	else if (value.mode.environment === "outdoor") tags.push("Outdoor");
	tags.push(value.mode.daily ? "Daily" : "Random Drop");
	tags.push(formatDifficultyLabel(value.mode.difficulty));
	return tags;
}

function roundLabel(round: Round, index: number): string {
	const name = round.location_name ? ` \u2014 ${round.location_name}` : "";
	return `Round ${index + 1}${name}`;
}

function isSkipped(round: Round): boolean {
	return round.skipped || (!round.guess && round.score === null);
}

function getErrorName(error: unknown): string | null {
	if (typeof error !== "object" || error === null) return null;
	const name = Reflect.get(error, "name");
	return typeof name === "string" ? name : null;
}

async function copyShareText(text: string) {
	if (navigator.clipboard?.writeText) {
		await navigator.clipboard.writeText(text);
		return;
	}
	const ta = document.createElement("textarea");
	ta.value = text;
	ta.setAttribute("readonly", "");
	ta.style.position = "fixed";
	ta.style.opacity = "0";
	document.body.append(ta);
	ta.select();
	const copied = document.execCommand("copy");
	ta.remove();
	if (!copied) throw new Error("Clipboard is not available on this device");
}

let isSharing = false;

async function handleShare() {
	if (!game || isSharing) return;
	isSharing = true;
	const shareText = buildGameShareText(game, window.location.origin);
	try {
		if (navigator.share) {
			try {
				await navigator.share({ title: "VandyGuessr Results", text: shareText });
				return;
			} catch (error) {
				if (getErrorName(error) === "AbortError") return;
			}
		}
		await copyShareText(shareText);
		toast.success("Results copied to clipboard");
	} catch (error) {
		toast.error(error instanceof Error ? error.message : "Failed to share results");
	} finally {
		isSharing = false;
	}
}
</script>

{#if $gameQuery.isLoading}
	<div class="loading-screen">
		<Spinner />
	</div>
{:else if $gameQuery.isError || !game || !quality}
	<div class="error-screen">
		<p class="error-text">Failed to load game</p>
		<Button on:click={() => navigate("/", { replace: true })}>Go Home</Button>
	</div>
{:else}
	{#if quality.confetti}
		<Confetti />
	{/if}

	<div class="summary-page">
		<Navbar />

		<main class="main">
			<section class="hero">
				<span
					class="quality-word"
					class:visible={showQuality}
					style="color: {quality.color}"
				>
					{quality.word}
				</span>

				<div class="score-row">
					<span class="hero-score" style="color: {quality.color}">
						{game.totalScore.toLocaleString()}
					</span>
					<span class="hero-max">/ {maxScore.toLocaleString()}</span>
				</div>

				<div class="emoji-grid" aria-label="Round results as emoji">{emojiGrid}</div>

				<div class="mode-tags">
					{#each modeTags(game) as tag}
						<span class="mode-tag">{tag}</span>
					{/each}
				</div>
			</section>

			<section class="chart-section">
				<div class="bar-chart">
					{#each game.rounds as round, i}
						{@const score = round.score ?? 0}
						{@const height = Math.max(3, (score / maxRoundScore) * 120)}
						<div class="bar-col">
							<div
								class="bar"
								style="height: {height}px; background: {getBarColor(round.score)}; animation-delay: {i * 80}ms;"
							/>
							<span class="bar-label">{score.toLocaleString()}</span>
						</div>
					{/each}
				</div>
			</section>

			<section class="stats-row">
				<div class="stat-item">
					<span class="stat-label">Avg score</span>
					<span class="stat-value">{avgScore.toLocaleString()}</span>
				</div>
				<span class="stat-sep" />
				<div class="stat-item">
					<span class="stat-label">Best round</span>
					<span class="stat-value">
						{bestRound ? (bestRound.score ?? 0).toLocaleString() : "\u2014"}
						{#if bestRound?.location_name}
							<span class="stat-location">{bestRound.location_name}</span>
						{/if}
					</span>
				</div>
				<span class="stat-sep" />
				<div class="stat-item">
					<span class="stat-label">Worst round</span>
					<span class="stat-value">
						{#if worstRound && bestRound?.roundId !== worstRound?.roundId}
							{(worstRound.score ?? 0).toLocaleString()}
							{#if worstRound.location_name}
								<span class="stat-location">{worstRound.location_name}</span>
							{/if}
						{:else}
							&mdash;
						{/if}
					</span>
				</div>
			</section>

			<div class="actions">
				<Button size="lg" on:click={() => navigate("/", { replace: true })}>Play Again</Button>
				<Button variant="secondary" size="lg" disabled={isSharing} on:click={handleShare}>
					{isSharing ? "Sharing\u2026" : "Share Results"}
				</Button>
				<button class="link-btn" on:click={() => navigate("/leaderboard")}>Leaderboard</button>
			</div>

			<section class="rounds">
				{#each game.rounds as round, index}
					{@const skipped = isSkipped(round)}
					{@const rq = getRoundQuality(round.score)}
					<article class="round-card">
						<div class="round-card-header">
							<h3>{roundLabel(round, index)}</h3>
							{#if skipped}
								<span class="round-score-label muted">Skipped</span>
							{:else}
								<span class="round-score-label" style="color: {rq.color}">
									{(round.score ?? 0).toLocaleString()}
								</span>
							{/if}
						</div>

						{#if round.guess && round.actual}
							<div class="round-map">
								<ResultsMap
									guess={round.guess}
									actual={round.actual}
									distanceMeters={round.distanceMeters ?? 0}
									locationName={round.location_name}
								/>
						</div>
					{/if}

						{#if !skipped}
							<div class="round-meta">
								<span>{formatDistance(round.distanceMeters)}</span>
								<span class="round-meta-sep">&middot;</span>
								<span>{computeTimeTaken(round)}</span>
							</div>
						{/if}
					</article>
				{/each}
			</section>
		</main>
	</div>
{/if}

<style>
	.summary-page {
		min-height: 100vh;
		background: var(--canvas);
	}

	.main {
		width: min(720px, calc(100% - 32px));
		margin: 16px auto 40px;
		display: grid;
		gap: 24px;
	}

	/* Hero */
	.hero {
		display: grid;
		gap: 10px;
		text-align: center;
		padding: 8px 0;
	}

	.quality-word {
		font-size: clamp(24px, 5vw, 36px);
		font-weight: 800;
		letter-spacing: -0.03em;
		line-height: 1;
		opacity: 0;
		transform: scale(0.7);
		transition: opacity 400ms var(--ease), transform 400ms var(--ease);
	}

	.quality-word.visible {
		opacity: 1;
		transform: scale(1);
	}

	.score-row {
		display: flex;
		align-items: baseline;
		justify-content: center;
		gap: 8px;
	}

	.hero-score {
		font-family: "IBM Plex Mono", monospace;
		font-size: clamp(48px, 9vw, 72px);
		font-weight: 700;
		line-height: 0.95;
	}

	.hero-max {
		font-family: "IBM Plex Mono", monospace;
		font-size: clamp(16px, 3vw, 20px);
		font-weight: 600;
		color: var(--muted);
	}

	.emoji-grid {
		font-size: 24px;
		letter-spacing: 4px;
		line-height: 1;
	}

	.mode-tags {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		justify-content: center;
	}

	.mode-tag {
		border-radius: var(--radius-pill);
		background: var(--surface-strong);
		color: var(--muted);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.06em;
		padding: 4px 10px;
		text-transform: uppercase;
	}

	/* Bar chart */
	.chart-section {
		padding: 0 8px;
	}

	.bar-chart {
		display: flex;
		align-items: flex-end;
		gap: 8px;
		height: 140px;
	}

	.bar-col {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
	}

	.bar {
		width: 100%;
		border-radius: 4px 4px 0 0;
		transform-origin: bottom;
		animation: barGrow 0.5s var(--ease) both;
	}

	@keyframes barGrow {
		from {
			transform: scaleY(0);
		}
		to {
			transform: scaleY(1);
		}
	}

	.bar-label {
		font-size: 11px;
		font-family: "IBM Plex Mono", monospace;
		font-weight: 600;
		color: var(--muted);
	}

	/* Stats row */
	.stats-row {
		display: flex;
		align-items: flex-start;
		gap: 16px;
		padding: 16px 0;
		border-top: 1px solid var(--line);
		border-bottom: 1px solid var(--line);
	}

	.stat-item {
		flex: 1;
		display: grid;
		gap: 2px;
	}

	.stat-label {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.stat-value {
		font-family: "IBM Plex Mono", monospace;
		font-size: 18px;
		font-weight: 600;
		color: var(--ink);
		line-height: 1.3;
	}

	.stat-location {
		display: block;
		font-family: "Inter", sans-serif;
		font-size: 12px;
		font-weight: 500;
		color: var(--muted);
		margin-top: 2px;
	}

	.stat-sep {
		width: 1px;
		height: 36px;
		background: var(--line);
		flex-shrink: 0;
		margin-top: 4px;
	}

	/* Actions */
	.actions {
		display: flex;
		align-items: center;
		gap: 10px;
		flex-wrap: wrap;
	}

	.link-btn {
		background: none;
		border: none;
		padding: 8px 4px;
		font-size: 14px;
		font-weight: 600;
		color: var(--muted);
		cursor: pointer;
		transition: color var(--duration-fast) var(--ease);
	}

	.link-btn:hover {
		color: var(--ink);
	}

	/* Round cards */
	.rounds {
		display: grid;
		gap: 14px;
	}

	.round-card {
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		background: var(--surface);
		overflow: hidden;
	}

	.round-card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 14px 16px;
	}

	.round-card-header h3 {
		margin: 0;
		font-size: 15px;
		font-weight: 700;
		line-height: 1.3;
	}

	.round-score-label {
		font-family: "IBM Plex Mono", monospace;
		font-size: 16px;
		font-weight: 700;
		white-space: nowrap;
		flex-shrink: 0;
	}

	.round-score-label.muted {
		font-family: "Inter", sans-serif;
		font-size: 13px;
		font-weight: 600;
		color: var(--muted);
	}

	.round-map {
		position: relative;
		height: 220px;
		border-top: 1px solid var(--line);
		border-bottom: 1px solid var(--line);
		overflow: hidden;
		isolation: isolate;
		z-index: 0;
	}

	.round-meta {
		padding: 10px 16px;
		font-size: 13px;
		font-family: "IBM Plex Mono", monospace;
		font-weight: 500;
		color: var(--muted);
		display: flex;
		gap: 8px;
	}

	.round-meta-sep {
		opacity: 0.5;
	}

	/* Loading / Error */
	.loading-screen,
	.error-screen {
		position: fixed;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 16px;
		background: var(--canvas);
	}

	.error-text {
		font-size: 16px;
		font-weight: 500;
		color: var(--muted);
	}

	@media (max-width: 640px) {
		.stats-row {
			flex-direction: column;
			gap: 12px;
		}

		.stat-sep {
			display: none;
		}

		.stat-item {
			flex-direction: row;
			align-items: baseline;
			gap: 8px;
		}

		.stat-location {
			display: inline;
			margin-top: 0;
			margin-left: 4px;
		}

		.actions {
			flex-direction: column;
			align-items: stretch;
		}

		.link-btn {
			text-align: center;
		}

		.round-map {
			height: 180px;
		}
	}
</style>
