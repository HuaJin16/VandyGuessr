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
$: gameQueryOptions = { ...gameQueries.byId(id), enabled: $auth.isInitialized };
$: gameQuery = createQuery(gameQueryOptions);

$: if ($gameQuery.data) {
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
		queryClient.setQueryData(["games", id], updated);
	} catch (err: unknown) {
		const e = err as { response?: { data?: { detail?: string } }; message?: string };
		toast.error(e?.response?.data?.detail || e?.message || "Failed to submit guess");
	} finally {
		gameStore.setSubmitting(false);
	}
}

async function handleEndGame() {
	if (!game) return;
	try {
		const ended = await gamesService.end(game.id);
		queryClient.setQueryData(["games", id], ended);
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
		background: #f5f2e9;
	}

	.error-text {
		font-size: 16px;
		font-weight: 500;
		color: rgba(24, 24, 27, 0.6);
	}
</style>
