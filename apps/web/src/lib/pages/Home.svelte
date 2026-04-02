<script lang="ts">
import { gamesService } from "$lib/domains/games/api/games.service";
import { gameQueries } from "$lib/domains/games/queries/games.queries";
import {
	DEFAULT_DIFFICULTY,
	type Difficulty,
	type Environment,
	type GameMode,
} from "$lib/domains/games/types";
import { leaderboardQueries } from "$lib/domains/leaderboard/queries/leaderboard.queries";
import { multiplayerService } from "$lib/domains/multiplayer/api/multiplayer.service";
import { multiplayerQueries } from "$lib/domains/multiplayer/queries/multiplayer.queries";
import type { Environment as MpEnvironment, MultiplayerGame } from "$lib/domains/multiplayer/types";
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
const recentGamesParams = { status: "completed", limit: 5 };

$: isAuthenticated = $auth.currentUserOid !== null;

$: user = createQuery({
	...userQueries.me($auth.currentUserOid),
	enabled: isAuthenticated,
});
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

$: leaderboard = createQuery({
	...leaderboardQueries.leaderboard(
		{ timeframe: "alltime", mode: "all", limit: 1, offset: 0 },
		$auth.currentUserOid,
	),
	enabled: isAuthenticated,
});

$: leaderboardStats = $leaderboard.data?.userEntry;

$: activeRoundNumber = $activeGame.data
	? $activeGame.data.rounds.filter((r) => r.guess || r.skipped).length + 1
	: 0;

$: activeMultiplayerRoundNumber = $activeMultiplayerGame.data
	? Math.max($activeMultiplayerGame.data.currentRound, 1)
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
		return {
			label: "Open Lobby",
			path: `/multiplayer/${game.id}/lobby`,
		};
	}

	return {
		label: "Resume Match",
		path: `/multiplayer/${game.id}`,
	};
}

