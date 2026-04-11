<script lang="ts">
import CampusTour from "$lib/pages/CampusTour.svelte";
import DemoRedirect from "$lib/pages/DemoRedirect.svelte";
import Game from "$lib/pages/Game.svelte";
import GameHistory from "$lib/pages/GameHistory.svelte";
import GameSummary from "$lib/pages/GameSummary.svelte";
import Home from "$lib/pages/Home.svelte";
import Leaderboard from "$lib/pages/Leaderboard.svelte";
import Login from "$lib/pages/Login.svelte";
import MultiplayerGame from "$lib/pages/MultiplayerGame.svelte";
import MultiplayerJoin from "$lib/pages/MultiplayerJoin.svelte";
import MultiplayerLobby from "$lib/pages/MultiplayerLobby.svelte";
import ReviewSubmissions from "$lib/pages/ReviewSubmissions.svelte";
import TourLocation from "$lib/pages/TourLocation.svelte";
import Upload from "$lib/pages/Upload.svelte";
import { queryClient } from "$lib/shared/api/queryClient";
import { auth, isAuthenticated, isLoading } from "$lib/shared/auth/auth.store";
import { QueryClientProvider } from "@tanstack/svelte-query";
import { onMount } from "svelte";
import { Route, Router, navigate } from "svelte-routing";
import { Toaster } from "svelte-sonner";

const multiplayerEnabled = import.meta.env.VITE_FEATURE_MULTIPLAYER === "true";

onMount(() => {
	auth.initialize();
});

$: if (!$isLoading) {
	const path = window.location.pathname;
	const isPublicPath = path === "/login" || path === "/demo";
	if ($isAuthenticated) {
		if (path === "/login") {
			navigate("/", { replace: true });
		}
	} else if (!isPublicPath) {
		navigate("/login", { replace: true });
	}
}
</script>

<Toaster
  position="bottom-center"
  toastOptions={{
    unstyled: true,
    classes: {
      toast: "sonner-toast",
      default: "sonner-toast--default",
      warning: "sonner-toast--warning",
      error: "sonner-toast--error",
      success: "sonner-toast--success",
      title: "sonner-title",
      description: "sonner-description",
    },
  }}
/>

<QueryClientProvider client={queryClient}>
  <Router>
    <Route path="/" component={Home} />
    <Route path="/tour/:locationName" component={TourLocation} />
    <Route path="/tour" component={CampusTour} />
    <Route path="/history" component={GameHistory} />
    <Route path="/game/:id/summary" component={GameSummary} />
    <Route path="/game/:id" component={Game} />
    <Route path="/leaderboard" component={Leaderboard} />
    <Route path="/upload" component={Upload} />
    <Route path="/review/submissions" component={ReviewSubmissions} />
    <Route path="/login" component={Login} />
    <Route path="/demo" component={DemoRedirect} />
    {#if multiplayerEnabled}
      <Route path="/multiplayer/join/:code" component={MultiplayerJoin} />
      <Route path="/multiplayer/:id/lobby" component={MultiplayerLobby} />
      <Route path="/multiplayer/:id" component={MultiplayerGame} />
    {/if}
  </Router>
</QueryClientProvider>
