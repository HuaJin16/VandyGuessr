<script lang="ts">
import { auth, authError, isLoading } from "$lib/shared/auth/auth.store";
import logo from "../../assets/logo.webp";
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
				Made exclusively for Vanderbilt students
			</p>

			<button
				class="btn-3d mt-3 flex w-full items-center justify-center gap-3 text-[15px]"
				disabled={$isLoading}
				on:click={() => auth.login()}
			>
				<svg width="20" height="20" viewBox="0 0 21 21" fill="none" aria-hidden="true">
					<rect x="1" y="1" width="9" height="9" fill="#F25022" />
					<rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
					<rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
					<rect x="11" y="11" width="9" height="9" fill="#FFB900" />
				</svg>
				{$isLoading ? "Loading..." : "Continue with Vanderbilt"}
			</button>
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
