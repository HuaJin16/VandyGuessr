<script lang="ts">
import { gamesService } from "$lib/domains/games/api/games.service";
import { gameQueries } from "$lib/domains/games/queries/games.queries";
import type { Game, Round } from "$lib/domains/games/types";
import { auth } from "$lib/shared/auth/auth.store";
import { createQuery } from "@tanstack/svelte-query";
import { LogOut, Trophy as TrophyIcon } from "lucide-svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";
import logo from "../../assets/logo.webp";

export let id: string;

$: gameQuery = createQuery({ ...gameQueries.byId(id), enabled: $auth.isInitialized });
$: game = $gameQuery.data as Game | undefined;

$: maxScore = game ? game.rounds.length * 5000 : 25000;
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

function getRating(score: number, max: number): string {
	const pct = max > 0 ? score / max : 0;
	if (pct >= 1) return "Perfect!";
	if (pct >= 0.8) return "Great Game!";
	if (pct >= 0.6) return "Good Job!";
	if (pct >= 0.4) return "Nice Try!";
	return "Keep Practicing";
}

function formatDistance(meters: number | null): string {
	if (meters === null) return "\u2014";
	if (meters < 1000) return `${Math.round(meters)}m`;
	return `${(meters / 1000).toFixed(1)}km`;
}

function modeLabel(g: Game): string {
	const parts: string[] = [];
	parts.push(g.mode.timed ? "Timed" : "Untimed");
	if (g.mode.environment === "indoor") parts.push("Indoor");
	else if (g.mode.environment === "outdoor") parts.push("Outdoor");
	else parts.push("Any");
	parts.push(g.mode.daily ? "Daily" : "Random Drop");
	return parts.join(" \u00b7 ");
}

function modePills(g: Game): Array<{ label: string; icon: string; color: string; bg: string }> {
	const pills: Array<{ label: string; icon: string; color: string; bg: string }> = [];
	pills.push(
		g.mode.timed
			? { label: "Timed", icon: "timer", color: "text-clay", bg: "bg-clay/10" }
			: { label: "Untimed", icon: "all_inclusive", color: "text-charcoal/60", bg: "bg-charcoal/5" },
	);
	if (g.mode.environment === "indoor")
		pills.push({ label: "Indoor", icon: "home", color: "text-violet-600", bg: "bg-violet-500/10" });
	else if (g.mode.environment === "outdoor")
		pills.push({ label: "Outdoor", icon: "park", color: "text-teal-600", bg: "bg-teal-500/10" });
	pills.push(
		g.mode.daily
			? { label: "Daily", icon: "calendar_today", color: "text-gold", bg: "bg-gold/10" }
			: { label: "Random Drop", icon: "casino", color: "text-jungle", bg: "bg-jungle/10" },
	);
	return pills;
}

function roundStatus(
	r: Round,
	best: Round | null,
	worst: Round | null,
): "best" | "worst" | "skipped" | "normal" {
	if (r.skipped || (!r.guess && r.score === null)) return "skipped";
	if (best && r.roundId === best.roundId) return "best";
	if (worst && r.roundId === worst.roundId && best?.roundId !== worst?.roundId) return "worst";
	return "normal";
}

let starting = false;

