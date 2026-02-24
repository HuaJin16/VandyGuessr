<script lang="ts">
import { gamesService } from "$lib/domains/games/api/games.service";
import { gameQueries } from "$lib/domains/games/queries/games.queries";
import type { Environment, GameMode } from "$lib/domains/games/types";
import { multiplayerService } from "$lib/domains/multiplayer/api/multiplayer.service";
import type { Environment as MpEnvironment } from "$lib/domains/multiplayer/types";
import { userQueries } from "$lib/domains/users/queries/users.queries";
import { auth } from "$lib/shared/auth/auth.store";
import Avatar from "$lib/shared/components/Avatar.svelte";
import Navbar from "$lib/shared/components/Navbar.svelte";
import TogglePills from "$lib/shared/components/TogglePills.svelte";
import type { ToggleOption } from "$lib/shared/components/TogglePills.svelte";
import { createQuery } from "@tanstack/svelte-query";
import { CalendarDays, ChevronRight, Clock, Globe, Sofa, TreePine } from "lucide-svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

const multiplayerEnabled = import.meta.env.VITE_FEATURE_MULTIPLAYER === "true";

$: user = createQuery({ ...userQueries.me(), enabled: $auth.isInitialized });
$: activeGame = createQuery({ ...gameQueries.active(), enabled: $auth.isInitialized });

$: stats = $user.data?.stats;

$: activeRoundNumber = $activeGame.data
	? $activeGame.data.rounds.filter((r) => r.guess || r.skipped).length + 1
	: 0;

const timingOptions = [
	{ value: "untimed", label: "Untimed", icon: Globe },
	{ value: "timed", label: "Timed", icon: Clock },
] satisfies ToggleOption[];

