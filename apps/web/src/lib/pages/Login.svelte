<script lang="ts">
import {
	auth,
	authError,
	isAuthFlowLoading,
	isGoogleLoading,
	isLoading,
	isMicrosoftLoading,
} from "$lib/shared/auth/auth.store";
import { renderGoogleSignInButton } from "$lib/shared/auth/googleIdentity";
import { onMount } from "svelte";
import { toast } from "svelte-sonner";
import logo from "../../assets/logo.webp";

const isVanderbiltRestricted =
	import.meta.env.VITE_FEATURE_VANDERBILT_RESTRICTED_LOGINS !== "false";

let googleButtonContainer: HTMLDivElement;
let googleButtonReady = false;

$: isGoogleButtonDisabled = $isLoading || $isAuthFlowLoading || !googleButtonReady;

async function setupGoogleButton() {
	if (!googleButtonContainer) return;

	const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
	if (!clientId) {
		toast.error("Google OAuth is not configured");
		auth.failGoogleLogin("Google OAuth is not configured");
		return;
	}

	try {
		await renderGoogleSignInButton({
			container: googleButtonContainer,
			clientId,
			onSuccess: (token) => {
				void auth.completeGoogleLogin(token);
			},
			onError: (message) => {
				auth.failGoogleLogin(message);
			},
		});
		googleButtonReady = true;
	} catch (error) {
		const message = error instanceof Error ? error.message : "Failed to load Google sign-in";
		toast.error(message);
		auth.failGoogleLogin(message);
	}
}

onMount(() => {
	if (!isVanderbiltRestricted) {
		void setupGoogleButton();
	}
});
</script>

<div class="flex min-h-screen items-center justify-center bg-canvas px-4 py-12">
	<div class="w-full" style="max-width: 480px;">
		<main class="card text-center">
			<div class="flex items-center justify-center gap-2.5">
				<img src={logo} alt="" class="h-10 w-10 rounded-md" />
				<span class="text-[20px] font-bold text-ink">VandyGuessr</span>
			</div>

			<h1 class="mt-5 text-[32px] font-bold leading-[1.15] text-ink">
				How well do you know campus?
			</h1>

			<p class="mt-2 text-[15px] leading-relaxed text-muted">
				Explore real Vanderbilt locations, drop your pin, and see where you rank among classmates.
			</p>

			{#if $authError}
				<div class="mt-4 rounded-[var(--radius-sm)] border border-danger/20 bg-danger-light px-4 py-3">
					<p class="text-sm text-danger-ink">{$authError}</p>
					<button
						class="mt-2 text-xs font-medium text-muted underline hover:text-ink"
						on:click={() => auth.clearError()}
					>
						Dismiss
					</button>
				</div>
			{/if}

			<p class="mt-6 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted/60">
				{isVanderbiltRestricted ? "Made exclusively for Vanderbilt students" : "Sign in to get started"}
			</p>

			<div class="mt-4 flex w-full flex-col gap-4">
				<button
					class="btn-3d flex w-full items-center justify-center gap-3 text-[15px]"
					disabled={$isLoading || $isAuthFlowLoading}
					on:click={() => auth.loginWithMicrosoft()}
				>
					<svg width="20" height="20" viewBox="0 0 21 21" fill="none" aria-hidden="true">
						<rect x="1" y="1" width="9" height="9" fill="#F25022" />
						<rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
						<rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
						<rect x="11" y="11" width="9" height="9" fill="#FFB900" />
					</svg>
					{$isMicrosoftLoading ? "Loading..." : "Continue with Vanderbilt"}
				</button>

				{#if !isVanderbiltRestricted}
					<div class={`google-provider-wrap ${isGoogleButtonDisabled ? "google-provider-wrap-disabled" : ""}`}>
						<button
							type="button"
							class="btn-3d google-provider-visual flex w-full items-center justify-center gap-3 text-[15px]"
							disabled={isGoogleButtonDisabled}
						>
							<svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
								<path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.7 1.1 7.8 2.9l5.7-5.7C33.8 6.1 29.2 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.3-.4-3.5z" />
								<path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 18.9 12 24 12c3 0 5.7 1.1 7.8 2.9l5.7-5.7C33.8 6.1 29.2 4 24 4c-7.7 0-14.3 4.3-17.7 10.7z" />
								<path fill="#4CAF50" d="M24 44c5.1 0 9.8-1.9 13.4-5.1l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.3 0-9.7-3.3-11.4-8l-6.5 5C9.5 39.5 16.2 44 24 44z" />
								<path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-1 2.7-2.8 4.8-5.1 6.2l6.2 5.2C36 39.7 44 34 44 24c0-1.3-.1-2.3-.4-3.5z" />
							</svg>
							{$isGoogleLoading ? "Loading..." : "Continue with Google"}
						</button>

						<div
							bind:this={googleButtonContainer}
							class={`google-provider-overlay ${isGoogleButtonDisabled ? "google-provider-overlay-disabled" : ""}`}
							aria-hidden="true"
						/>
					</div>

					{#if $isGoogleLoading}
						<p class="text-[12px] text-muted">Finishing Google sign-in...</p>
					{/if}
				{/if}
			</div>
		</main>

		<div class="card mt-4">
			<p class="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted/60">
				How it works
			</p>

			<div class="mt-5 flex flex-col gap-4">
				<div class="flex items-center gap-3.5 text-left">
					<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand/8">
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
							<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
							<circle cx="12" cy="10" r="3" />
						</svg>
					</div>
					<div>
						<p class="text-[13px] font-medium text-ink">See a spot on campus</p>
						<p class="mt-0.5 text-[12px] leading-snug text-muted">You're dropped into a real panorama somewhere on Vanderbilt's campus</p>
					</div>
				</div>

				<div class="flex items-center gap-3.5 text-left">
					<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand/8">
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
							<circle cx="12" cy="12" r="10" />
							<circle cx="12" cy="12" r="6" />
							<circle cx="12" cy="12" r="2" />
						</svg>
					</div>
					<div>
						<p class="text-[13px] font-medium text-ink">Place your guess</p>
						<p class="mt-0.5 text-[12px] leading-snug text-muted">Drop a pin on the map where you think the photo was taken</p>
					</div>
				</div>

				<div class="flex items-center gap-3.5 text-left">
					<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand/8">
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
							<path d="M18 20V10" /><path d="M12 20V4" /><path d="M6 20v-6" />
						</svg>
					</div>
					<div>
						<p class="text-[13px] font-medium text-ink">Climb the ranks</p>
						<p class="mt-0.5 text-[12px] leading-snug text-muted">Earn points for accuracy and compete on the leaderboard</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
