<script lang="ts">
import LeaderboardBoard from "$lib/domains/leaderboard/components/LeaderboardBoard.svelte";
import LeaderboardFilters from "$lib/domains/leaderboard/components/LeaderboardFilters.svelte";
import { leaderboardQueries } from "$lib/domains/leaderboard/queries/leaderboard.queries";
import { createLeaderboardViewStore } from "$lib/domains/leaderboard/stores/leaderboardView.store";
import { userQueries } from "$lib/domains/users/queries/users.queries";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import { createQuery } from "@tanstack/svelte-query";

const viewStore = createLeaderboardViewStore();

$: view = $viewStore;
$: user = createQuery({ ...userQueries.me(), enabled: $auth.isInitialized });
$: leaderboard = createQuery({
	...leaderboardQueries.leaderboard({
		timeframe: view.timeframe,
		mode: view.mode,
		limit: view.limit,
		offset: view.offset,
	}),
	enabled: $auth.isInitialized,
});

$: currentUserId = $user.data?.id;
$: currentUserName = $user.data?.name ?? "";
</script>

<div class="min-h-screen bg-terrain font-body">
	<Navbar activePage="leaderboard" />
	<LeaderboardBoard
		leaderboard={$leaderboard}
		{currentUserId}
		{currentUserName}
		onSetLimit={viewStore.setLimit}
	>
		<div slot="filters">
			<LeaderboardFilters
				timeframe={view.timeframe}
				mode={view.mode}
				onTimeframeChange={viewStore.setTimeframe}
				onModeChange={viewStore.setMode}
			/>
		</div>
	</LeaderboardBoard>
</div>
