<script lang="ts">
import { gameQueries } from "$lib/domains/games/queries/games.queries";
import { buildGameShareText } from "$lib/domains/games/share";
import type { Game, Round } from "$lib/domains/games/types";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import { createQuery } from "@tanstack/svelte-query";
import L from "leaflet";
import { tick } from "svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

export let id: string;

$: gameQuery = createQuery({ ...gameQueries.byId(id), enabled: $auth.isInitialized });
$: game = $gameQuery.data as Game | undefined;

$: playedRounds = game?.rounds.filter((r) => r.guess && !r.skipped) ?? [];
$: avgScore =
	playedRounds.length > 0
		? Math.round(playedRounds.reduce((sum, r) => sum + (r.score ?? 0), 0) / playedRounds.length)
		: 0;

$: bestRound =
	playedRounds.length > 0
		? playedRounds.reduce((best, r) => ((r.score ?? 0) > (best.score ?? 0) ? r : best))
		: null;
$: worstRound =
	playedRounds.length > 0
		? playedRounds.reduce((worst, r) => ((r.score ?? 0) < (worst.score ?? 0) ? r : worst))
		: null;

$: maxRoundScore =
	playedRounds.length > 0 ? Math.max(...playedRounds.map((r) => r.score ?? 0), 1) : 5000;

function formatDistance(meters: number | null): string {
	if (meters === null) return "\u2014";
	if (meters < 1000) return `${Math.round(meters)}m`;
	return `${(meters / 1000).toFixed(1)}km`;
}

function computeTimeTaken(r: Round): string {
	if (!r.startedAt) return "\u2014";
	const start = new Date(r.startedAt).getTime();
	const end = r.guessedAt ? new Date(r.guessedAt).getTime() : Date.now();
	const diffMs = Math.max(0, end - start);
	const totalSec = Math.floor(diffMs / 1000);
	const mins = String(Math.floor(totalSec / 60)).padStart(2, "0");
	const secs = String(totalSec % 60).padStart(2, "0");
	return `${mins}:${secs}`;
}

function roundClass(r: Round): string {
	if (r.skipped || (!r.guess && r.score === null)) return "skipped";
	if (bestRound && r.roundId === bestRound.roundId) return "best";
	if (worstRound && r.roundId === worstRound.roundId && bestRound?.roundId !== worstRound?.roundId)
		return "worst";
	return "";
}

function barClass(r: Round): string {
	const rc = roundClass(r);
	if (rc === "best") return "round-bar best";
	if (rc === "worst") return "round-bar worst";
	return "round-bar";
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

	const textArea = document.createElement("textarea");
	textArea.value = text;
	textArea.setAttribute("readonly", "");
	textArea.style.position = "fixed";
	textArea.style.opacity = "0";
	document.body.append(textArea);
	textArea.select();

	const copied = document.execCommand("copy");
	textArea.remove();

	if (!copied) {
		throw new Error("Clipboard is not available on this device");
	}
}

let isSharing = false;

