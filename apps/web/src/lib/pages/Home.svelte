<script lang="ts">
import { gamesService } from "$lib/domains/games/api/games.service";
import { gameQueries } from "$lib/domains/games/queries/games.queries";
import {
	DEFAULT_DIFFICULTY,
	type Difficulty,
	type Environment,
	type GameMode,
} from "$lib/domains/games/types";
import { multiplayerService } from "$lib/domains/multiplayer/api/multiplayer.service";
import { multiplayerQueries } from "$lib/domains/multiplayer/queries/multiplayer.queries";
import type { Environment as MpEnvironment, MultiplayerGame } from "$lib/domains/multiplayer/types";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import TogglePills from "$lib/shared/components/TogglePills.svelte";
import type { ToggleOption } from "$lib/shared/components/TogglePills.svelte";
import Button from "$lib/shared/ui/Button.svelte";
import Card from "$lib/shared/ui/Card.svelte";
import PageShell from "$lib/shared/ui/PageShell.svelte";
import StateBlock from "$lib/shared/ui/StateBlock.svelte";
import { createQuery } from "@tanstack/svelte-query";
import { ArrowRight, CalendarRange } from "lucide-svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

const multiplayerEnabled = import.meta.env.VITE_FEATURE_MULTIPLAYER === "true";
const recentGamesParams = { status: "completed", limit: 5 };

const timingOptions = [
	{ value: "untimed", label: "Untimed" },
	{ value: "timed", label: "Timed" },
] satisfies ToggleOption[];

const locationOptions = [
	{ value: "any", label: "All" },
	{ value: "indoor", label: "Indoor" },
	{ value: "outdoor", label: "Outdoor" },
] satisfies ToggleOption[];

const difficultyOptions = [
	{ value: "easy", label: "Easy" },
	{ value: "medium", label: "Medium" },
	{ value: "hard", label: "Hard" },
] satisfies ToggleOption[];

let timed = false;
let environment: Environment = "any";
let difficulty: Difficulty = DEFAULT_DIFFICULTY;
let starting = false;

let mpEnvironment: MpEnvironment = "any";
let creatingGame = false;
let joinCode = "";
let joiningGame = false;

$: isAuthenticated = $auth.currentUserOid !== null;

$: activeGame = createQuery({
	...gameQueries.active($auth.currentUserOid),
	enabled: isAuthenticated,
});

$: activeMultiplayerGame = createQuery({
	...multiplayerQueries.active($auth.currentUserOid),
	enabled: isAuthenticated && multiplayerEnabled,
});

$: recentGames = createQuery({
	...gameQueries.list(recentGamesParams, $auth.currentUserOid),
	enabled: isAuthenticated,
});

$: activeRoundNumber = $activeGame.data
	? $activeGame.data.rounds.filter((round) => round.guess || round.skipped).length + 1
	: 0;

$: activeMultiplayerRoundNumber = $activeMultiplayerGame.data
	? Math.max($activeMultiplayerGame.data.currentRound, 1)
	: 0;

