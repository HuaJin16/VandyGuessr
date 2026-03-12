<script lang="ts">
import { gamesService } from "$lib/domains/games/api/games.service";
import { gameQueries } from "$lib/domains/games/queries/games.queries";
import type { Environment, GameMode } from "$lib/domains/games/types";
import { leaderboardQueries } from "$lib/domains/leaderboard/queries/leaderboard.queries";
import { multiplayerService } from "$lib/domains/multiplayer/api/multiplayer.service";
import type { Environment as MpEnvironment } from "$lib/domains/multiplayer/types";
import { userQueries } from "$lib/domains/users/queries/users.queries";
import { auth } from "$lib/shared/auth/auth.store";
import Avatar from "$lib/shared/components/Avatar.svelte";
import Navbar from "$lib/shared/components/Navbar.svelte";
import TogglePills from "$lib/shared/components/TogglePills.svelte";
import type { ToggleOption } from "$lib/shared/components/TogglePills.svelte";
import { createQuery } from "@tanstack/svelte-query";
import { ChevronRight } from "lucide-svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

const multiplayerEnabled = import.meta.env.VITE_FEATURE_MULTIPLAYER === "true";

$: user = createQuery({ ...userQueries.me(), enabled: $auth.isInitialized });
$: activeGame = createQuery({ ...gameQueries.active(), enabled: $auth.isInitialized });
$: lbQuery = createQuery({
	...leaderboardQueries.leaderboard({ timeframe: "alltime", mode: "all", limit: 1, offset: 0 }),
	enabled: $auth.isInitialized,
});
$: lbEntry = $lbQuery.data?.userEntry ?? null;

$: activeRoundNumber = $activeGame.data
	? $activeGame.data.rounds.filter((r) => r.guess || r.skipped).length + 1
	: 0;

const timingOptions = [
	{ value: "untimed", label: "Untimed" },
	{ value: "timed", label: "Timed" },
] satisfies ToggleOption[];

const locationOptions = [
	{ value: "any", label: "All" },
	{ value: "indoor", label: "Indoor" },
	{ value: "outdoor", label: "Outdoor" },
] satisfies ToggleOption[];

let timed = false;
let environment: Environment = "any";

let starting = false;

let mpEnvironment: MpEnvironment = "any";
let creatingGame = false;
let joinCode = "";
let joiningGame = false;

