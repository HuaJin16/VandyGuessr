<script lang="ts">
import { multiplayerService } from "$lib/domains/multiplayer/api/multiplayer.service";
import { auth } from "$lib/shared/auth/auth.store";
import Spinner from "$lib/shared/ui/Spinner.svelte";
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
		const error = err as { response?: { data?: { detail?: string } }; message?: string };
		toast.error(error?.response?.data?.detail || error?.message || "Failed to join game");
		navigate("/", { replace: true });
	} finally {
		isJoining = false;
	}
}
</script>

<div class="join-screen">
	<div class="join-card">
		<Spinner />
		<p class="join-label">Multiplayer</p>
		<p class="join-text">{isJoining ? "Joining match..." : "Redirecting..."}</p>
	</div>
</div>

<style>
	.join-screen {
		position: fixed;
		inset: 0;
		display: grid;
		place-items: center;
		padding: 24px;
		background: var(--canvas);
	}

	.join-card {
		display: grid;
		justify-items: center;
		gap: 12px;
		padding: 28px 32px;
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		background: var(--surface);
		box-shadow: var(--shadow-sm);
	}

	.join-label,
	.join-text {
		margin: 0;
	}

	.join-label {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	.join-text {
		font-size: 15px;
		font-weight: 700;
		color: var(--ink);
	}
</style>