function formatDifficultyLabel(value: Difficulty): string {
	return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatModeSummary(mode: GameMode): string {
	const parts = [mode.daily ? "Daily" : "Random", mode.timed ? "Timed" : "Untimed"];
	if (mode.environment === "indoor") parts.push("Indoor");
	else if (mode.environment === "outdoor") parts.push("Outdoor");
	return parts.join(" \u00b7 ");
}

function formatGameDate(iso: string) {
	return new Date(iso).toLocaleDateString(undefined, {
		month: "short",
		day: "numeric",
	});
}

function getSoloModeLabel(daily: boolean, timedMode: boolean) {
	if (daily) return "Daily Challenge";
	return timedMode ? "Timed Random Drop" : "Random Drop";
}

function getEnvironmentLabel(value: "any" | "indoor" | "outdoor") {
	if (value === "indoor") return "Indoor";
	if (value === "outdoor") return "Outdoor";
	return "All campus";
}

function getMultiplayerCta(game: MultiplayerGame) {
	if (game.status === "waiting") {
		return { label: "Open Lobby", path: `/multiplayer/${game.id}/lobby` };
	}
	return { label: "Resume Match", path: `/multiplayer/${game.id}` };
}

async function createMultiplayerGame() {
	creatingGame = true;
	try {
		const game = await multiplayerService.create({ environment: mpEnvironment });
		navigate(`/multiplayer/${game.id}/lobby`);
	} catch (err: unknown) {
		const e = err as { response?: { data?: { detail?: string } }; message?: string };
		const detail = e?.response?.data?.detail || e?.message || "Failed to create game";
		toast.error(detail);
	} finally {
		creatingGame = false;
	}
}

async function joinMultiplayerGame() {
	if (!joinCode.trim() || joiningGame) return;
	joiningGame = true;
	try {
		const game = await multiplayerService.join({ code: joinCode.trim().toUpperCase() });
		navigate(`/multiplayer/${game.id}/lobby`);
	} catch (err: unknown) {
		const e = err as { response?: { data?: { detail?: string } }; message?: string };
		toast.error(e?.response?.data?.detail || e?.message || "Failed to join game");
	} finally {
		joiningGame = false;
	}
}

async function startGame(daily: boolean) {
	starting = true;
	const mode: GameMode = {
		daily,
		timed: daily ? false : timed,
		environment: daily ? "any" : environment,
		difficulty,
	};
	try {
		const game = await gamesService.start({ mode });
		navigate(`/game/${game.id}`);
	} catch (err: unknown) {
		const e = err as { response?: { data?: { detail?: string } }; message?: string };
		toast.error(e?.response?.data?.detail || e?.message || "Failed to start game");
	} finally {
		starting = false;
	}
}
</script>

<div class="min-h-screen bg-canvas font-sans text-ink">
	<Navbar activePage="home" />

	<PageShell size="content">
		<!-- Resume active games -->
		{#if $activeGame.data || (multiplayerEnabled && $activeMultiplayerGame.data)}
			<section class="resume-section">
				{#if $activeGame.data}
					<button class="resume-card" type="button" on:click={() => navigate(`/game/${$activeGame.data?.id}`)}>
						<div class="resume-badge">Solo</div>
						<div class="resume-info">
							<p class="resume-title">{getSoloModeLabel($activeGame.data.mode.daily, $activeGame.data.mode.timed)}</p>
							<p class="resume-meta">
								Round {activeRoundNumber}/{$activeGame.data.rounds.length} · {$activeGame.data.totalScore.toLocaleString()} pts
							</p>
						</div>
						<span class="resume-action">Resume <ArrowRight size={16} /></span>
					</button>
				{/if}
				{#if multiplayerEnabled && $activeMultiplayerGame.data}
					{@const mp = $activeMultiplayerGame.data}
					{@const cta = getMultiplayerCta(mp)}
					<button class="resume-card resume-card--mp" type="button" on:click={() => navigate(cta.path)}>
						<div class="resume-badge resume-badge--mp">MP</div>
						<div class="resume-info">
							<p class="resume-title">{mp.status === "waiting" ? "Lobby open" : "Match in progress"}</p>
							<p class="resume-meta">
								{mp.players.length} players · {mp.status === "waiting" ? `Code ${mp.inviteCode}` : `Round ${activeMultiplayerRoundNumber}/${mp.rounds.length}`}
							</p>
						</div>
						<span class="resume-action">{cta.label} <ArrowRight size={16} /></span>
					</button>
				{/if}
			</section>
		{/if}

		<!-- Solo Play -->
		<section class="play-section">
			<h2 class="section-title">Play</h2>

			<Card class="play-card">
				<button class="daily-row" type="button" disabled={starting} on:click={() => startGame(true)}>
					<CalendarRange size={16} />
					<span class="daily-row-label">Daily Challenge</span>
					<ArrowRight size={14} class="daily-row-arrow" />
				</button>

				<div class="config-divider" />

				<div class="config-body">
					<div class="config-controls">
						<div class="control">
							<span class="control-lbl">Timing</span>
							<TogglePills
								ariaLabel="Game timing"
								selected={timed ? "timed" : "untimed"}
								options={timingOptions}
								on:change={(e) => { timed = e.detail === "timed"; }}
							/>
						</div>
						<div class="control">
							<span class="control-lbl">Environment</span>
							<TogglePills
								ariaLabel="Game environment"
								selected={environment}
								options={locationOptions}
								on:change={(e) => {
									if (e.detail === "any" || e.detail === "indoor" || e.detail === "outdoor") {
										environment = e.detail;
									}
								}}
							/>
						</div>
						<div class="control">
							<span class="control-lbl">Difficulty</span>
							<TogglePills
								ariaLabel="Game difficulty"
								selected={difficulty}
								options={difficultyOptions}
								on:change={(e) => {
									if (e.detail === "easy" || e.detail === "medium" || e.detail === "hard") {
										difficulty = e.detail;
									}
								}}
							/>
						</div>
					</div>

					<div class="config-footer">
						<span class="config-summary">
							{timed ? "Timed" : "Untimed"} · {getEnvironmentLabel(environment)} · {formatDifficultyLabel(difficulty)}
						</span>
						<Button size="lg" class="w-full sm:w-auto" disabled={starting} type="button" on:click={() => startGame(false)}>
							{starting ? "Starting..." : "Start Guessing"}
						</Button>
					</div>
				</div>
			</Card>
		</section>

		<!-- Multiplayer -->
		{#if multiplayerEnabled}
			<section class="mp-section">
				<h2 class="section-title">Multiplayer</h2>
				<div class="mp-grid">
					<Card>
						<div class="mp-card">
							<p class="mp-card-title">Create match</p>
							<p class="mp-card-desc">Pick your settings and share the code.</p>
							<div class="control">
								<span class="control-lbl">Environment</span>
								<TogglePills
									ariaLabel="Multiplayer environment"
									selected={mpEnvironment}
									options={locationOptions}
									on:change={(e) => {
										if (e.detail === "any" || e.detail === "indoor" || e.detail === "outdoor") {
											mpEnvironment = e.detail;
										}
									}}
								/>
							</div>
							<Button class="w-full" disabled={creatingGame} type="button" on:click={createMultiplayerGame}>
								{creatingGame ? "Creating..." : "Create"}
							</Button>
						</div>
					</Card>

					<Card>
						<div class="mp-card">
							<p class="mp-card-title">Join match</p>
							<p class="mp-card-desc">Enter a friend's invite code.</p>
							<div class="join-field">
								<input
									type="text"
									class="join-input"
									placeholder="Enter code"
									maxlength={6}
									bind:value={joinCode}
									on:keydown={(e) => { if (e.key === "Enter") joinMultiplayerGame(); }}
								/>
							</div>
							<Button variant="outline" class="w-full" disabled={joiningGame || !joinCode.trim()} type="button" on:click={joinMultiplayerGame}>
								{joiningGame ? "Joining..." : "Join"}
							</Button>
						</div>
					</Card>
				</div>
			</section>
		{/if}

		<!-- Campus Tour -->
		<section class="tour-section">
			<Card>
				<div class="tour-card">
					<div class="tour-text">
						<h2 class="section-title">Campus Tour</h2>
						<p class="tour-desc">Browse approved panoramas from across Vanderbilt's campus.</p>
					</div>
					<Button variant="outline" on:click={() => navigate("/tour")}>
						Explore
						<ArrowRight size={16} />
					</Button>
				</div>
			</Card>
		</section>

		<!-- Recent Games -->
		<section class="recent-section">
			<div class="recent-header">
				<h2 class="section-title">Recent games</h2>
				<a href="/history" class="recent-link" on:click|preventDefault={() => navigate("/history")}>View all</a>
			</div>

			{#if $recentGames.isLoading}
				<StateBlock title="Loading recent games" copy="Pulling your latest runs." />
			{:else if $recentGames.isError}
				<StateBlock tone="error" title="Couldn't load recent games" copy="Something went wrong fetching your history.">
					<Button type="button" on:click={() => $recentGames.refetch()}>Try again</Button>
				</StateBlock>
			{:else if $recentGames.data && $recentGames.data.length > 0}
				<div class="recent-list">
					{#each $recentGames.data as game}
						<button class="recent-row" type="button" on:click={() => navigate(`/game/${game.id}/summary`)}>
							<div class="recent-main">
								<span class="recent-mode">{formatModeSummary(game.mode)}</span>
								<span class="recent-badge">{formatDifficultyLabel(game.mode.difficulty ?? "medium")}</span>
								<span class="recent-date">{formatGameDate(game.createdAt)}</span>
							</div>
							<span class="recent-score">{game.totalScore.toLocaleString()}</span>
						</button>
					{/each}
				</div>
			{:else}
				<StateBlock tone="soft" title="No games yet" copy="Complete your first run and it'll show up here.">
					<Button type="button" on:click={() => startGame(false)}>Start playing</Button>
				</StateBlock>
			{/if}
		</section>
	</PageShell>
</div>

<style>
	/* Resume */
	.resume-section {
		display: grid;
		gap: 8px;
		margin-bottom: 24px;
	}

	.resume-card {
		display: grid;
		grid-template-columns: auto 1fr auto;
		align-items: center;
		gap: 12px;
		padding: 12px 16px;
		border: 1px solid color-mix(in srgb, var(--brand) 25%, var(--line));
		border-radius: var(--radius-md);
		background: color-mix(in srgb, var(--brand) 3%, var(--surface));
		text-align: left;
		cursor: pointer;
		transition: border-color var(--duration-fast) var(--ease),
			background var(--duration-fast) var(--ease),
			transform var(--duration-fast) var(--ease);
	}

	.resume-card:hover {
		border-color: color-mix(in srgb, var(--brand) 40%, var(--line));
		background: color-mix(in srgb, var(--brand) 5%, var(--surface));
	}

	.resume-card:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.resume-card:active {
		transform: scale(0.985);
	}

	.resume-card--mp {
		border-color: color-mix(in srgb, var(--mp) 20%, var(--line));
		background: color-mix(in srgb, var(--mp) 3%, var(--surface));
	}

	.resume-card--mp:hover {
		border-color: color-mix(in srgb, var(--mp) 35%, var(--line));
		background: color-mix(in srgb, var(--mp) 5%, var(--surface));
	}

	.resume-badge {
		font-size: 11px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--brand-dark);
		background: var(--brand-light);
		padding: 3px 7px;
		border-radius: var(--radius-sm);
	}

	.resume-badge--mp {
		color: var(--mp);
		background: rgba(59, 130, 246, 0.1);
	}

	.resume-info {
		min-width: 0;
	}

	.resume-title,
	.resume-meta {
		margin: 0;
	}

	.resume-title {
		font-size: 14px;
		font-weight: 600;
	}

	.resume-meta {
		font-size: 13px;
		color: var(--muted);
		margin-top: 1px;
	}

	.resume-action {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-size: 13px;
		font-weight: 600;
		color: var(--brand);
		white-space: nowrap;
	}

	/* Shared */
	.section-title {
		margin: 0;
		font-size: 16px;
		font-weight: 700;
		letter-spacing: -0.01em;
	}

	/* Solo Play */
	.play-section {
		display: grid;
		gap: 10px;
		margin-bottom: 24px;
	}

	:global(.play-card) {
		padding: 0 !important;
		overflow: hidden;
	}

	.daily-row {
		display: flex;
		align-items: center;
		gap: 10px;
		width: 100%;
		padding: 14px 16px;
		border: none;
		background: transparent;
		color: var(--ink);
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		text-align: left;
		transition: background var(--duration-fast) var(--ease);
	}

	.daily-row:hover {
		background: var(--surface-subtle);
	}

	.daily-row:focus-visible {
		outline: none;
		box-shadow: inset var(--ring);
	}

	.daily-row:active:not(:disabled) {
		background: var(--surface-strong);
	}

	.daily-row:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	:global(.daily-row-arrow) {
		margin-left: auto;
		color: var(--muted);
		flex-shrink: 0;
	}

	.config-divider {
		height: 1px;
		background: var(--line);
	}

	.config-body {
		display: grid;
		gap: 14px;
		padding: 16px;
	}

	.config-controls {
		display: grid;
		gap: 12px;
	}

	.control {
		display: grid;
		gap: 5px;
	}

	.control-lbl {
		font-size: 12px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--muted);
	}

	.config-footer {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
		padding-top: 10px;
		border-top: 1px solid var(--line);
	}

	.config-summary {
		font-size: 13px;
		font-weight: 500;
		color: var(--muted);
	}

	/* Multiplayer */
	.mp-section {
		display: grid;
		gap: 10px;
		margin-bottom: 24px;
	}

	.mp-grid {
		display: grid;
		gap: 10px;
		grid-template-columns: 1fr;
	}

	.mp-card {
		display: grid;
		gap: 12px;
	}

	.mp-card-title {
		margin: 0;
		font-size: 15px;
		font-weight: 700;
	}

	.mp-card-desc {
		margin: -4px 0 0;
		font-size: 13px;
		color: var(--muted);
		line-height: 1.4;
	}

	.join-field {
		display: grid;
	}

	.join-input {
		height: 42px;
		padding: 0 14px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
		color: var(--ink);
		font-size: 15px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.join-input::placeholder {
		text-transform: none;
		letter-spacing: normal;
		font-weight: 400;
	}

	.join-input:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	/* Recent */
	.tour-section {
		margin-bottom: 24px;
	}

	.tour-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
	}

	.tour-text {
		display: grid;
		gap: 2px;
	}

	.tour-desc {
		margin: 0;
		font-size: 13px;
		color: var(--muted);
		line-height: 1.4;
	}

	.recent-section {
		margin-bottom: 24px;
	}

	.recent-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 10px;
	}

	.recent-link {
		font-size: 13px;
		font-weight: 600;
		color: var(--brand);
		text-decoration: none;
	}

	.recent-link:hover {
		text-decoration: underline;
	}

	.recent-list {
		display: grid;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		overflow: hidden;
	}

	.recent-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 10px 16px;
		background: var(--surface);
		text-align: left;
		cursor: pointer;
		border: none;
		border-bottom: 1px solid var(--line);
		transition: background var(--duration-fast) var(--ease);
	}

	.recent-row:last-child {
		border-bottom: none;
	}

	.recent-row:hover {
		background: var(--surface-subtle);
	}

	.recent-row:focus-visible {
		outline: none;
		box-shadow: inset var(--ring);
	}

	.recent-row:active {
		background: var(--surface-strong);
	}

	.recent-main {
		display: flex;
		align-items: center;
		gap: 8px;
		min-width: 0;
		flex-wrap: wrap;
	}

	.recent-mode {
		font-size: 14px;
		font-weight: 500;
	}

	.recent-badge {
		font-size: 11px;
		font-weight: 600;
		padding: 2px 6px;
		border-radius: var(--radius-sm);
		background: var(--surface-strong);
		color: var(--muted);
		text-transform: capitalize;
	}

	.recent-date {
		font-size: 13px;
		color: var(--muted);
		flex-shrink: 0;
	}

	.recent-score {
		font-family: "IBM Plex Mono", monospace;
		font-size: 14px;
		font-weight: 600;
		color: var(--ink);
		flex-shrink: 0;
	}

	@media (min-width: 640px) {
		.mp-grid {
			grid-template-columns: 1fr 1fr;
		}

		.config-body {
			padding: 20px;
		}

		.daily-row {
			padding: 14px 20px;
		}
	}
</style>
