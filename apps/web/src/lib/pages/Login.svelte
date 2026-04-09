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
import Button from "$lib/shared/ui/Button.svelte";
import { onMount } from "svelte";
import { toast } from "svelte-sonner";
import logo from "../../assets/VandyGuessr_Logo.png";

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

<div class="login-page">
	<div class="login-container">
		<div class="login-header">
			<div class="login-logo-wrap">
				<img src={logo} alt="VandyGuessr" class="login-logo" />
			</div>
			<h1 class="login-title">How well do you know campus?</h1>
			<p class="login-subtitle">
				Explore 360-degree Vanderbilt panoramas, place your pin, and compete on the leaderboard.
			</p>
		</div>

		{#if $authError}
			<div class="login-error" role="alert">
				<p>{$authError}</p>
				<button type="button" on:click={() => auth.clearError()}>Dismiss</button>
			</div>
		{/if}

		<div class="login-actions">
			<Button
				class="w-full justify-center text-[15px]"
				size="lg"
				disabled={$isLoading || $isAuthFlowLoading}
				on:click={() => auth.loginWithMicrosoft()}
			>
				<svg width="20" height="20" viewBox="0 0 21 21" fill="none" aria-hidden="true">
					<rect x="1" y="1" width="9" height="9" fill="#F25022" />
					<rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
					<rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
					<rect x="11" y="11" width="9" height="9" fill="#FFB900" />
				</svg>
				{$isMicrosoftLoading ? "Signing in..." : "Continue with Vanderbilt"}
			</Button>

			{#if !isVanderbiltRestricted}
				<div class={`google-wrap ${isGoogleButtonDisabled ? "google-wrap--disabled" : ""}`}>
					<Button
						variant="outline"
						size="lg"
						class="pointer-events-none w-full justify-center text-[15px]"
						disabled={isGoogleButtonDisabled}
					>
						<svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
							<path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.7 1.1 7.8 2.9l5.7-5.7C33.8 6.1 29.2 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.3-.4-3.5z" />
							<path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 18.9 12 24 12c3 0 5.7 1.1 7.8 2.9l5.7-5.7C33.8 6.1 29.2 4 24 4c-7.7 0-14.3 4.3-17.7 10.7z" />
							<path fill="#4CAF50" d="M24 44c5.1 0 9.8-1.9 13.4-5.1l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.3 0-9.7-3.3-11.4-8l-6.5 5C9.5 39.5 16.2 44 24 44z" />
							<path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-1 2.7-2.8 4.8-5.1 6.2l6.2 5.2C36 39.7 44 34 44 24c0-1.3-.1-2.3-.4-3.5z" />
						</svg>
						{$isGoogleLoading ? "Signing in..." : "Continue with Google"}
					</Button>
					<div
						bind:this={googleButtonContainer}
						class={`google-overlay ${isGoogleButtonDisabled ? "google-overlay--disabled" : ""}`}
						aria-hidden="true"
					/>
				</div>
			{/if}
		</div>

		<div class="login-features">
			<div class="login-feature">
				<div class="login-feature-dot" />
				<span>360-degree campus panoramas</span>
			</div>
			<div class="login-feature">
				<div class="login-feature-dot" />
				<span>Solo and multiplayer modes</span>
			</div>
			<div class="login-feature">
				<div class="login-feature-dot" />
				<span>Daily challenges and leaderboards</span>
			</div>
		</div>
	</div>
</div>

<style>
	.login-page {
		min-height: 100vh;
		display: grid;
		place-items: center;
		padding: 24px 16px;
	}

	.login-container {
		width: 100%;
		max-width: 400px;
		display: grid;
		gap: 32px;
	}

	.login-header {
		text-align: center;
		display: grid;
		gap: 14px;
		justify-items: center;
	}

	.login-logo-wrap {
		width: min(320px, 82vw);
		height: clamp(56px, 11vw, 80px);
	}

	.login-logo {
		display: block;
		width: 100%;
		height: 100%;
		object-fit: cover;
		object-position: center;
	}

	.login-title {
		margin: 0;
		font-size: 32px;
		line-height: 1.1;
		font-weight: 700;
		letter-spacing: -0.03em;
		color: var(--ink);
	}

	.login-subtitle {
		margin: 0;
		font-size: 15px;
		line-height: 1.55;
		color: var(--muted);
		max-width: 36ch;
	}

	.login-error {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 12px 14px;
		border: 1px solid color-mix(in srgb, var(--danger) 20%, var(--line));
		border-radius: var(--radius-md);
		background: var(--danger-light);
	}

	.login-error p {
		margin: 0;
		font-size: 13px;
		line-height: 1.45;
		color: var(--danger-ink);
	}

	.login-error button {
		border: none;
		background: transparent;
		color: var(--danger-ink);
		font-weight: 600;
		font-size: 13px;
		cursor: pointer;
		flex-shrink: 0;
	}

	.login-actions {
		display: grid;
		gap: 12px;
	}

	.google-wrap {
		position: relative;
		width: 100%;
		min-height: 48px;
	}

	.google-overlay {
		position: absolute;
		inset: 0;
		opacity: 0;
		border-radius: var(--radius-md);
	}

	.google-wrap--disabled {
		opacity: 0.72;
	}

	.google-overlay--disabled {
		pointer-events: none;
	}

	.login-features {
		display: flex;
		justify-content: center;
		gap: 20px;
		flex-wrap: wrap;
	}

	.login-feature {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 13px;
		color: var(--muted);
	}

	.login-feature-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--brand);
		flex-shrink: 0;
	}
</style>
