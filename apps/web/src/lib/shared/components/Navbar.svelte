<script lang="ts">
import { auth } from "$lib/shared/auth/auth.store";
import { LogOut, Trophy as TrophyIcon } from "lucide-svelte";
import { navigate } from "svelte-routing";
import logo from "../../../assets/logo.webp";

export let activePage: "home" | "leaderboard" | undefined = undefined;
</script>

<header class="sticky top-0 z-50 border-b border-gray-100 bg-white">
	<div class="mx-auto flex max-w-4xl items-center justify-between px-4 py-3 sm:px-6 sm:py-4">
		<button
			type="button"
			class="flex items-center gap-2 sm:gap-3"
			on:click={() => navigate("/")}
		>
			<img src={logo} alt="VandyGuessr" class="h-9 w-9 sm:h-10 sm:w-10" />
			<span class="hidden font-heading text-lg font-bold text-charcoal sm:block">
				VandyGuessr
			</span>
		</button>

		<div class="flex items-center gap-1 sm:gap-2">
			<button
				type="button"
				class="flex items-center gap-1.5 rounded-lg p-2 text-xs font-medium transition-colors sm:text-sm {activePage === 'leaderboard'
					? 'text-jungle'
					: 'text-charcoal/60 hover:bg-charcoal/5 hover:text-jungle'}"
				on:click={() => navigate("/leaderboard")}
			>
				<TrophyIcon size={18} />
				<span class="hidden sm:inline">Leaderboard</span>
			</button>
			<button
				class="flex items-center gap-1.5 rounded-lg p-2 text-xs font-medium text-charcoal/50 transition-colors hover:bg-charcoal/5 hover:text-clay sm:text-sm"
				on:click={() => auth.logout()}
			>
				<LogOut size={18} />
				<span class="hidden sm:inline">Logout</span>
			</button>
		</div>
	</div>
</header>