async function playAgain() {
	if (!game || starting) return;
	starting = true;
	try {
		const newGame = await gamesService.start({ mode: game.mode });
		navigate(`/game/${newGame.id}`);
	} catch (err: unknown) {
		const e = err as { response?: { data?: { detail?: string } }; message?: string };
		toast.error(e?.response?.data?.detail || e?.message || "Failed to start game");
	} finally {
		starting = false;
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
	<div class="min-h-screen bg-terrain font-body">
		<!-- Background -->
		<div class="fixed inset-0 z-0">
			<div class="absolute inset-0 scale-110 bg-terrain bg-cover bg-center blur-[24px]"></div>
			<div class="absolute inset-0 bg-terrain/80"></div>
		</div>

		<div class="relative z-10 min-h-screen flex flex-col">
			<!-- Navbar -->
			<header class="sticky top-0 z-50 border-b border-gray-100 bg-white">
				<div class="mx-auto flex max-w-4xl items-center justify-between px-4 py-3 sm:px-6 sm:py-4">
					<a href="/" class="flex items-center gap-2 sm:gap-3">
						<img src={logo} alt="VandyGuessr" class="h-9 w-9 sm:h-10 sm:w-10" />
						<span class="font-heading text-lg font-bold text-charcoal hidden sm:block">VandyGuessr</span>
					</a>
					<div class="flex items-center gap-1 sm:gap-2">
						<a
							href="/leaderboard"
							class="flex items-center gap-1.5 rounded-lg p-2 text-xs font-medium text-charcoal/60 transition-colors hover:bg-charcoal/5 hover:text-jungle sm:text-sm"
						>
							<TrophyIcon size={18} />
							<span class="hidden sm:inline">Leaderboard</span>
						</a>
						<button
							class="flex items-center gap-1.5 rounded-lg p-2 text-xs font-medium text-charcoal/50 transition-colors hover:bg-charcoal/5 hover:text-clay sm:text-sm"
							on:click={() => auth.logout()}
						>
							<LogOut size={18} />
							<span class="hidden sm:inline">Logout</span>
						</button>
					</div>
				</div>
			</header>

			<!-- Content -->
			<main class="flex-1 flex flex-col items-center px-4 py-6 sm:py-8 gap-4 sm:gap-5">

				<!-- Map Strip -->
				<div class="map-strip w-full max-w-2xl">
					<div class="map-bg">
						<div class="map-grid"></div>
					</div>

					<!-- Pin pairs for each round -->
					{#each game.rounds as round, i}
						{@const xBase = 10 + i * (80 / Math.max(game.rounds.length - 1, 1))}
						{@const status = roundStatus(round, bestRound, worstRound)}
						{#if status === "skipped"}
							<div class="absolute z-20 opacity-30" style="left: {xBase + 2}%; top: 35%;">
								<span class="material-symbols-outlined text-charcoal text-2xl drop-shadow-md" style="font-variation-settings: 'FILL' 1;">flag</span>
							</div>
							<div class="round-label opacity-40" style="left: {xBase + 1}%; top: 8%;">
								{i + 1}
							</div>
						{:else if round.guess && round.actual}
							<div class="absolute z-20" style="left: {xBase}%; top: {25 + (i % 3) * 15}%;">
								<span class="material-symbols-outlined text-jungle text-2xl drop-shadow-md" style="font-variation-settings: 'FILL' 1;">location_on</span>
							</div>
							<div class="absolute z-20" style="left: {xBase + 5}%; top: {15 + (i % 2) * 10}%;">
								<span class="material-symbols-outlined text-gold text-2xl drop-shadow-md" style="font-variation-settings: 'FILL' 1;">flag</span>
							</div>
							<svg class="absolute inset-0 w-full h-full z-10 pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
								<line
									x1="{xBase + 1}"
									y1="{30 + (i % 3) * 15}"
									x2="{xBase + 6}"
									y2="{20 + (i % 2) * 10}"
									stroke="#18181B"
									stroke-width="0.3"
									class="dashed-line"
									stroke-linecap="round"
								/>
							</svg>
							<div
								class="round-label"
								class:round-label--best={status === "best"}
								style="left: {xBase + 2}%; top: 8%;"
							>
								{i + 1}
							</div>
						{/if}
					{/each}

					<!-- Legend -->
					<div class="map-legend">
						<div class="flex items-center gap-1">
							<span class="material-symbols-outlined text-jungle text-sm" style="font-variation-settings: 'FILL' 1;">location_on</span>
							<span class="text-[10px] font-semibold text-charcoal/60">Guess</span>
						</div>
						<div class="w-px h-3 bg-gray-300"></div>
						<div class="flex items-center gap-1">
							<span class="material-symbols-outlined text-gold text-sm" style="font-variation-settings: 'FILL' 1;">flag</span>
							<span class="text-[10px] font-semibold text-charcoal/60">Actual</span>
						</div>
					</div>
				</div>

				<!-- Glass Card -->
				<div class="glass-card w-full max-w-2xl border border-white/50 overflow-hidden">

					<!-- Hero: Total Score -->
					<div class="px-6 sm:px-8 pt-6 sm:pt-8 pb-5 sm:pb-6 text-center">
						<div class="flex justify-center mb-3">
							<div class="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-gold/20 flex items-center justify-center">
								<span class="material-symbols-outlined text-gold text-4xl sm:text-5xl" style="font-variation-settings: 'FILL' 1;">emoji_events</span>
							</div>
						</div>
						<p class="text-xs sm:text-sm font-bold text-gold uppercase tracking-wider mb-2">
							{getRating(game.totalScore, maxScore)}
						</p>

						<div class="flex items-baseline justify-center gap-2 sm:gap-3 mb-1">
							<span class="score-pop font-heading font-bold text-5xl sm:text-6xl text-charcoal">
								{game.totalScore.toLocaleString()}
							</span>
							<span class="text-charcoal/40 font-mono text-lg sm:text-xl">pts</span>
						</div>

						<p class="text-xs text-charcoal/40 font-mono mb-4">out of {maxScore.toLocaleString()}</p>

						<!-- Mode Pills -->
						<div class="flex flex-wrap justify-center gap-2">
							{#each modePills(game) as pill}
								<span class="inline-flex items-center gap-1 {pill.bg} {pill.color} text-xs font-semibold px-3 py-1 rounded-full">
									<span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">{pill.icon}</span>
									{pill.label}
								</span>
							{/each}
						</div>
					</div>

					<!-- Summary Stats Row -->
					<div class="px-5 sm:px-8">
						<div class="flex gap-3 sm:gap-4 mb-1">
							<div class="flex-1 bg-terrain rounded-xl p-3 sm:p-4 text-center">
								<p class="stat-label">Avg Score</p>
								<p class="font-mono font-bold text-lg sm:text-xl text-charcoal">{avgScore.toLocaleString()}</p>
							</div>
							<div class="flex-1 bg-jungle/5 rounded-xl p-3 sm:p-4 text-center border border-jungle/10">
								<p class="stat-label text-jungle/70">Best Round</p>
								<p class="font-mono font-bold text-lg sm:text-xl text-jungle">
									{bestRound ? (bestRound.score ?? 0).toLocaleString() : "\u2014"}
								</p>
								{#if bestRound}
									<p class="text-[10px] text-jungle/50 font-semibold mt-0.5">Round {bestRound.roundId}</p>
								{/if}
							</div>
							<div class="flex-1 bg-clay/5 rounded-xl p-3 sm:p-4 text-center border border-clay/10">
								<p class="stat-label text-clay/70">Worst Round</p>
								<p class="font-mono font-bold text-lg sm:text-xl text-clay">
									{worstRound && bestRound?.roundId !== worstRound?.roundId ? (worstRound.score ?? 0).toLocaleString() : "\u2014"}
								</p>
								{#if worstRound && bestRound?.roundId !== worstRound?.roundId}
									<p class="text-[10px] text-clay/50 font-semibold mt-0.5">Round {worstRound.roundId}</p>
								{/if}
							</div>
						</div>
					</div>

					<!-- Per-Round Breakdown -->
					<div class="p-5 sm:p-6 pt-4 sm:pt-5">
						<h3 class="font-heading font-bold text-base sm:text-lg text-charcoal mb-3 flex items-center gap-2">
							<span class="material-symbols-outlined text-charcoal/40 text-lg">format_list_numbered</span>
							Round Breakdown
						</h3>

						<div class="space-y-2 sm:space-y-2.5">
							{#each game.rounds as round, i}
								{@const status = roundStatus(round, bestRound, worstRound)}
								{#if status === "skipped"}
									<!-- Skipped Round -->
									<div class="round-card round-card--skipped">
										<div class="flex items-start gap-3">
											<div class="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
												<span class="font-mono font-bold text-sm text-charcoal/30">{i + 1}</span>
											</div>
											<div class="flex-1 min-w-0">
												<div class="flex items-center justify-between mb-1">
													<div class="flex items-center gap-1.5 min-w-0">
														<p class="font-semibold text-charcoal/40 text-sm truncate">
															{round.location_name ?? `Round ${i + 1}`}
														</p>
														<span class="badge badge--skipped">Skipped</span>
													</div>
													<div class="flex items-baseline gap-1.5 flex-shrink-0 ml-2">
														<span class="font-mono font-bold text-sm text-charcoal/30">0</span>
														<span class="text-[10px] text-charcoal/20 font-mono">pts</span>
													</div>
												</div>
												<div class="h-1.5 bg-gray-100 rounded-full mb-1.5">
													<div class="score-bar h-1.5 bg-gray-200 rounded-full" style="width: 0%;"></div>
												</div>
												<div class="flex items-center justify-between">
													<p class="text-[10px] sm:text-xs text-charcoal/30">Game ended early</p>
													<span class="font-mono text-[10px] sm:text-xs text-charcoal/30">&mdash;</span>
												</div>
											</div>
										</div>
									</div>
								{:else if status === "best"}
									<!-- Best Round -->
									<div class="round-card round-card--best">
										<div class="flex items-start gap-3">
											<div class="w-8 h-8 rounded-lg bg-jungle/10 flex items-center justify-center flex-shrink-0">
												<span class="font-mono font-bold text-sm text-jungle">{i + 1}</span>
											</div>
											<div class="flex-1 min-w-0">
												<div class="flex items-center justify-between mb-1">
													<div class="flex items-center gap-1.5 min-w-0">
														<p class="font-semibold text-charcoal text-sm truncate">
															{round.location_name ?? `Round ${i + 1}`}
														</p>
														<span class="badge badge--best">Best</span>
													</div>
													<div class="flex items-baseline gap-1.5 flex-shrink-0 ml-2">
														<span class="font-mono font-bold text-sm text-jungle">{(round.score ?? 0).toLocaleString()}</span>
														<span class="text-[10px] text-jungle/50 font-mono">pts</span>
													</div>
												</div>
												<div class="h-1.5 bg-jungle/10 rounded-full mb-1.5">
													<div class="score-bar h-1.5 bg-jungle rounded-full" style="width: {((round.score ?? 0) / 5000) * 100}%;"></div>
												</div>
												<div class="flex items-center justify-between">
													<p class="text-[10px] sm:text-xs text-charcoal/40">{round.location_name ?? ""}</p>
													<span class="font-mono text-[10px] sm:text-xs text-charcoal/50">{formatDistance(round.distanceMeters)} away</span>
												</div>
											</div>
										</div>
									</div>
								{:else if status === "worst"}
									<!-- Worst Round -->
									<div class="round-card round-card--worst">
										<div class="flex items-start gap-3">
											<div class="w-8 h-8 rounded-lg bg-clay/10 flex items-center justify-center flex-shrink-0">
												<span class="font-mono font-bold text-sm text-clay">{i + 1}</span>
											</div>
											<div class="flex-1 min-w-0">
												<div class="flex items-center justify-between mb-1">
													<div class="flex items-center gap-1.5 min-w-0">
														<p class="font-semibold text-charcoal text-sm truncate">
															{round.location_name ?? `Round ${i + 1}`}
														</p>
														<span class="badge badge--worst">Worst</span>
													</div>
													<div class="flex items-baseline gap-1.5 flex-shrink-0 ml-2">
														<span class="font-mono font-bold text-sm text-clay">{(round.score ?? 0).toLocaleString()}</span>
														<span class="text-[10px] text-clay/50 font-mono">pts</span>
													</div>
												</div>
												<div class="h-1.5 bg-clay/10 rounded-full mb-1.5">
													<div class="score-bar h-1.5 bg-clay/70 rounded-full" style="width: {((round.score ?? 0) / 5000) * 100}%;"></div>
												</div>
												<div class="flex items-center justify-between">
													<p class="text-[10px] sm:text-xs text-charcoal/40">{round.location_name ?? ""}</p>
													<span class="font-mono text-[10px] sm:text-xs text-charcoal/50">{formatDistance(round.distanceMeters)} away</span>
												</div>
											</div>
										</div>
									</div>
								{:else}
									<!-- Normal Round -->
									<div class="round-card round-card--normal">
										<div class="flex items-start gap-3">
											<div class="w-8 h-8 rounded-lg bg-terrain flex items-center justify-center flex-shrink-0">
												<span class="font-mono font-bold text-sm text-charcoal/60">{i + 1}</span>
											</div>
											<div class="flex-1 min-w-0">
												<div class="flex items-center justify-between mb-1">
													<p class="font-semibold text-charcoal text-sm truncate">
														{round.location_name ?? `Round ${i + 1}`}
													</p>
													<div class="flex items-baseline gap-1.5 flex-shrink-0 ml-2">
														<span class="font-mono font-bold text-sm text-charcoal">{(round.score ?? 0).toLocaleString()}</span>
														<span class="text-[10px] text-charcoal/40 font-mono">pts</span>
													</div>
												</div>
												<div class="h-1.5 bg-gray-100 rounded-full mb-1.5">
													<div class="score-bar h-1.5 bg-jungle/60 rounded-full" style="width: {((round.score ?? 0) / 5000) * 100}%;"></div>
												</div>
												<div class="flex items-center justify-between">
													<p class="text-[10px] sm:text-xs text-charcoal/40">{round.location_name ?? ""}</p>
													<span class="font-mono text-[10px] sm:text-xs text-charcoal/50">{formatDistance(round.distanceMeters)} away</span>
												</div>
											</div>
										</div>
									</div>
								{/if}
							{/each}
						</div>
					</div>

					<!-- CTA Buttons -->
					<div class="px-5 sm:px-8 pb-6 sm:pb-8">
						<button
							class="btn-3d w-full flex flex-col items-center justify-center transition-colors mb-3"
							disabled={starting}
							on:click={playAgain}
						>
							<div class="flex items-center gap-2">
								<span class="material-symbols-outlined text-xl" style="font-variation-settings: 'FILL' 1;">replay</span>
								<span class="text-base sm:text-lg">{starting ? "Starting..." : "Play Again"}</span>
							</div>
							<span class="text-white/60 text-[10px] sm:text-xs font-normal mt-0.5">{modeLabel(game)}</span>
						</button>

						<div class="flex gap-3">
							<a
								href="/"
								class="flex-1 px-4 py-2.5 sm:py-3 rounded-xl border-2 border-charcoal/15 text-charcoal font-heading font-bold text-sm sm:text-base hover:bg-charcoal/5 transition-colors flex items-center justify-center gap-1.5"
							>
								<span class="material-symbols-outlined text-lg">home</span>
								<span>Home</span>
							</a>
							<a
								href="/leaderboard"
								class="flex-1 px-4 py-2.5 sm:py-3 rounded-xl border-2 border-charcoal/15 text-charcoal font-heading font-bold text-sm sm:text-base hover:bg-charcoal/5 transition-colors flex items-center justify-center gap-1.5"
							>
								<span class="material-symbols-outlined text-lg">leaderboard</span>
								<span>Ranks</span>
							</a>
							<button
								class="px-4 py-2.5 sm:py-3 rounded-xl border-2 border-gold/40 text-gold hover:bg-gold/5 font-heading font-bold text-sm sm:text-base transition-colors flex items-center justify-center gap-1.5"
								on:click={() => toast.success("Share feature coming soon!")}
							>
								<span class="material-symbols-outlined text-lg">share</span>
								<span>Share</span>
							</button>
						</div>
					</div>
				</div>
			</main>
		</div>
	</div>
{/if}

<style>
	/* Loading / Error screens */
	.loading-screen {
		position: fixed;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #f5f2e9;
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 4px solid rgba(24, 24, 27, 0.1);
		border-top-color: #2e933c;
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
		background: #f5f2e9;
	}

	.error-text {
		font-size: 16px;
		font-weight: 500;
		color: rgba(24, 24, 27, 0.6);
	}

	/* Map Strip */
	.map-strip {
		position: relative;
		height: 200px;
		border-radius: 24px;
		overflow: hidden;
		box-shadow: 6px 6px 0px 0px rgba(0, 0, 0, 0.15);
		border: 1px solid rgba(255, 255, 255, 0.5);
	}

	.map-bg {
		position: absolute;
		inset: 0;
		background: #E8E4D9;
		filter: sepia(0.25) contrast(1.05) saturate(0.85);
	}

	.map-bg::after {
		content: "";
		position: absolute;
		inset: 0;
		background: linear-gradient(135deg, rgba(245, 242, 233, 0.3) 0%, rgba(232, 228, 217, 0.5) 100%);
	}

	.map-grid {
		position: absolute;
		inset: 0;
		background-image:
			repeating-linear-gradient(0deg, transparent, transparent 40px, rgba(0, 0, 0, 0.03) 40px, rgba(0, 0, 0, 0.03) 41px),
			repeating-linear-gradient(90deg, transparent, transparent 40px, rgba(0, 0, 0, 0.03) 40px, rgba(0, 0, 0, 0.03) 41px);
	}

	.round-label {
		position: absolute;
		z-index: 30;
		background: white;
		border-radius: 9999px;
		width: 20px;
		height: 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		font-size: 10px;
		font-family: "JetBrains Mono", monospace;
		font-weight: 700;
		color: #18181b;
	}

	.round-label--best {
		color: #2e933c;
		box-shadow: 0 0 0 1px rgba(46, 147, 60, 0.3), 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.map-legend {
		position: absolute;
		bottom: 12px;
		left: 12px;
		z-index: 30;
		display: flex;
		align-items: center;
		gap: 12px;
		background: rgba(255, 255, 255, 0.9);
		backdrop-filter: blur(4px);
		border-radius: 8px;
		padding: 6px 12px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
	}

	.dashed-line {
		stroke-dasharray: 2, 2;
		animation: dash 0.6s linear forwards;
	}

	@keyframes dash {
		from { stroke-dashoffset: 20; }
		to { stroke-dashoffset: 0; }
	}

	/* Score animation */
	.score-pop {
		animation: scorePop 0.5s ease-out forwards;
	}

	@keyframes scorePop {
		0% { transform: scale(0.5); opacity: 0; }
		70% { transform: scale(1.1); }
		100% { transform: scale(1); opacity: 1; }
	}

	/* Stats labels */
	.stat-label {
		font-size: 10px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: rgba(24, 24, 27, 0.5);
		margin-bottom: 4px;
	}

	/* Round cards */
	.round-card {
		border-radius: 12px;
		overflow: hidden;
		padding: 12px 16px;
		transition: all 0.15s;
		box-shadow: 4px 4px 0px 0px rgba(0, 0, 0, 0.1);
	}

	.round-card:hover {
		background: rgba(245, 242, 233, 0.5);
	}

	.round-card--normal {
		background: white;
		border: 1px solid rgba(0, 0, 0, 0.06);
	}

	.round-card--best {
		background: rgba(46, 147, 60, 0.04);
		border: 1px solid rgba(46, 147, 60, 0.2);
	}

	.round-card--worst {
		background: rgba(217, 93, 57, 0.03);
		border: 1px solid rgba(217, 93, 57, 0.15);
	}

	.round-card--skipped {
		background: rgb(249, 250, 251);
		border: 1px dashed rgba(0, 0, 0, 0.12);
		opacity: 0.6;
	}

	/* Round badges */
	.badge {
		font-size: 8px;
		font-weight: 700;
		text-transform: uppercase;
		padding: 2px 6px;
		border-radius: 9999px;
		flex-shrink: 0;
	}

	.badge--best {
		color: #2e933c;
		background: rgba(46, 147, 60, 0.1);
	}

	.badge--worst {
		color: #D95D39;
		background: rgba(217, 93, 57, 0.1);
	}

	.badge--skipped {
		color: rgba(24, 24, 27, 0.4);
		background: rgba(24, 24, 27, 0.05);
	}

	/* Score bars */
	.score-bar {
		transition: width 0.6s ease-out;
	}

	@media (min-width: 640px) {
		.round-card {
			padding: 12px 16px;
		}

		.badge {
			font-size: 10px;
		}
	}
</style>
