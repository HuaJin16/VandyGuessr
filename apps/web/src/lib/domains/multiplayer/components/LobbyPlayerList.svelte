<script lang="ts">
import Button from "$lib/shared/ui/Button.svelte";
import { createEventDispatcher } from "svelte";
import type { MultiplayerPlayer } from "../types";

export let players: MultiplayerPlayer[];
export let hostId: string;
export let currentUserId: string;
export let maxPlayers = 10;
export let readyPlayers: string[] = [];
export let showReadyToggle = true;

const dispatch = createEventDispatcher<{
	toggleReady: undefined;
	kick: { userId: string };
}>();

const PLAYER_COLORS = [
	"var(--p-you)",
	"var(--p-blue)",
	"var(--p-purple)",
	"var(--p-orange)",
	"var(--p-cyan)",
	"var(--p-pink)",
];

function getColor(index: number, userId: string): string {
	if (userId === currentUserId) return PLAYER_COLORS[0];
	let opponentIdx = 0;
	for (let i = 0; i < players.length; i += 1) {
		if (players[i].userId === currentUserId) continue;
		if (players[i].userId === userId) return PLAYER_COLORS[opponentIdx + 1] ?? PLAYER_COLORS[1];
		opponentIdx += 1;
	}
	return PLAYER_COLORS[(index + 1) % PLAYER_COLORS.length];
}

function getInitials(name: string): string {
	return name
		.split(" ")
		.map((word) => word[0])
		.join("")
		.toUpperCase()
		.slice(0, 2);
}

$: emptySlots = Math.max(0, maxPlayers - players.length);
$: currentUserReady = readyPlayers.includes(currentUserId);

function handleKick(userId: string) {
	dispatch("kick", { userId });
}

function toggleReady() {
	dispatch("toggleReady");
}
</script>

<section class="player-list">
	<div class="player-list__header">
		<div>
			<p class="section-label">Players</p>
			<h2>{players.length} in lobby</h2>
		</div>
		<span class="player-list__count">{players.length}/{maxPlayers}</span>
	</div>

	<div class="player-list__rows">
		{#each players as player, index (player.userId)}
			{@const isYou = player.userId === currentUserId}
			{@const isHost = player.userId === hostId}
			{@const isReady = readyPlayers.includes(player.userId)}
			{@const canKick = hostId === currentUserId && !isHost}
			{@const color = getColor(index, player.userId)}
			<div class={`player-row ${isYou ? "player-row--you" : ""}`}>
				<div class="player-avatar" style="background: {color};">
					{#if player.avatarUrl}
						<img src={player.avatarUrl} alt={player.name} class="player-avatar__image" />
					{:else}
						{getInitials(player.name)}
					{/if}
				</div>

				<div class="player-copy">
					<p class="player-copy__name">{player.name}</p>
					<p class="player-copy__meta">
						{#if player.status === "disconnected"}
							Reconnecting...
						{:else if player.status === "forfeited"}
							Left the match
						{:else}
							Connected
						{/if}
					</p>
				</div>

				<div class="player-badges">
					{#if isHost}
						<span class="badge badge-host">Host</span>
					{/if}
					{#if isYou}
						<span class="badge badge-you">You</span>
					{/if}
					{#if isReady}
						<span class="badge badge-ready">Ready</span>
					{/if}
				</div>

				{#if canKick}
					<Button variant="outline" size="sm" type="button" on:click={() => handleKick(player.userId)}>
						Kick
					</Button>
				{/if}
			</div>
		{/each}

		{#each Array(emptySlots) as _, index}
			<div class="player-row player-row--empty" aria-hidden="true">
				<div class="player-avatar player-avatar--empty">?</div>
				<div class="player-copy">
					<p class="player-copy__name">Open slot {index + 1}</p>
					<p class="player-copy__meta">Waiting for another player to join.</p>
				</div>
			</div>
		{/each}
	</div>

	{#if showReadyToggle && players.some((player) => player.userId === currentUserId)}
		<Button class="w-full" variant={currentUserReady ? "secondary" : "default"} size="lg" on:click={toggleReady}>
			{currentUserReady ? "Unready" : "Ready Up"}
		</Button>
	{/if}
</section>

<style>
	.player-list {
		display: grid;
		gap: 16px;
	}

	.player-list__header {
		display: flex;
		justify-content: space-between;
		align-items: end;
		gap: 12px;
	}

	.section-label,
	.player-list__count,
	.player-copy__name,
	.player-copy__meta,
	h2 {
		margin: 0;
	}

	.section-label {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	h2 {
		margin-top: 6px;
		font-size: 22px;
		font-weight: 800;
		line-height: 1.1;
		letter-spacing: -0.03em;
	}

	.player-list__count {
		font-family: "IBM Plex Mono", monospace;
		font-size: 13px;
		font-weight: 700;
		color: var(--muted);
	}

	.player-list__rows {
		display: grid;
		gap: 10px;
	}

	.player-row {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) auto auto;
		gap: 12px;
		align-items: center;
		padding: 14px 16px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
	}

	.player-row--you {
		background: color-mix(in srgb, var(--brand-quiet) 90%, var(--surface));
		border-color: color-mix(in srgb, var(--brand) 24%, var(--line));
	}

	.player-row--empty {
		border-style: dashed;
		background: var(--surface-subtle);
	}

	.player-avatar {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		color: #fff;
		font-size: 12px;
		font-weight: 700;
		display: grid;
		place-items: center;
		flex-shrink: 0;
		overflow: hidden;
	}

	.player-avatar__image {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.player-avatar--empty {
		background: var(--surface-strong);
		color: var(--muted);
	}

	.player-copy {
		min-width: 0;
	}

	.player-copy__name {
		font-size: 15px;
		font-weight: 700;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.player-copy__meta {
		margin-top: 4px;
		font-size: 12px;
		line-height: 1.45;
		color: var(--muted);
	}

	.player-badges {
		display: flex;
		flex-wrap: wrap;
		justify-content: flex-end;
		gap: 6px;
	}

	.badge {
		font-size: 10px;
		font-weight: 800;
		padding: 3px 8px;
		border-radius: var(--radius-pill);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.badge-host {
		background: var(--gold-light);
		color: var(--gold-ink);
	}

	.badge-you {
		background: var(--brand-light);
		color: var(--brand-dark);
	}

	.badge-ready {
		background: var(--success-light);
		color: var(--success-ink);
	}

	@media (max-width: 640px) {
		.player-row {
			grid-template-columns: auto minmax(0, 1fr);
		}

		.player-badges {
			grid-column: 2;
			justify-content: flex-start;
		}
	}
</style>
