<script lang="ts">
import { userQueries } from "$lib/domains/users/queries/users.queries";
import { auth } from "$lib/shared/auth/auth.store";
import { createQuery } from "@tanstack/svelte-query";
import { History, LogOut, ShieldCheck, Trophy as TrophyIcon } from "lucide-svelte";
import logo from "../../../assets/logo.webp";

export let activePage: "home" | "leaderboard" | "history" | "review" | undefined = undefined;

$: me = createQuery({ ...userQueries.me(), enabled: $auth.isInitialized });
</script>

<header class="sticky top-0 z-50 border-b border-line bg-surface">
	<div class="mx-auto flex min-h-[48px] items-center justify-between gap-3 px-2 sm:min-h-[52px] sm:px-3" style="width: min(1180px, calc(100% - 32px));">
		<a href="/" class="flex items-center gap-2.5">
			<img src={logo} alt="VandyGuessr" class="h-[34px] w-[34px] rounded-md" />
			<span class="hidden text-lg font-extrabold text-ink sm:block">VandyGuessr</span>
		</a>

		<div class="flex items-center gap-2">
			{#if $me.data?.can_review_submissions}
				<a
					href="/review/submissions"
					class="flex items-center gap-1.5 rounded-sm border border-line px-2.5 py-[7px] text-[13px] font-semibold transition-all {activePage === 'review'
						? 'border-brand bg-brand-light text-brand'
						: 'bg-surface text-ink hover:border-brand hover:bg-brand-light hover:text-brand'}"
					style="transition-duration: var(--duration-fast); transition-timing-function: var(--ease);"
				>
					<ShieldCheck size={15} />
					<span class="hidden sm:inline">Review</span>
				</a>
			{/if}
			<a
				href="/history"
				class="flex items-center gap-1.5 rounded-sm border border-line px-2.5 py-[7px] text-[13px] font-semibold transition-all {activePage === 'history'
					? 'border-brand bg-brand-light text-brand'
					: 'bg-surface text-ink hover:border-brand hover:bg-brand-light hover:text-brand'}"
				style="transition-duration: var(--duration-fast); transition-timing-function: var(--ease);"
			>
				<History size={15} />
				<span class="hidden sm:inline">History</span>
			</a>
			<a
				href="/leaderboard"
				class="flex items-center gap-1.5 rounded-sm border border-line px-2.5 py-[7px] text-[13px] font-semibold transition-all {activePage === 'leaderboard'
					? 'border-brand bg-brand-light text-brand'
					: 'bg-surface text-ink hover:border-brand hover:bg-brand-light hover:text-brand'}"
				style="transition-duration: var(--duration-fast); transition-timing-function: var(--ease);"
			>
				<TrophyIcon size={15} />
				<span class="hidden sm:inline">Leaderboard</span>
			</a>
			<button
				class="flex items-center gap-1.5 rounded-sm border border-line bg-surface px-2.5 py-[7px] text-[13px] font-semibold text-ink transition-all hover:border-danger hover:bg-danger-light hover:text-danger"
				style="transition-duration: var(--duration-fast); transition-timing-function: var(--ease);"
				on:click={() => auth.logout()}
			>
				<LogOut size={15} />
				<span class="hidden sm:inline">Logout</span>
			</button>
		</div>
	</div>
</header>
