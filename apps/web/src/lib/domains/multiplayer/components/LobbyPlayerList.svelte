<script lang="ts">
import type { MultiplayerPlayer } from "../types";

export let players: MultiplayerPlayer[];
export let hostId: string;

const statusColors: Record<string, string> = {
	connected: "#2e933c",
	disconnected: "#d95d39",
	forfeited: "#9a9a9a",
};
</script>

<div class="player-list">
	{#each players as player (player.userId)}
		<div class="player-row">
			<div class="avatar-wrapper">
				{#if player.avatarUrl}
					<img src={player.avatarUrl} alt={player.name} class="avatar" />
				{:else}
					<div class="avatar placeholder">
						{player.name.charAt(0).toUpperCase()}
					</div>
				{/if}
				<span
					class="status-dot"
					style="background: {statusColors[player.status] ?? '#9a9a9a'}"
				/>
			</div>
			<div class="player-info">
				<span class="name">
					{player.name}
					{#if player.userId === hostId}
						<span class="host-badge">Host</span>
					{/if}
				</span>
				{#if player.status === "disconnected"}
					<span class="status-text">Reconnecting...</span>
				{:else if player.status === "forfeited"}
					<span class="status-text">Left</span>
				{/if}
			</div>
		</div>
	{/each}
</div>

<style>
	.player-list {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.player-row {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 8px 12px;
		border-radius: 12px;
		background: rgba(0, 0, 0, 0.03);
	}
	.avatar-wrapper {
		position: relative;
		flex-shrink: 0;
	}
	.avatar {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		object-fit: cover;
	}
	.avatar.placeholder {
		display: flex;
		align-items: center;
		justify-content: center;
		background: #2e933c;
		color: white;
		font-family: "Rubik", sans-serif;
		font-weight: 700;
		font-size: 1rem;
	}
	.status-dot {
		position: absolute;
		bottom: 0;
		right: 0;
		width: 12px;
		height: 12px;
		border-radius: 50%;
		border: 2px solid white;
	}
	.player-info {
		display: flex;
		flex-direction: column;
	}
	.name {
		font-family: "Rubik", sans-serif;
		font-weight: 600;
		font-size: 0.9375rem;
		color: #18181b;
	}
	.host-badge {
		display: inline-block;
		font-size: 0.6875rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #f4c430;
		background: rgba(244, 196, 48, 0.15);
		padding: 1px 6px;
		border-radius: 4px;
		margin-left: 6px;
		vertical-align: middle;
	}
	.status-text {
		font-size: 0.75rem;
		color: #9a9a9a;
	}
</style>