async function handleShare() {
	if (!game || isSharing) return;

	isSharing = true;
	const shareText = buildGameShareText(game, window.location.origin);

	try {
		if (navigator.share) {
			try {
				await navigator.share({
					title: "VandyGuessr Results",
					text: shareText,
				});
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

let miniMapEls: HTMLDivElement[] = [];
let mapsInitialized = false;

$: if (game && !mapsInitialized) {
	tick().then(() => initMiniMaps());
}

function initMiniMaps() {
	if (!game || mapsInitialized) return;
	mapsInitialized = true;

	for (let i = 0; i < game.rounds.length; i++) {
		const round = game.rounds[i];
		const el = miniMapEls[i];
		if (!el || !round.guess || !round.actual) continue;

		const map = L.map(el, {
			zoomControl: false,
			attributionControl: false,
			dragging: false,
			scrollWheelZoom: false,
			doubleClickZoom: false,
			boxZoom: false,
			keyboard: false,
			touchZoom: false,
		});

		L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);

		const bounds = L.latLngBounds(
			[round.guess.lat, round.guess.lng],
			[round.actual.lat, round.actual.lng],
		);
		map.fitBounds(bounds.pad(0.85), { maxZoom: 17 });

		L.polyline(
			[
				[round.guess.lat, round.guess.lng],
				[round.actual.lat, round.actual.lng],
			],
			{ color: "#5c6370", weight: 2, dashArray: "5 4" },
		).addTo(map);

		L.circleMarker([round.guess.lat, round.guess.lng], {
			radius: 5,
			color: "#fff",
			fillColor: "#2e933c",
			fillOpacity: 1,
			weight: 2,
		}).addTo(map);

		L.circleMarker([round.actual.lat, round.actual.lng], {
			radius: 5,
			color: "#fff",
			fillColor: "#e8a817",
			fillOpacity: 1,
			weight: 2,
		}).addTo(map);
	}
}
</script>

{#if $gameQuery.isLoading}
	<div class="loading-screen">
		<div class="loading-spinner" />
	</div>
{:else if $gameQuery.isError || !game}
	<div class="error-screen">
		<p class="error-text">Failed to load game</p>
		<button class="btn-3d" on:click={() => navigate("/", { replace: true })}>Go Home</button>
	</div>
{:else}
	<div class="summary-page">
		<Navbar />

		<main class="main">
			<!-- Score Card -->
			<section class="card">
				<p class="section-label">Final Score</p>
				<div class="score-area">
					<div class="score-left">
						<div class="score-row">
							<span class="score">{game.totalScore.toLocaleString()}</span>
							<span class="score-unit">points</span>
						</div>
					</div>
					<div class="round-chart-wrap">
						<p class="round-chart-label">Per Round</p>
						<div class="round-chart">
							{#each game.rounds as round}
								{@const score = round.score ?? 0}
								{@const height = Math.max(2, (score / maxRoundScore) * 56)}
								<div class="round-bar-col">
									<div class={barClass(round)} style="height: {height}px;"></div>
									<span class="round-bar-num">{score.toLocaleString()}</span>
								</div>
							{/each}
						</div>
					</div>
				</div>

				<div class="stats">
					<article class="stat">
						<p class="stat-label">Avg</p>
						<p class="stat-value">{avgScore.toLocaleString()}</p>
					</article>
					<article class="stat">
						<p class="stat-label">Best</p>
						<p class="stat-value" style="color: var(--brand);">
							{bestRound ? (bestRound.score ?? 0).toLocaleString() : "\u2014"}
						</p>
					</article>
					<article class="stat">
						<p class="stat-label">Worst</p>
						<p class="stat-value" style="color: var(--danger);">
							{worstRound && bestRound?.roundId !== worstRound?.roundId
								? (worstRound.score ?? 0).toLocaleString()
								: "\u2014"}
						</p>
					</article>
				</div>

				<div class="buttons">
					<button class="play-btn" type="button" on:click={() => navigate("/", { replace: true })}>
						Play Again
					</button>
					<button class="share-btn" type="button" on:click={handleShare} disabled={isSharing}>
						{isSharing ? "Sharing..." : "Share Results"}
					</button>
				</div>
			</section>

			<!-- Breakdown Card -->
			<section class="card">
				<p class="section-label">Per Location Breakdown</p>
				<div class="round-list">
					{#each game.rounds as round, i}
						{@const status = roundClass(round)}
						<article class="round-row" class:best={status === "best"} class:worst={status === "worst"}>
							<div
								bind:this={miniMapEls[i]}
								class="mini-map"
								aria-label="Round {i + 1} map thumbnail"
							></div>
							<div class="round-meta">
								<h3>Round {i + 1}{round.location_name ? ` \u2014 ${round.location_name}` : ""}</h3>
								{#if status === "skipped"}
									<p class="round-detail">Skipped</p>
								{:else}
									<p class="round-detail">{formatDistance(round.distanceMeters)} · {computeTimeTaken(round)}</p>
								{/if}
							</div>
							{#if status === "skipped"}
								<span class="round-score skipped">Skipped</span>
							{:else}
								<span class="round-score">{(round.score ?? 0).toLocaleString()}</span>
							{/if}
						</article>
					{/each}
				</div>
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
		width: min(700px, calc(100% - 32px));
		margin: 16px auto 24px;
		display: grid;
		gap: 14px;
	}

	.card {
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-sm);
		padding: 16px;
	}

	.section-label {
		margin: 0;
		color: var(--muted);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	/* Score area */
	.score-area {
		margin-top: 12px;
	}

	.score-row {
		display: flex;
		align-items: baseline;
		gap: 8px;
		flex-wrap: wrap;
	}

	.score {
		font-family: "IBM Plex Mono", monospace;
		font-size: 48px;
		line-height: 1;
		font-weight: 700;
		color: var(--brand);
	}

	.score-unit {
		font-family: "IBM Plex Mono", monospace;
		color: var(--muted);
		font-size: 14px;
		font-weight: 600;
	}

	/* Round chart */
	.round-chart-wrap {
		margin-top: 14px;
		display: flex;
		flex-direction: column;
	}

	.round-chart-label {
		margin: 0 0 6px;
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.round-chart {
		display: flex;
		align-items: flex-end;
		gap: 6px;
		height: 64px;
	}

	.round-bar-col {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
	}

	.round-bar {
		width: 100%;
		border-radius: 3px 3px 0 0;
		background: var(--line);
		transition: background 120ms var(--ease);
	}

	.round-bar.best { background: var(--brand); }
	.round-bar.worst { background: var(--danger); }

	.round-bar-num {
		font-size: 10px;
		font-family: "IBM Plex Mono", monospace;
		font-weight: 500;
		color: var(--muted);
	}

	/* Stats */
	.stats {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 8px;
		margin-top: 18px;
	}

	/* Buttons */
	.buttons {
		margin-top: 18px;
		display: grid;
		gap: 10px;
	}

	.play-btn {
		width: 100%;
		border: none;
		border-radius: var(--radius-md);
		background: var(--brand);
		color: #fff;
		font-family: Inter, sans-serif;
		font-size: 15px;
		font-weight: 700;
		padding: 12px 14px;
		box-shadow: 0 4px 0 var(--brand-dark);
		cursor: pointer;
		transition: all 120ms var(--ease);
	}

	.play-btn:hover { background: #278234; }
	.play-btn:active { transform: translateY(4px); box-shadow: 0 0 0 var(--brand-dark); }
	.play-btn:focus-visible { outline: none; box-shadow: 0 4px 0 var(--brand-dark), var(--ring); }

	.share-btn {
		width: 100%;
		border: 2px solid var(--gold);
		border-radius: var(--radius-md);
		background: linear-gradient(105deg, var(--gold-light), transparent 68%), var(--surface);
		color: var(--gold-dark);
		font-family: Inter, sans-serif;
		font-size: 15px;
		font-weight: 700;
		padding: 12px 14px;
		box-shadow: 0 4px 0 var(--gold-dark);
		cursor: pointer;
		transition: all 120ms var(--ease);
	}

	.share-btn:hover {
		background: linear-gradient(105deg, rgba(232, 168, 23, 0.22), transparent 68%),
			var(--surface);
	}

	.share-btn:active {
		transform: translateY(4px);
		box-shadow: 0 0 0 var(--gold-dark);
	}

	.share-btn:focus-visible {
		outline: none;
		box-shadow: 0 4px 0 var(--gold-dark), 0 0 0 3px rgba(232, 168, 23, 0.24);
	}

	.share-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		pointer-events: none;
	}

	/* Round list */
	.round-list {
		display: grid;
		gap: 0;
		margin-top: 12px;
	}

	.round-row {
		border-bottom: 1px solid var(--line);
		background: var(--surface);
		padding: 12px 6px 12px 0;
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.round-row:last-child { border-bottom: none; }
	.round-row.best { background: rgba(46, 147, 60, 0.04); }
	.round-row.worst { background: rgba(220, 74, 58, 0.04); }

	.mini-map {
		width: 80px;
		height: 60px;
		border: 1px solid var(--line);
		border-radius: var(--radius-sm);
		overflow: hidden;
		background: #ece7d8;
		flex-shrink: 0;
		isolation: isolate;
	}

	.mini-map :global(.leaflet-tile-pane) {
		filter: saturate(0.2) sepia(20%) brightness(1.06) contrast(0.95);
	}

	.round-meta {
		flex: 1;
		min-width: 0;
	}

	.round-meta h3 {
		margin: 0;
		font-size: 15px;
		font-weight: 600;
		line-height: 1.2;
		color: var(--ink);
	}

	.round-detail {
		margin: 2px 0 0;
		font-size: 12px;
		color: var(--muted);
	}

	.round-score {
		font-family: "IBM Plex Mono", monospace;
		font-size: 18px;
		font-weight: 700;
		color: var(--ink);
		flex-shrink: 0;
		text-align: right;
	}

	.round-score.skipped {
		color: var(--muted);
		font-size: 13px;
		font-weight: 600;
		font-family: Inter, sans-serif;
	}

	/* Loading / Error */
	.loading-screen {
		position: fixed;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--canvas);
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 4px solid var(--line);
		border-top-color: var(--brand);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

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

	@media (min-width: 700px) {
		.card { padding: 18px; }
		.round-row { padding: 14px 6px 14px 0; }
		.mini-map { width: 100px; height: 70px; }
	}

	@media (min-width: 540px) {
		.buttons {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 500px) {
		.score { font-size: 36px; }
		.mini-map { width: 60px; height: 45px; }
		.round-score { font-size: 15px; }
		.round-meta h3 { font-size: 14px; }
		.stats { gap: 6px; }
	}
</style>