function formatDifficultyLabel(value: Difficulty): string {
	return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatModeSummary(mode: GameMode): string {
	const parts = [mode.daily ? "Daily" : "Random Drop", mode.timed ? "Timed" : "Untimed"];

	if (mode.environment === "indoor") {
		parts.push("Indoor");
	} else if (mode.environment === "outdoor") {
		parts.push("Outdoor");
	}

	return parts.join(" · ");
}

async function createMultiplayerGame() {
	creatingGame = true;
	try {
		const game = await multiplayerService.create({ environment: mpEnvironment });
		navigate(`/multiplayer/${game.id}/lobby`);
	} catch (err: unknown) {
		const e = err as { response?: { data?: { detail?: string } }; message?: string };
		const detail = e?.response?.data?.detail || e?.message || "Failed to create game";

		if (detail === "You already have an active multiplayer game.") {
			try {
				const active = await multiplayerService.getActive();
				if (active) {
					const path =
						active.status === "waiting"
							? `/multiplayer/${active.id}/lobby`
							: `/multiplayer/${active.id}`;
					toast.message("Redirecting to your active multiplayer game");
					navigate(path);
					return;
				}
			} catch {
				// Fall through to the original error toast.
			}
		}

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

	<main class="main">
		<section class="left-column">
			<section class="card active-games-card">
				<p class="section-label">Continue</p>
				<h2>Active Games</h2>
				<p class="desc">Jump back into any game you still have in progress.</p>

				<div class="active-games-list">
					{#if $activeGame.data}
						<article class="active-game-item">
							<div class="active-game-copy">
								<div class="active-game-header">
									<p class="active-game-title">{getSoloModeLabel($activeGame.data.mode.daily, $activeGame.data.mode.timed)}</p>
									<span class="active-game-badge">Solo</span>
								</div>
								<p class="active-game-meta">
									Round {activeRoundNumber} of {$activeGame.data.rounds.length} - {$activeGame.data.totalScore.toLocaleString()} pts
								</p>
								<p class="active-game-subtle">
									{getEnvironmentLabel($activeGame.data.mode.environment)} - {$activeGame.data.mode.timed ? "Timer on" : "No timer"}
								</p>
							</div>
							<button
								class="btn-3d active-game-btn"
								type="button"
								on:click={() => navigate(`/game/${$activeGame.data?.id}`)}
							>
								Resume
							</button>
						</article>
					{/if}

					{#if multiplayerEnabled && $activeMultiplayerGame.data}
						{@const multiplayerCta = getMultiplayerCta($activeMultiplayerGame.data)}
						<article class="active-game-item multiplayer-item">
							<div class="active-game-copy">
								<div class="active-game-header">
									<p class="active-game-title">{$activeMultiplayerGame.data.status === "waiting" ? "Multiplayer Lobby" : "Multiplayer Match"}</p>
									<span class="active-game-badge active-game-badge--multiplayer">Multiplayer</span>
								</div>
								<p class="active-game-meta">
									{$activeMultiplayerGame.data.players.length} players - {$activeMultiplayerGame.data.status === "waiting" ? "Waiting to start" : `Round ${activeMultiplayerRoundNumber} of ${$activeMultiplayerGame.data.rounds.length}`}
								</p>
								<p class="active-game-subtle">
									{getEnvironmentLabel($activeMultiplayerGame.data.mode.environment)}
									{#if $activeMultiplayerGame.data.status === "waiting"}
										- Code {$activeMultiplayerGame.data.inviteCode}
									{/if}
								</p>
							</div>
							<button
								class="btn-3d active-game-btn"
								type="button"
								on:click={() => navigate(multiplayerCta.path)}
							>
								{multiplayerCta.label}
							</button>
						</article>
					{/if}

					{#if !$activeGame.data && (!multiplayerEnabled || !$activeMultiplayerGame.data)}
						<div class="active-games-empty">
							<p class="empty-title">No games in progress</p>
							<p class="empty-copy">Start a solo round in the center column or spin up a multiplayer match on the right.</p>
						</div>
					{/if}
				</div>
			</section>

			<section class="card contribute-card">
				<p class="section-label">Community</p>
				<h2>Share a campus photo</h2>
				<p class="desc">
					Upload a panorama with GPS embedded. Submissions are reviewed before they appear in games.
				</p>
				<button class="btn-3d contribute-btn" type="button" on:click={() => navigate("/upload")}>
					Upload a photo
				</button>
			</section>
		</section>

		<section class="center-column">
			<section class="card">
				<div class="flex items-center gap-3">
					<Avatar name={$user.data?.name ?? ""} size="md" />
					<div class="min-w-0">
						<p class="text-[17px] font-bold leading-tight">{$user.data?.name ?? "Loading..."}</p>
						<p class="mt-0.5 text-[13px] text-muted">{$user.data?.email?.toLowerCase() ?? ""}</p>
					</div>
				</div>
				<div class="mt-3 grid grid-cols-3 gap-2">
					<article class="stat">
						<p class="stat-label">Rank</p>
						<p class="stat-value">{leaderboardStats?.rank ? `#${leaderboardStats.rank}` : "-"}</p>
					</article>
					<article class="stat">
						<p class="stat-label">Avg score</p>
						<p class="stat-value">{leaderboardStats?.avgScore ? Math.round(leaderboardStats.avgScore).toLocaleString() : "-"}</p>
					</article>
					<article class="stat">
						<p class="stat-label">Games</p>
						<p class="stat-value">{leaderboardStats?.gamesPlayed ?? 0}</p>
					</article>
				</div>
			</section>

			<section class="card">
				<p class="section-label">Play</p>
				<h2>Choose your mode</h2>
				<p class="desc">Pick your pace, environment, and difficulty, then jump in.</p>

				<div class="toggle-bar">
					<div class="toggle-group">
						<p class="toggle-label">Timing</p>
						<TogglePills
							ariaLabel="Game timing"
							selected={timed ? "timed" : "untimed"}
							options={timingOptions}
							on:change={(event) => {
								timed = event.detail === "timed";
							}}
						/>
					</div>
					<div class="toggle-group">
						<p class="toggle-label">Location</p>
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
					<div class="toggle-group">
						<p class="toggle-label">Difficulty</p>
						<TogglePills
							ariaLabel="Game difficulty"
							selected={difficulty}
							options={difficultyOptions}
							on:change={(event) => {
								if (
									event.detail === "easy" ||
									event.detail === "medium" ||
									event.detail === "hard"
								) {
									difficulty = event.detail;
								}
							}}
						/>
					</div>
				</div>

				<div class="mode-list">
					<div
						class="mode-row hero"
						tabindex="0"
						role="button"
						on:click={() => startGame(true)}
						on:keydown={(event) => {
							if (event.key === "Enter" || event.key === " ") startGame(true);
						}}
					>
						<div class="mode-icon hero-icon">🏆</div>
						<div class="min-w-0 flex-1">
							<p class="text-[15px] font-bold">Daily Challenge</p>
							<p class="mt-0.5 text-[13px] text-muted">Shared 5-drop route.</p>
						</div>
						<span class="mode-arrow"><ChevronRight size={18} /></span>
					</div>
					<div
						class="mode-row"
						tabindex="0"
						role="button"
						on:click={() => startGame(false)}
						on:keydown={(event) => {
							if (event.key === "Enter" || event.key === " ") startGame(false);
						}}
					>
						<div class="mode-icon">🌍</div>
						<div class="min-w-0 flex-1">
							<p class="text-[15px] font-bold">Random Drop</p>
							<p class="mt-0.5 text-[13px] text-muted">Five random campus locations.</p>
						</div>
						<span class="mode-arrow"><ChevronRight size={18} /></span>
					</div>
				</div>

				<button class="btn-3d mt-3 w-full" disabled={starting} type="button" on:click={() => startGame(false)}>
					{starting ? "Starting..." : "Start New Round"}
				</button>
			</section>

			<section class="card">
				<p class="section-label">Recent Games</p>
				<h2>Recent results</h2>
				<p class="desc">Your latest completed games and the difficulty each one used.</p>

				<div class="history-list">
					{#if $recentGames.isLoading}
						<p class="history-empty">Loading recent games...</p>
					{:else if $recentGames.isError}
						<p class="history-empty">Failed to load recent games.</p>
					{:else if $recentGames.data && $recentGames.data.length > 0}
						{#each $recentGames.data as game}
							<button
								class="history-row"
								type="button"
								on:click={() => navigate(`/game/${game.id}/summary`)}
							>
								<div class="history-main">
									<p class="history-title">{formatModeSummary(game.mode)}</p>
									<p class="history-meta">Played {new Date(game.createdAt).toLocaleDateString()}</p>
								</div>
								<div class="history-side">
									<span class="difficulty-pill">{formatDifficultyLabel(game.mode.difficulty)}</span>
									<span class="history-score">{game.totalScore.toLocaleString()} pts</span>
								</div>
							</button>
						{/each}
					{:else}
						<p class="history-empty">No completed games yet.</p>
					{/if}
				</div>
			</section>
		</section>

		{#if multiplayerEnabled}
			<section class="right-column">
				<section class="card">
					<p class="section-label">Multiplayer</p>

					<div class="toggle-bar single-toggle">
						<TogglePills
							ariaLabel="Multiplayer location"
							selected={mpEnvironment}
							options={locationOptions}
							on:change={(event) => {
								if (
									event.detail === "any" ||
									event.detail === "indoor" ||
									event.detail === "outdoor"
								) {
									mpEnvironment = event.detail;
								}
							}}
						/>
					</div>

					<button class="btn-3d mt-3 w-full" disabled={creatingGame} type="button" on:click={createMultiplayerGame}>
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
						<button class="join-btn" disabled={joiningGame || !joinCode.trim()} type="button" on:click={joinMultiplayerGame}>
							{joiningGame ? "..." : "Join"}
						</button>
					</div>

					{#if $activeMultiplayerGame.data}
						<p class="multiplayer-note">
							You already have {$activeMultiplayerGame.data.status === "waiting" ? "a live lobby" : "a live match"} in progress. Use the Active Games panel to return to it.
						</p>
					{/if}
				</section>
			</section>
		{/if}
	</main>
</div>

<style>
	.main {
		width: min(1180px, calc(100% - 32px));
		margin: 16px auto 24px;
		display: grid;
		gap: 14px;
	}

	.left-column,
	.center-column,
	.right-column {
		display: grid;
		gap: 14px;
		align-content: start;
	}

	.section-label {
		margin: 0;
		color: var(--muted);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
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

	.active-games-card {
		border-color: color-mix(in srgb, var(--brand) 36%, var(--line));
	}

	.contribute-card {
		border-color: color-mix(in srgb, var(--gold) 32%, var(--line));
	}

	.contribute-btn {
		margin-top: 14px;
		width: 100%;
	}

	.active-games-list {
		display: grid;
		gap: 10px;
		margin-top: 14px;
	}

	.active-game-item {
		display: grid;
		gap: 12px;
		padding: 14px;
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		background: linear-gradient(180deg, color-mix(in srgb, var(--surface) 88%, white), var(--surface));
	}

	.multiplayer-item {
		border-color: color-mix(in srgb, var(--brand) 28%, var(--line));
	}

	.active-game-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
	}

	.active-game-title {
		margin: 0;
		font-size: 15px;
		font-weight: 800;
		line-height: 1.2;
	}

	.active-game-badge {
		padding: 4px 8px;
		border-radius: 999px;
		background: var(--gold-light);
		color: var(--gold-dark);
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		flex-shrink: 0;
	}

	.active-game-badge--multiplayer {
		background: var(--brand-light);
		color: var(--brand-dark);
	}

	.active-game-meta,
	.active-game-subtle {
		margin: 6px 0 0;
		font-size: 13px;
		line-height: 1.45;
	}

	.active-game-meta {
		color: var(--ink);
		font-weight: 600;
	}

	.active-game-subtle {
		color: var(--muted);
	}

	.active-game-btn {
		width: 100%;
	}

	.active-games-empty {
		padding: 16px 14px;
		border: 1px dashed var(--line);
		border-radius: var(--radius-lg);
		background: color-mix(in srgb, var(--brand-light) 40%, var(--surface));
	}

	.empty-title {
		margin: 0;
		font-size: 14px;
		font-weight: 700;
	}

	.empty-copy {
		margin: 6px 0 0;
		font-size: 13px;
		line-height: 1.45;
		color: var(--muted);
	}

	.toggle-bar {
		display: flex;
		gap: 10px;
		margin-top: 14px;
		flex-wrap: wrap;
	}

	.toggle-group {
		display: grid;
		gap: 6px;
	}

	.toggle-label {
		margin: 0;
		color: var(--muted);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.single-toggle {
		flex-wrap: wrap;
	}

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

	.history-list {
		display: grid;
		gap: 10px;
		margin-top: 14px;
	}

	.history-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		width: 100%;
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		background: var(--surface);
		padding: 12px 14px;
		cursor: pointer;
		text-align: left;
		transition: all 140ms var(--ease);
	}

	.history-row:hover {
		border-color: var(--brand);
		background: var(--brand-light);
		transform: translateX(4px);
	}

	.history-row:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	.history-main {
		min-width: 0;
	}

	.history-title {
		margin: 0;
		font-size: 14px;
		font-weight: 700;
		color: var(--ink);
	}

	.history-meta {
		margin: 4px 0 0;
		font-size: 12px;
		color: var(--muted);
	}

	.history-side {
		display: grid;
		justify-items: end;
		gap: 6px;
		flex-shrink: 0;
	}

	.difficulty-pill {
		border-radius: var(--radius-pill);
		background: var(--gold-light);
		color: var(--gold-dark);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.04em;
		padding: 4px 8px;
		text-transform: uppercase;
	}

	.history-score {
		font-family: "IBM Plex Mono", monospace;
		font-size: 13px;
		font-weight: 700;
		color: var(--ink);
	}

	.history-empty {
		margin: 14px 0 0;
		color: var(--muted);
		font-size: 14px;
	}
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

	.multiplayer-note {
		margin: 12px 0 0;
		font-size: 13px;
		line-height: 1.45;
		color: var(--muted);
	}

	@media (min-width: 980px) {
		.main {
			grid-template-columns: minmax(260px, 0.9fr) minmax(360px, 1.2fr) minmax(260px, 0.9fr);
			align-items: start;
		}
	}

	@media (min-width: 700px) and (max-width: 979px) {
		.main {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.center-column {
			grid-column: 1 / -1;
		}
	}

	@media (min-width: 700px) {
		:global(.card) {
			padding: 18px;
		}
	}

	@media (max-width: 400px) {
		.toggle-bar,
		.join-row {
			flex-wrap: wrap;
		}

		h2 {
			font-size: 20px;
		}

		.mode-icon {
			width: 32px;
			height: 32px;
			font-size: 15px;
		}

		.code-input,
		.join-btn,
		.active-game-btn {
			width: 100%;
		}

		.code-input {
			font-size: 14px;
			padding: 8px 10px;
		}

		.history-row {
			align-items: flex-start;
		}

		.history-side {
			justify-items: start;
		}
	}
</style>