const locationOptions = [
	{ value: "any", label: "Any" },
	{ value: "indoor", label: "Indoor", icon: Sofa },
	{ value: "outdoor", label: "Outdoor", icon: TreePine },
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

<div class="min-h-screen bg-terrain font-body">
	<Navbar activePage="home" />

	<main class="flex flex-1 items-center justify-center px-3 py-6 sm:px-4 sm:py-12">
		<div class="glass-card w-full max-w-2xl overflow-hidden border border-white/50 shadow-hard-lg">
			<div class="px-4 py-4 sm:px-8 sm:py-6">
				<div class="flex items-center gap-3 sm:gap-4">
					<Avatar name={$user.data?.name ?? ""} size="lg" />
					<div class="min-w-0 flex-1">
						<h2 class="truncate font-heading text-lg font-bold text-charcoal sm:text-2xl">
							{$user.data?.name ?? "Loading..."}
						</h2>
						<p class="truncate text-xs text-charcoal/50 sm:text-sm">
							{$user.data?.email ?? ""}
						</p>
					</div>
				</div>

				<div class="mt-4 flex items-center justify-around border-t border-gray-100 pt-4 sm:mt-5 sm:pt-5">
					<div class="px-2 text-center sm:px-3">
						<div class="mb-1 font-mono text-lg font-bold text-charcoal sm:text-xl">
							{stats?.rank ? `#${stats.rank}` : "\u2014"}
						</div>
						<div class="text-[10px] font-medium uppercase tracking-wider text-charcoal/50">Rank</div>
					</div>
					<div class="h-8 w-px bg-gray-100 sm:h-10"></div>
					<div class="px-2 text-center sm:px-3">
						<div class="mb-1 font-mono text-lg font-bold text-charcoal sm:text-xl">
							{stats?.totalPoints?.toLocaleString() ?? "0"}
						</div>
						<div class="text-[10px] font-medium uppercase tracking-wider text-charcoal/50">Points</div>
					</div>
					<div class="h-8 w-px bg-gray-100 sm:h-10"></div>
					<div class="px-2 text-center sm:px-3">
						<div class="mb-1 font-mono text-lg font-bold text-charcoal sm:text-xl">
							{stats?.gamesPlayed ?? 0}
						</div>
						<div class="text-[10px] font-medium uppercase tracking-wider text-charcoal/50">Games</div>
					</div>
				</div>
			</div>

		<div class="bg-terrain/30 px-4 py-4 sm:p-6">
			{#if $activeGame.data}
				<button
					class="resume-banner"
					on:click={() => navigate(`/game/${$activeGame.data?.id}`)}
				>
					<div class="flex items-center gap-3">
						<div class="resume-dot" />
						<div class="min-w-0 flex-1 text-left">
							<span class="font-heading text-sm font-bold text-charcoal">Game in Progress</span>
							<p class="text-[13px] text-charcoal/50">
								Round {activeRoundNumber}/{$activeGame.data.rounds.length}
								&middot; {$activeGame.data.totalScore.toLocaleString()} pts
							</p>
						</div>
						<ChevronRight size={18} class="flex-shrink-0 text-charcoal/30" />
					</div>
				</button>
			{/if}

			<!-- Daily Challenge banner -->
			<button
				class="daily-banner"
				disabled={starting}
				on:click={() => startGame(true)}
			>
				<div class="flex items-center gap-3">
					<CalendarDays size={20} class="flex-shrink-0 text-gold" />
					<div class="min-w-0 flex-1 text-left">
						<div class="flex items-center gap-2">
							<span class="font-heading text-sm font-bold text-charcoal">Daily Challenge</span>
							<span class="rounded-full bg-gold/20 px-1.5 py-0.5 text-[10px] font-bold uppercase text-gold">2X</span>
						</div>
						<p class="text-[13px] text-charcoal/50">Today's curated round — compete with everyone</p>
					</div>
					<ChevronRight size={18} class="flex-shrink-0 text-charcoal/30" />
				</div>
			</button>

			<!-- Toggle controls -->
			<div class="mt-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:gap-x-5 sm:gap-y-3">
				<div>
					<div class="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-charcoal/40">Timing</div>
					<TogglePills
						ariaLabel="Game timing"
						selected={timed ? "timed" : "untimed"}
						options={timingOptions}
						on:change={(event) => {
							timed = event.detail === "timed";
						}}
					/>
				</div>

				<div>
					<div class="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-charcoal/40">Location</div>
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
			</div>

			<!-- Big Start button -->
			<button
				class="btn-3d mt-5 w-full py-4 text-base sm:mt-6 sm:py-5 sm:text-lg"
				disabled={starting}
				on:click={() => startGame(false)}
			>
				{starting ? "Starting..." : "Start Guessing"}
			</button>

			{#if multiplayerEnabled}
				<div class="multiplayer-section">
					<div class="section-divider">
						<span class="divider-text">Multiplayer</span>
					</div>

					<button
						class="mp-create-btn"
						disabled={creatingGame}
						on:click={createMultiplayerGame}
					>
						<div class="flex items-center gap-3">
							<div class="mp-icon">VS</div>
							<div class="min-w-0 flex-1 text-left">
								<span class="font-heading text-sm font-bold text-charcoal">Create Game</span>
								<p class="text-[13px] text-charcoal/50">Start a lobby and invite friends</p>
							</div>
							<ChevronRight size={18} class="flex-shrink-0 text-charcoal/30" />
						</div>
					</button>

					<div class="join-row">
						<input
							type="text"
							class="join-input"
							placeholder="Enter code"
							maxlength={6}
							bind:value={joinCode}
							on:keydown={(e) => {
								if (e.key === "Enter") joinMultiplayerGame();
							}}
						/>
						<button
							class="join-btn"
							disabled={joiningGame || !joinCode.trim()}
							on:click={joinMultiplayerGame}
						>
							{joiningGame ? "Joining..." : "Join"}
						</button>
					</div>
				</div>
			{/if}

			</div>
		</div>
	</main>
</div>

<style>
	.daily-banner {
		display: block;
		width: 100%;
		border-radius: 12px;
		padding: 14px 16px;
		border: 1.5px dashed rgba(244, 196, 48, 0.5);
		background: rgba(244, 196, 48, 0.06);
		cursor: pointer;
		transition: all 0.15s;
	}

	.resume-banner {
		display: block;
		width: 100%;
		border-radius: 12px;
		padding: 14px 16px;
		margin-bottom: 12px;
		border: 1.5px solid rgba(46, 147, 60, 0.3);
		background: rgba(46, 147, 60, 0.06);
		cursor: pointer;
		transition: all 0.15s;
	}

	.resume-banner:hover {
		border-color: rgba(46, 147, 60, 0.6);
		background: rgba(46, 147, 60, 0.1);
	}

	.resume-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: #2e933c;
		box-shadow: 0 0 0 3px rgba(46, 147, 60, 0.2);
		animation: pulse-dot 2s ease-in-out infinite;
	}

	@keyframes pulse-dot {
		0%, 100% { box-shadow: 0 0 0 3px rgba(46, 147, 60, 0.2); }
		50% { box-shadow: 0 0 0 6px rgba(46, 147, 60, 0.1); }
	}

	.daily-banner:hover {
		border-color: rgba(244, 196, 48, 0.8);
		background: rgba(244, 196, 48, 0.1);
	}

	.daily-banner:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}


	.multiplayer-section {
		margin-top: 24px;
	}

	.section-divider {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 16px;
	}

	.section-divider::before,
	.section-divider::after {
		content: "";
		flex: 1;
		height: 1px;
		background: rgba(0, 0, 0, 0.08);
	}

	.divider-text {
		font-family: "Rubik", sans-serif;
		font-weight: 600;
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: rgba(24, 24, 27, 0.4);
	}

	.mp-create-btn {
		display: block;
		width: 100%;
		border-radius: 12px;
		padding: 14px 16px;
		border: 1.5px solid rgba(59, 130, 246, 0.3);
		background: rgba(59, 130, 246, 0.06);
		cursor: pointer;
		transition: all 0.15s;
	}

	.mp-create-btn:hover {
		border-color: rgba(59, 130, 246, 0.6);
		background: rgba(59, 130, 246, 0.1);
	}

	.mp-create-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.mp-icon {
		width: 36px;
		height: 36px;
		border-radius: 8px;
		background: #3b82f6;
		color: white;
		font-family: "Rubik", sans-serif;
		font-weight: 800;
		font-size: 0.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.join-row {
		display: flex;
		gap: 8px;
		margin-top: 10px;
	}

	.join-input {
		flex: 1;
		padding: 12px 16px;
		border-radius: 12px;
		border: 1px solid rgba(0, 0, 0, 0.1);
		background: white;
		font-family: "Rubik Mono One", monospace;
		font-size: 0.9375rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		text-align: center;
		outline: none;
		transition: border-color 0.15s;
	}

	.join-input:focus {
		border-color: #3b82f6;
	}

	.join-input::placeholder {
		font-family: "Rubik", sans-serif;
		font-weight: 400;
		letter-spacing: normal;
		text-transform: none;
		color: rgba(24, 24, 27, 0.3);
	}

	.join-btn {
		padding: 12px 24px;
		border-radius: 12px;
		background: #3b82f6;
		color: white;
		font-family: "Rubik", sans-serif;
		font-weight: 700;
		font-size: 0.875rem;
		border: none;
		cursor: pointer;
		box-shadow: 0 4px 0 #2563eb;
		transition: transform 0.1s, box-shadow 0.1s;
	}

	.join-btn:hover {
		background: #2563eb;
		transform: translateY(2px);
		box-shadow: 0 2px 0 #2563eb;
	}

	.join-btn:active {
		transform: translateY(4px);
		box-shadow: 0 0 0 #2563eb;
	}

	.join-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
		box-shadow: 0 4px 0 #2563eb;
	}
</style>
