<script lang="ts">
import { gamesService } from "$lib/domains/games/api/games.service";
import { gameQueries } from "$lib/domains/games/queries/games.queries";
import type { Environment, GameMode } from "$lib/domains/games/types";
import { userQueries } from "$lib/domains/users/queries/users.queries";
import { auth } from "$lib/shared/auth/auth.store";
import { createQuery } from "@tanstack/svelte-query";
import {
	CalendarDays,
	ChevronRight,
	Clock,
	Globe,
	LogOut,
	Sofa,
	TreePine,
	Trophy as TrophyIcon,
} from "lucide-svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";
import logo from "../../assets/logo.webp";

$: user = createQuery({ ...userQueries.me(), enabled: $auth.isInitialized });
$: activeGame = createQuery({ ...gameQueries.active(), enabled: $auth.isInitialized });

$: stats = $user.data?.stats;
$: initials = ($user.data?.name ?? "")
	.split(" ")
	.map((w) => w[0])
	.join("")
	.slice(0, 2)
	.toUpperCase();

$: activeRoundNumber = $activeGame.data
	? $activeGame.data.rounds.filter((r) => r.guess || r.skipped).length + 1
	: 0;

let timed = false;
let environment: Environment = "any";

let starting = false;

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
	<header class="sticky top-0 z-50 border-b border-gray-100 bg-white">
		<div class="mx-auto flex max-w-4xl items-center justify-between px-4 py-3 sm:px-6 sm:py-4">
			<div class="flex items-center gap-2 sm:gap-3">
				<img src={logo} alt="VandyGuessr" class="h-9 w-9 sm:h-10 sm:w-10" />
				<span class="font-heading text-base font-bold text-charcoal sm:text-xl">
					VandyGuessr
				</span>
			</div>

			<div class="flex items-center gap-1 sm:gap-2">
				<a
					href="/leaderboard"
					class="flex items-center gap-1.5 rounded-lg p-2 text-xs font-medium text-charcoal/60 transition-colors hover:bg-charcoal/5 hover:text-jungle sm:text-sm"
				>
					<TrophyIcon size={18} />
					Leaderboard
				</a>
				<button
					class="flex items-center gap-1.5 rounded-lg p-2 text-xs font-medium text-charcoal/50 transition-colors hover:bg-charcoal/5 hover:text-clay sm:text-sm"
					on:click={() => auth.logout()}
				>
					<LogOut size={18} />
					Logout
				</button>
			</div>
		</div>
	</header>

	<main class="flex flex-1 items-center justify-center px-3 py-6 sm:px-4 sm:py-12">
		<div class="glass-card w-full max-w-2xl overflow-hidden border border-white/50 shadow-hard-lg">
			<div class="px-4 py-4 sm:px-8 sm:py-6">
				<div class="flex items-center gap-3 sm:gap-4">
					<div class="avatar-initials flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full font-heading text-base font-bold text-white shadow-hard sm:h-16 sm:w-16 sm:text-xl">
						{initials || "?"}
					</div>
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
					<div class="toggle-group">
						<button
							class={timed ? "toggle-inactive" : "toggle-active"}
							on:click={() => { timed = false; }}
						><Globe size={14} /> Untimed</button>
						<button
							class={timed ? "toggle-active" : "toggle-inactive"}
							on:click={() => { timed = true; }}
						><Clock size={14} /> Timed</button>
					</div>
				</div>

				<div>
					<div class="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-charcoal/40">Location</div>
					<div class="toggle-group">
						<button
							class={environment === "any" ? "toggle-active" : "toggle-inactive"}
							on:click={() => { environment = "any"; }}
						>Any</button>
						<button
							class={environment === "indoor" ? "toggle-active" : "toggle-inactive"}
							on:click={() => { environment = "indoor"; }}
						><Sofa size={14} /> Indoor</button>
						<button
							class={environment === "outdoor" ? "toggle-active" : "toggle-inactive"}
							on:click={() => { environment = "outdoor"; }}
						><TreePine size={14} /> Outdoor</button>
					</div>
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

			</div>
		</div>
	</main>
</div>

<style>
	.avatar-initials {
		background: linear-gradient(135deg, #2e933c 0%, #236e2d 100%);
	}

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

	.toggle-group {
		display: flex;
		border-radius: 9999px;
		padding: 3px;
		border: 1px solid rgba(0, 0, 0, 0.08);
		background: white;
	}

	@media (min-width: 640px) {
		.toggle-group {
			display: inline-flex;
		}
	}

	.toggle-active {
		display: inline-flex;
		flex: 1;
		align-items: center;
		justify-content: center;
		gap: 5px;
		background: #2e933c;
		color: white;
		border-radius: 9999px;
		padding: 7px 16px;
		font-size: 13px;
		font-weight: 600;
		transition: all 0.15s;
	}

	@media (min-width: 640px) {
		.toggle-active {
			flex: none;
		}
	}

	.toggle-inactive {
		display: inline-flex;
		flex: 1;
		align-items: center;
		justify-content: center;
		gap: 5px;
		background: transparent;
		color: #18181b;
		border-radius: 9999px;
		padding: 7px 16px;
		font-size: 13px;
		font-weight: 500;
		transition: all 0.15s;
		cursor: pointer;
	}

	@media (min-width: 640px) {
		.toggle-inactive {
			flex: none;
		}
	}

	.toggle-inactive:hover {
		background: rgba(46, 147, 60, 0.08);
	}
</style>
