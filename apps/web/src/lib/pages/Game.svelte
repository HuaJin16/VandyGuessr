<script lang="ts">
import { gamesService } from "$lib/domains/games/api/games.service";
import GameplayView from "$lib/domains/games/components/GameplayView.svelte";
import RoundResultsView from "$lib/domains/games/components/RoundResultsView.svelte";
import { gameQueries } from "$lib/domains/games/queries/games.queries";
import { currentRound, gameStore } from "$lib/domains/games/stores/game.store";
import { auth } from "$lib/shared/auth/auth.store";
import { createQuery, useQueryClient } from "@tanstack/svelte-query";
import { onDestroy } from "svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

export let id: string;

const queryClient = useQueryClient();
$: gameQueryOptions = {
	...gameQueries.byId(id, $auth.currentUserOid),
	enabled: $auth.currentUserOid !== null,
};
$: gameQuery = createQuery(gameQueryOptions);

let hydratedFromQuery = false;

$: if ($gameQuery.data && !hydratedFromQuery) {
	hydratedFromQuery = true;
	gameStore.setGame($gameQuery.data);
}

$: game = $gameStore.game;
$: round = $currentRound;
$: phase = $gameStore.phase;

async function handleGuess() {
	if (!game || !round || !$gameStore.guessPosition) return;

	gameStore.setSubmitting(true);
	const roundNumber = $gameStore.currentRoundIndex + 1;
	try {
		const updated = await gamesService.submitGuess(game.id, roundNumber, $gameStore.guessPosition);
		gameStore.showResults(updated, $gameStore.currentRoundIndex);
		queryClient.setQueryData(gameQueryOptions.queryKey, updated);
	} catch (err: unknown) {
		const e = err as {
			response?: { status?: number; data?: { detail?: string } };
			message?: string;
		};
		if (e?.response?.status === 409) {
			await refetchAndReconcile("Round expired — moving to next round.");
			return;
		}
		toast.error(e?.response?.data?.detail || e?.message || "Failed to submit guess");
	} finally {
		gameStore.setSubmitting(false);
	}
}

async function handleTimerExpiry() {
	if (!game) return;

	if ($gameStore.guessPosition) {
		await handleGuess();
		return;
	}

	toast.info("Time's up! Round skipped.");
	await refetchAndReconcile();
}

async function refetchAndReconcile(message?: string) {
	if (!game) return;
	try {
		const updated = await gamesService.getById(game.id);
		if (!updated) return;
		queryClient.setQueryData(gameQueryOptions.queryKey, updated);
		if (updated.status !== "active") {
			navigate(`/game/${updated.id}/summary`, { replace: true });
			return;
		}
		gameStore.setGame(updated);
		if (message) toast.info(message);
	} catch {
		toast.error("Failed to refresh game state");
	}
}

async function handleEndGame() {
	if (!game) return;
	try {
		const ended = await gamesService.end(game.id);
		queryClient.setQueryData(gameQueryOptions.queryKey, ended);
		gameStore.updateGame(ended);
		gameStore.toggleEndDialog();
		navigate("/", { replace: true });
	} catch (err: unknown) {
		const e = err as { response?: { data?: { detail?: string } }; message?: string };
		toast.error(e?.response?.data?.detail || e?.message || "Failed to end game");
	}
}

function handleNextRound() {
	gameStore.nextRound();
}

function handleFinish() {
	if (!game) return;
	navigate(`/game/${game.id}/summary`, { replace: true });
}

onDestroy(() => {
	gameStore.reset();
});
</script>

{#if $gameQuery.isLoading}
	<div class="loading-screen">
		<div class="loading-spinner" />
	</div>
{:else if $gameQuery.isError}
	<div class="error-screen">
		<p class="error-text">Failed to load game</p>
		<button class="btn-3d" on:click={() => navigate("/", { replace: true })}>
			Go Home
		</button>
	</div>
{:else if game && round}
	{#if phase === "playing"}
		<GameplayView
			{game}
			onGuess={handleGuess}
			onTimerExpiry={handleTimerExpiry}
			onEndGame={handleEndGame}
		/>
	{:else}
		<RoundResultsView
			{game}
			{round}
			roundIndex={$gameStore.currentRoundIndex}
			onNextRound={handleNextRound}
			onFinish={handleFinish}
		/>
	{/if}
{/if}

<style>
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
		to {
			transform: rotate(360deg);
		}
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
</style>
