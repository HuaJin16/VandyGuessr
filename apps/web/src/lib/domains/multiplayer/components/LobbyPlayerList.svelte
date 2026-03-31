<script lang="ts">
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
	for (let i = 0; i < players.length; i++) {
		if (players[i].userId === currentUserId) continue;
		if (players[i].userId === userId) return PLAYER_COLORS[opponentIdx + 1] ?? PLAYER_COLORS[1];
		opponentIdx++;
	}
	return PLAYER_COLORS[(index + 1) % PLAYER_COLORS.length];
}

function getInitials(name: string): string {
	return name
		.split(" ")
		.map((w) => w[0])
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

<section class="card p-0 sm:p-0">
	<div class="flex items-center justify-between px-4 pt-4 sm:px-[18px] sm:pt-[18px]">
		<p class="text-sm font-bold text-[var(--ink)]">Players</p>
		<span class="font-mono text-[13px] font-semibold text-[var(--muted)]">
			{players.length}<span class="opacity-50">/{maxPlayers}</span>
		</span>
	</div>

	<div class="grid gap-1.5 px-4 pb-4 pt-2.5 sm:px-[18px] sm:pb-[18px]">
		{#each players as player, i (player.userId)}
			{@const isYou = player.userId === currentUserId}
			{@const isHost = player.userId === hostId}
			{@const isReady = readyPlayers.includes(player.userId)}
			{@const canKick = hostId === currentUserId && !isHost}
			{@const color = getColor(i, player.userId)}
			<div
				class="player-row"
				class:is-you={isYou}
			>
				<div class="player-avatar" style="background: {color};">
					{#if player.avatarUrl}
						<img src={player.avatarUrl} alt={player.name} class="h-full w-full rounded-full object-cover" />
					{:else}
						{getInitials(player.name)}
					{/if}
					{#if player.status === "connected"}
						<div class="player-online" class:you-bg={isYou} />
					{/if}
				</div>
				<p class="player-name">{player.name}</p>
				{#if isHost}
					<span class="badge badge-host">Host</span>
				{/if}
				{#if isYou}
					<span class="badge badge-you">You</span>
				{/if}
				{#if isReady}
					<span class="badge badge-ready">Ready</span>
				{/if}
				{#if player.status === "disconnected"}
					<span class="text-xs font-medium text-[var(--muted)]">Reconnecting...</span>
				{:else if player.status === "forfeited"}
					<span class="text-xs font-medium text-[var(--danger)]">Left</span>
				{/if}
				{#if canKick}
					<button class="kick-btn" on:click={() => handleKick(player.userId)} aria-label={`Kick ${player.name}`}>
						Kick
					</button>
				{/if}
			</div>
		{/each}

		{#if showReadyToggle && players.some((player) => player.userId === currentUserId)}
			<button class="ready-btn" class:ready={currentUserReady} on:click={toggleReady}>
				{currentUserReady ? "Unready" : "Ready"}
			</button>
		{/if}

		{#each Array(emptySlots) as _}
			<div class="empty-row">
				<div class="empty-avatar">
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b5b0a6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
						<circle cx="9" cy="7" r="4" />
						<line x1="19" y1="8" x2="19" y2="14" />
						<line x1="22" y1="11" x2="16" y2="11" />
					</svg>
				</div>
				<p class="empty-text">Waiting for player<span class="dots" /></p>
			</div>
		{/each}
	</div>
</section>

<style>
	.player-row {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 10px 12px;
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		background: var(--surface);
	}

	.player-row.is-you {
		background: var(--brand-light);
		border-color: var(--brand);
	}

	.player-avatar {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		color: #fff;
		font-size: 12px;
		font-weight: 700;
		display: grid;
		place-items: center;
		flex-shrink: 0;
		position: relative;
	}

	.player-online {
		position: absolute;
		bottom: -1px;
		right: -1px;
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--brand);
		border: 2px solid var(--surface);
	}

	.player-online.you-bg {
		border-color: #e8f5e9;
	}

	.player-name {
		margin: 0;
		font-size: 14px;
		font-weight: 600;
		flex: 1;
		min-width: 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.badge {
		font-size: 10px;
		font-weight: 700;
		padding: 2px 7px;
		border-radius: var(--radius-pill);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		flex-shrink: 0;
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
		background: #dff3e3;
		color: #20723a;
	}

	.ready-btn {
		border: none;
		border-radius: var(--radius-md);
		background: #e7efe9;
		color: var(--muted);
		font-size: 13px;
		font-weight: 700;
		padding: 10px 14px;
		cursor: pointer;
		transition: all 120ms var(--ease);
	}

	.ready-btn.ready {
		background: #dff3e3;
		color: #20723a;
	}

	.kick-btn {
		border: 1px solid rgba(220, 74, 58, 0.35);
		background: var(--danger-light);
		color: var(--danger-ink);
		font-size: 11px;
		font-weight: 700;
		padding: 4px 8px;
		border-radius: var(--radius-sm);
		cursor: pointer;
		transition: all 120ms var(--ease);
	}

	.kick-btn:hover {
		background: #f6d9d6;
	}

	.empty-row {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 10px 12px;
		border: 2px dashed var(--line);
		border-radius: var(--radius-md);
		opacity: 0.45;
	}

	.empty-avatar {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		background: var(--line);
		display: grid;
		place-items: center;
		flex-shrink: 0;
	}

	.empty-text {
		margin: 0;
		font-size: 13px;
		font-weight: 500;
		color: var(--muted);
	}

	@keyframes dots {
		0% { content: ""; }
		25% { content: "."; }
		50% { content: ".."; }
		75% { content: "..."; }
	}

	.dots::after {
		content: "";
		animation: dots 1.5s steps(4, end) infinite;
	}
</style>
