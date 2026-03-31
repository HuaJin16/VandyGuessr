<script lang="ts">
import { multiplayerService } from "$lib/domains/multiplayer/api/multiplayer.service";
import { auth } from "$lib/shared/auth/auth.store";
import { onMount } from "svelte";
import { navigate } from "svelte-routing";
import { toast } from "svelte-sonner";

export let code: string;

let isJoining = true;
let hasStartedJoin = false;

onMount(() => {
	if ($auth.isInitialized && !hasStartedJoin) {
		hasStartedJoin = true;
		void joinByLink();
	}
});

$: if ($auth.isInitialized && !hasStartedJoin) {
	hasStartedJoin = true;
	void joinByLink();
}

async function joinByLink() {
	if (!$auth.isInitialized) {
		return;
	}

	const inviteCode = code.trim().toUpperCase();
	if (!inviteCode) {
		toast.error("Invite code is missing");
		navigate("/", { replace: true });
		return;
	}

	try {
		const game = await multiplayerService.join({ code: inviteCode });
		navigate(`/multiplayer/${game.id}/lobby`, { replace: true });
	} catch (err: unknown) {
		const e = err as { response?: { data?: { detail?: string } }; message?: string };
		toast.error(e?.response?.data?.detail || e?.message || "Failed to join game");
		navigate("/", { replace: true });
	} finally {
		isJoining = false;
	}
}
</script>

<div class="join-screen">
	<div class="loading-spinner" />
	<p class="join-text">{isJoining ? "Joining game..." : "Redirecting..."}</p>
</div>

<style>
	.join-screen {
		position: fixed;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 12px;
		background: var(--canvas);
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 4px solid rgba(24, 24, 27, 0.1);
		border-top-color: var(--brand);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.join-text {
		margin: 0;
		font-size: 14px;
		font-weight: 600;
		color: var(--muted);
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
