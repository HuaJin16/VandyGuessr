<script lang="ts">
import Game from "$lib/pages/Game.svelte";
import GameSummary from "$lib/pages/GameSummary.svelte";
import Home from "$lib/pages/Home.svelte";
import Login from "$lib/pages/Login.svelte";
import { queryClient } from "$lib/shared/api/queryClient";
import { auth, isAuthenticated, isLoading } from "$lib/shared/auth/auth.store";
import { QueryClientProvider } from "@tanstack/svelte-query";
import { onMount } from "svelte";
import { Route, Router, navigate } from "svelte-routing";
import { Toaster } from "svelte-sonner";

onMount(() => {
	auth.initialize();
});

$: if (!$isLoading) {
	const path = window.location.pathname;
	if ($isAuthenticated) {
		if (path === "/login") {
			navigate("/", { replace: true });
		}
	} else {
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
    <Route path="/game/:id/summary" component={GameSummary} />
    <Route path="/game/:id" component={Game} />
    <Route path="/login" component={Login} />
  </Router>
</QueryClientProvider>