async function createMultiplayerGame() {
	creatingGame = true;
	try {
		const game = await multiplayerService.create({ environment: mpEnvironment });
		navigate(`/multiplayer/${game.id}/lobby`);
	} catch (err: unknown) {
		const e = err as { response?: { data?: { detail?: string } }; message?: string };
		toast.error(e?.response?.data?.detail || e?.message || "Failed to create game");
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

	<main class="main">
		<!-- Profile Card -->
		<section class="card">
			<div class="flex items-center gap-3">
				<Avatar name={$user.data?.name ?? ""} size="md" />
				<div class="min-w-0">
					<p class="text-[17px] font-bold leading-tight">{$user.data?.name ?? "Loading..."}</p>
					<p class="mt-0.5 text-[13px] text-muted">{$user.data?.email?.toLowerCase() ?? ""}</p>
				</div>
			</div>
			<p class="stats-scope">All-Time Stats</p>
			<div class="stats-grid">
				<article class="stat">
					<p class="stat-label">Rank</p>
					<p class="stat-value">{lbEntry?.rank ? `#${lbEntry.rank}` : "\u2014"}</p>
				</article>
				<article class="stat">
					<p class="stat-label">Avg Score</p>
					<p class="stat-value">{lbEntry ? Math.round(lbEntry.avgScore).toLocaleString() : "\u2014"}</p>
				</article>
				<article class="stat">
					<p class="stat-label">Games</p>
					<p class="stat-value">{lbEntry?.gamesPlayed ?? 0}</p>
				</article>
				<article class="stat">
					<p class="stat-label">Rounds</p>
					<p class="stat-value">{lbEntry?.roundsPlayed ?? 0}</p>
				</article>
			</div>
		</section>

		<!-- Resume Card -->
		{#if $activeGame.data}
			<section class="card resume-card">
				<p class="section-label">Continue</p>
				<h2>Current Session</h2>
				<p class="desc">
					Round {activeRoundNumber} of {$activeGame.data.rounds.length}. Current total is
					<span class="font-mono font-semibold text-ink">{$activeGame.data.totalScore.toLocaleString()}</span> points.
				</p>
				<button
					class="btn-3d mt-3 w-full"
					type="button"
					on:click={() => navigate(`/game/${$activeGame.data?.id}`)}
				>
					Resume Game
				</button>
			</section>
		{/if}

		<!-- Game Modes Card -->
		<section class="card">
			<p class="section-label">Play</p>
			<h2>Choose your mode</h2>
			<p class="desc">Pick your pace and environment, then jump in.</p>

			<div class="toggle-bar">
				<TogglePills
					ariaLabel="Game timing"
					selected={timed ? "timed" : "untimed"}
					options={timingOptions}
					on:change={(event) => {
						timed = event.detail === "timed";
					}}
				/>
				<TogglePills
					ariaLabel="Game location"
					selected={environment}
					options={locationOptions}
					on:change={(event) => {
						if (
							event.detail === "any" ||
							event.detail === "indoor" ||
							event.detail === "outdoor"
						) {
							environment = event.detail;
						}
					}}
				/>
			</div>

			<div class="mode-list">
				<!-- svelte-ignore a11y-click-events-have-key-events -->
				<div
					class="mode-row hero"
					tabindex="0"
					role="button"
					on:click={() => startGame(true)}
				>
					<div class="mode-icon hero-icon">🏆</div>
					<div class="min-w-0 flex-1">
						<p class="text-[15px] font-bold">Daily Challenge</p>
						<p class="mt-0.5 text-[13px] text-muted">Shared 5-drop route.</p>
					</div>
					<span class="mode-arrow"><ChevronRight size={18} /></span>
				</div>
				<!-- svelte-ignore a11y-click-events-have-key-events -->
				<div
					class="mode-row"
					tabindex="0"
					role="button"
					on:click={() => startGame(false)}
				>
					<div class="mode-icon">🌍</div>
					<div class="min-w-0 flex-1">
						<p class="text-[15px] font-bold">Random Drop</p>
						<p class="mt-0.5 text-[13px] text-muted">Five random campus locations.</p>
					</div>
					<span class="mode-arrow"><ChevronRight size={18} /></span>
				</div>
			</div>

			<button
				class="btn-3d mt-3 w-full"
				disabled={starting}
				type="button"
				on:click={() => startGame(false)}
			>
				{starting ? "Starting..." : "Start New Round"}
			</button>
		</section>

		<!-- Multiplayer Card -->
		{#if multiplayerEnabled}
			<section class="card">
				<p class="section-label">Multiplayer</p>

				<button
					class="btn-3d mt-3 w-full"
					disabled={creatingGame}
					type="button"
					on:click={createMultiplayerGame}
				>
					{creatingGame ? "Creating..." : "Create Game"}
				</button>

				<div class="mp-divider"><span>or</span></div>

				<div class="join-row">
					<input
						type="text"
						class="code-input"
						placeholder="Invite code"
						maxlength={6}
						bind:value={joinCode}
						on:keydown={(e) => {
							if (e.key === "Enter") joinMultiplayerGame();
						}}
					/>
					<button
						class="join-btn"
						disabled={joiningGame || !joinCode.trim()}
						type="button"
						on:click={joinMultiplayerGame}
					>
						{joiningGame ? "..." : "Join"}
					</button>
				</div>
			</section>
		{/if}
	</main>
</div>

<style>
	.main {
		width: min(600px, calc(100% - 32px));
		margin: 16px auto 24px;
		display: grid;
		gap: 14px;
	}

	.section-label {
		margin: 0;
		color: var(--muted);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.stats-scope {
		margin: 12px 0 0;
		color: var(--muted);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.stats-grid {
		margin-top: 6px;
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 8px;
	}

	@media (min-width: 640px) {
		.stats-grid {
			grid-template-columns: repeat(4, 1fr);
		}
	}

	h2 {
		margin: 8px 0 0;
		font-size: 24px;
		font-weight: 800;
		line-height: 1.15;
	}

	.desc {
		margin: 8px 0 0;
		color: var(--muted);
		font-size: 15px;
		line-height: 1.45;
	}

	.resume-card {
		border-color: var(--brand);
		border-width: 2px;
	}

	/* Toggle bar */
	.toggle-bar {
		display: flex;
		gap: 10px;
		margin-top: 14px;
	}

	@media (max-width: 400px) {
		.toggle-bar {
			flex-wrap: wrap;
		}
	}

	/* Mode rows */
	.mode-list {
		display: grid;
		gap: 10px;
		margin-top: 14px;
	}

	.mode-row {
		display: flex;
		gap: 12px;
		align-items: center;
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		background: var(--surface);
		padding: 13px 14px;
		transition: all 140ms var(--ease);
		cursor: pointer;
	}

	.mode-row:hover {
		transform: translateX(4px);
		border-color: var(--brand);
		background: var(--brand-light);
	}

	.mode-row:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.mode-row.hero {
		border: 2px solid var(--gold);
		background: linear-gradient(105deg, var(--gold-light), transparent 60%);
	}

	.mode-row.hero:hover {
		border-color: var(--gold-dark);
		background: linear-gradient(105deg, rgba(232, 168, 23, 0.2), transparent 60%);
		transform: translateX(4px);
	}

	.mode-icon {
		width: 38px;
		height: 38px;
		border-radius: var(--radius-md);
		background: var(--brand-light);
		display: grid;
		place-items: center;
		font-size: 17px;
		flex-shrink: 0;
	}

	.hero-icon {
		background: var(--gold-light);
	}

	.mode-arrow {
		color: var(--muted);
		transition: all 140ms var(--ease);
		display: flex;
	}

	.mode-row:hover .mode-arrow {
		color: var(--brand);
		transform: translateX(4px);
	}

	.mode-row.hero:hover .mode-arrow {
		color: var(--gold-dark);
	}

	/* Multiplayer divider */
	.mp-divider {
		display: flex;
		align-items: center;
		gap: 12px;
		margin: 14px 0;
	}

	.mp-divider::before,
	.mp-divider::after {
		content: "";
		flex: 1;
		height: 1px;
		background: var(--line);
	}

	.mp-divider span {
		font-size: 12px;
		font-weight: 600;
		color: var(--muted);
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}

	/* Join row */
	.join-row {
		display: flex;
		gap: 8px;
	}

	.code-input {
		flex: 1;
		min-width: 0;
		padding: 10px 14px;
		border: 2px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
		font-family: "IBM Plex Mono", monospace;
		font-size: 16px;
		font-weight: 600;
		letter-spacing: 0.2em;
		text-transform: uppercase;
		color: var(--ink);
		transition: all 120ms var(--ease);
	}

	.code-input::placeholder {
		font-family: Inter, sans-serif;
		font-size: 14px;
		font-weight: 400;
		letter-spacing: normal;
		text-transform: none;
		color: var(--muted);
		opacity: 0.6;
	}

	.code-input:focus {
		outline: none;
		border-color: var(--brand);
		box-shadow: var(--ring);
	}

	.join-btn {
		border: none;
		border-radius: var(--radius-md);
		background: var(--brand);
		color: #fff;
		font-size: 14px;
		font-weight: 700;
		padding: 10px 18px;
		box-shadow: 0 3px 0 var(--brand-dark);
		cursor: pointer;
		transition: all 120ms var(--ease);
		flex-shrink: 0;
	}

	.join-btn:hover {
		background: #278234;
	}

	.join-btn:active {
		transform: translateY(3px);
		box-shadow: 0 0 0 var(--brand-dark);
	}

	.join-btn:focus-visible {
		outline: none;
		box-shadow: 0 3px 0 var(--brand-dark), var(--ring);
	}

	.join-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
		box-shadow: 0 3px 0 var(--brand-dark);
	}

	/* Responsive */
	@media (min-width: 700px) {
		:global(.card) {
			padding: 18px;
		}
	}

	@media (max-width: 400px) {
		h2 {
			font-size: 20px;
		}

		.mode-icon {
			width: 32px;
			height: 32px;
			font-size: 15px;
		}

		.code-input {
			font-size: 14px;
			padding: 8px 10px;
		}
	}
</style>
