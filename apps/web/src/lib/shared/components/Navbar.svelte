<script lang="ts">
import { leaderboardQueries } from "$lib/domains/leaderboard/queries/leaderboard.queries";
import { userQueries } from "$lib/domains/users/queries/users.queries";
import { auth } from "$lib/shared/auth/auth.store";
import Avatar from "$lib/shared/components/Avatar.svelte";
import { createQuery } from "@tanstack/svelte-query";
import { ChevronDown, LogOut } from "lucide-svelte";
import { navigate } from "svelte-routing";
import logoMark from "../../../assets/VandyGuessr_Favicon.png";
import logoLockup from "../../../assets/VandyGuessr_Logo.png";

export let activePage:
	| "home"
	| "leaderboard"
	| "history"
	| "review"
	| "upload"
	| "tour"
	| undefined = undefined;

let dropdownOpen = false;
let triggerEl: HTMLButtonElement;

$: me = createQuery({
	...userQueries.me($auth.currentUserOid),
	enabled: $auth.currentUserOid !== null,
});

$: stats = createQuery({
	...leaderboardQueries.leaderboard(
		{ timeframe: "alltime", mode: "all", limit: 1, offset: 0 },
		$auth.currentUserOid,
	),
	enabled: $auth.currentUserOid !== null,
});

$: userStats = $stats.data?.userEntry ?? null;

function go(path: string) {
	navigate(path);
}

function toggleDropdown() {
	dropdownOpen = !dropdownOpen;
}

function closeDropdown() {
	dropdownOpen = false;
}

function handleWindowClick(e: MouseEvent) {
	if (!dropdownOpen) return;
	if (triggerEl?.contains(e.target as Node)) return;
	closeDropdown();
}

function handleKeydown(e: KeyboardEvent) {
	if (e.key === "Escape" && dropdownOpen) {
		closeDropdown();
		triggerEl?.focus();
	}
}

function handleLogout() {
	closeDropdown();
	auth.logout();
}

const links = [
	{ page: "home" as const, label: "Home", path: "/" },
	{ page: "leaderboard" as const, label: "Leaderboard", path: "/leaderboard" },
	{ page: "tour" as const, label: "Tour", path: "/tour" },
	{ page: "history" as const, label: "History", path: "/history" },
	{ page: "upload" as const, label: "Upload", path: "/upload" },
] as const;
</script>

<svelte:window on:click={handleWindowClick} on:keydown={handleKeydown} />

