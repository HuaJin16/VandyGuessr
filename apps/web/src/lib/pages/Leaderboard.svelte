<script lang="ts">
import LeaderboardBoard from "$lib/domains/leaderboard/components/LeaderboardBoard.svelte";
import LeaderboardFilters from "$lib/domains/leaderboard/components/LeaderboardFilters.svelte";
import { leaderboardQueries } from "$lib/domains/leaderboard/queries/leaderboard.queries";
import { createLeaderboardViewStore } from "$lib/domains/leaderboard/stores/leaderboardView.store";
import { userQueries } from "$lib/domains/users/queries/users.queries";
import { auth } from "$lib/shared/auth/auth.store";
import Navbar from "$lib/shared/components/Navbar.svelte";
import PageHeader from "$lib/shared/ui/PageHeader.svelte";
import PageShell from "$lib/shared/ui/PageShell.svelte";
import { createQuery } from "@tanstack/svelte-query";

const viewStore = createLeaderboardViewStore();

$: view = $viewStore;
$: isAuthenticated = $auth.currentUserOid !== null;

$: user = createQuery({
	...userQueries.me($auth.currentUserOid),
	enabled: isAuthenticated,
});

$: leaderboard = createQuery({
	...leaderboardQueries.leaderboard(
		{
			timeframe: view.timeframe,
			mode: view.mode,
			limit: view.limit,
			offset: view.offset,
		},
		$auth.currentUserOid,
	),
	enabled: isAuthenticated,
});

$: currentUserId = $user.data?.id;
$: currentUserName = $user.data?.name ?? "";
</script>

<div class="min-h-screen bg-canvas font-sans text-ink">
	<Navbar activePage="leaderboard" />

	<PageShell size="content">
		<PageHeader
			title="Leaderboard"
			split
		>
			<div slot="actions">
				<LeaderboardFilters
					timeframe={view.timeframe}
					mode={view.mode}
					onTimeframeChange={viewStore.setTimeframe}
					onModeChange={viewStore.setMode}
				/>
			</div>
		</PageHeader>

		<LeaderboardBoard
			leaderboard={$leaderboard}
			{currentUserId}
			{currentUserName}
			onSetLimit={viewStore.setLimit}
			offset={view.offset}
			onSetOffset={viewStore.setOffset}
		/>
	</PageShell>
</div>
