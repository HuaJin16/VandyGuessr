<script lang="ts">
import { auth, authError, isLoading } from "$lib/shared/auth/auth.store";
import logo from "../../assets/logo.webp";
</script>

<div class="flex min-h-screen items-center justify-center p-4">
	<div class="w-full max-w-md">
		<div class="glass-card px-8 py-10 sm:px-10 sm:py-12">
			<div class="flex flex-col items-center text-center">
				<img src={logo} alt="VandyGuessr logo" class="mb-3 h-16 w-16" />
				<h1 class="font-heading text-3xl font-bold text-charcoal sm:text-4xl">
					VandyGuessr
				</h1>
				<p class="mt-1 text-lg text-charcoal/60">
					The Vanderbilt campus guessing game
				</p>
				<p class="mt-4 mb-8 text-sm leading-relaxed text-charcoal/70">
					Think you know campus? Drop into a 360° photo, pin your guess on
					the map, and compete with fellow Commodores.
				</p>

				{#if $authError}
					<div class="mb-6 w-full rounded-xl border border-clay/20 bg-clay/5 px-4 py-3">
						<p class="text-sm text-clay">{$authError}</p>
						<button
							class="mt-2 text-xs font-medium text-charcoal/50 underline hover:text-charcoal/70"
							on:click={() => auth.clearError()}
						>
							Dismiss
						</button>
					</div>
				{/if}

				<button
					class="btn-3d flex w-full items-center justify-center gap-3 text-base"
					disabled={$isLoading}
					on:click={() => auth.login()}
				>
					<svg width="20" height="20" viewBox="0 0 21 21" fill="none" aria-hidden="true">
						<rect x="1" y="1" width="9" height="9" fill="#F25022" />
						<rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
						<rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
						<rect x="11" y="11" width="9" height="9" fill="#FFB900" />
					</svg>
					{$isLoading ? "Loading..." : "Log in with Vanderbilt"}
				</button>
			</div>
		</div>

		<p class="mt-6 text-center text-sm text-charcoal/40">
			Exclusively for Vanderbilt students
		</p>
	</div>
</div>