<header class="nav">
	<div class="nav-inner">
		<a href="/" class="nav-brand" aria-label="VandyGuessr home" on:click|preventDefault={() => go("/")}>
			<img src={logoMark} alt="" class="nav-logo-mark" />
			<img src={logoLockup} alt="" class="nav-logo-lockup" />
		</a>

		<nav class="nav-links" aria-label="Primary">
			{#each links as link}
				<a
					href={link.path}
					class="nav-link"
					class:nav-link--active={activePage === link.page}
					on:click|preventDefault={() => go(link.path)}
				>
					{link.label}
				</a>
			{/each}
			{#if $me.data?.can_review_submissions}
				<a
					href="/review/submissions"
					class="nav-link"
					class:nav-link--active={activePage === "review"}
					on:click|preventDefault={() => go("/review/submissions")}
				>
					Review
				</a>
			{/if}
		</nav>

		<div class="nav-right">
			{#if $me.data}
				<button
					class="nav-trigger"
					bind:this={triggerEl}
					on:click|stopPropagation={toggleDropdown}
					aria-expanded={dropdownOpen}
					aria-haspopup="true"
				>
					<Avatar name={$me.data.name} size="sm" />
					<span class="nav-trigger-name">{$me.data.name}</span>
					<ChevronDown size={14} class="nav-trigger-chevron {dropdownOpen ? 'rotated' : ''}" />
				</button>

				{#if dropdownOpen}
					<div class="dropdown" role="menu">
						<div class="dropdown-header">
							<p class="dropdown-name">{$me.data.name}</p>
						</div>

						<div class="dropdown-stats">
							<div class="dropdown-stat">
								<span class="dropdown-stat-label">Rank</span>
								<span class="dropdown-stat-value">{userStats?.rank ? `#${userStats.rank}` : "-"}</span>
							</div>
						<div class="dropdown-stat">
							<span class="dropdown-stat-label">Avg</span>
							<span class="dropdown-stat-value">{userStats?.avgScore ? Math.round(userStats.avgScore).toLocaleString() : "-"}</span>
						</div>
							<div class="dropdown-stat">
								<span class="dropdown-stat-label">Games</span>
								<span class="dropdown-stat-value">{(userStats?.gamesPlayed ?? 0).toLocaleString()}</span>
							</div>
						</div>

						<div class="dropdown-divider" />

						<button class="dropdown-item dropdown-item--danger" role="menuitem" on:click={handleLogout}>
							<LogOut size={15} />
							Log out
						</button>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</header>

<style>
	.nav {
		position: sticky;
		top: 0;
		z-index: 50;
		background: var(--surface);
		border-bottom: 1px solid var(--line);
	}

	.nav-inner {
		width: min(var(--page-wide), calc(100% - 32px));
		margin: 0 auto;
		height: 56px;
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.nav-brand {
		display: flex;
		align-items: center;
		gap: 8px;
		color: inherit;
		text-decoration: none;
		flex-shrink: 0;
	}

	.nav-logo-mark {
		width: 32px;
		height: 32px;
		display: block;
		object-fit: contain;
	}

	.nav-logo-lockup {
		display: none;
		width: 152px;
		height: 32px;
		object-fit: cover;
		object-position: center;
	}

	.nav-links {
		display: flex;
		align-items: center;
		gap: 2px;
		margin-left: 16px;
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
		mask-image: linear-gradient(to right, black calc(100% - 24px), transparent);
		-webkit-mask-image: linear-gradient(to right, black calc(100% - 24px), transparent);
	}

	.nav-link {
		padding: 8px 12px;
		border-radius: var(--radius-sm);
		color: var(--muted);
		text-decoration: none;
		font-size: 14px;
		font-weight: 500;
		white-space: nowrap;
		transition: color var(--duration-fast) var(--ease),
			background var(--duration-fast) var(--ease);
	}

	.nav-link:hover {
		color: var(--ink);
		background: var(--surface-strong);
	}

	.nav-link--active {
		color: var(--ink);
		font-weight: 600;
		background: var(--surface-strong);
	}

	.nav-right {
		position: relative;
		display: flex;
		align-items: center;
		margin-left: auto;
		flex-shrink: 0;
	}

	/* Avatar trigger */
	.nav-trigger {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 4px;
		border-radius: var(--radius-sm);
		border: none;
		background: transparent;
		cursor: pointer;
		transition: background var(--duration-fast) var(--ease);
	}

	.nav-trigger:hover {
		background: var(--surface-strong);
	}

	.nav-trigger[aria-expanded="true"] {
		background: var(--surface-strong);
	}

	.nav-trigger-name {
		display: none;
		font-size: 14px;
		font-weight: 500;
		color: var(--ink);
	}

	:global(.nav-trigger-chevron) {
		display: none !important;
		color: var(--muted);
		transition: transform var(--duration) var(--ease);
	}

	:global(.nav-trigger-chevron.rotated) {
		transform: rotate(180deg);
	}

	.nav-trigger:focus-visible,
	.nav-link:focus-visible,
	.nav-brand:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	/* Dropdown panel */
	.dropdown {
		position: absolute;
		top: calc(100% + 8px);
		right: 0;
		width: 240px;
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-lg);
		z-index: 60;
		animation: dropdownIn var(--duration) var(--ease);
	}

	@keyframes dropdownIn {
		from {
			opacity: 0;
			transform: translateY(-4px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.dropdown-header {
		padding: 14px 16px 0;
	}

	.dropdown-name {
		margin: 0;
		font-size: 14px;
		font-weight: 600;
		color: var(--ink);
	}

	.dropdown-stats {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 4px;
		padding: 12px 16px;
	}

	.dropdown-stat {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.dropdown-stat-label {
		font-size: 11px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--muted);
	}

	.dropdown-stat-value {
		font-family: "IBM Plex Mono", monospace;
		font-size: 13px;
		font-weight: 600;
		color: var(--ink);
	}

	.dropdown-divider {
		height: 1px;
		background: var(--line);
		margin: 0 12px;
	}

	.dropdown-item {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
		padding: 10px 16px;
		border: none;
		border-radius: 0 0 var(--radius-md) var(--radius-md);
		background: transparent;
		font-size: 14px;
		font-weight: 500;
		cursor: pointer;
		transition: background var(--duration-fast) var(--ease);
	}

	.dropdown-item:hover {
		background: var(--surface-subtle);
	}

	.dropdown-item:focus-visible {
		outline: none;
		box-shadow: inset var(--ring);
	}

	.dropdown-item--danger {
		color: var(--danger);
	}

	.dropdown-item--danger:hover {
		background: var(--danger-light);
	}

	@media (min-width: 768px) {
		.nav-logo-mark {
			display: none;
		}

		.nav-logo-lockup {
			display: block;
		}

		.nav-trigger-name {
			display: block;
		}

		:global(.nav-trigger-chevron) {
			display: block !important;
		}

		.nav-trigger {
			padding: 4px 8px 4px 4px;
		}

		.nav-links {
			margin-left: 24px;
			mask-image: none;
			-webkit-mask-image: none;
		}
	}
</style>
