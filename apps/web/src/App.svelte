<script lang="ts">
import Home from "$lib/pages/Home.svelte";
import Login from "$lib/pages/Login.svelte";
import { queryClient } from "$lib/shared/api/queryClient";
import { auth, isAuthenticated, isLoading } from "$lib/shared/auth/auth.store";
import { QueryClientProvider } from "@tanstack/svelte-query";
import { onMount } from "svelte";
import { Route, Router, navigate } from "svelte-routing";

onMount(() => {
	auth.initialize();
});

// Reactive navigation based on auth state
$: if (!$isLoading) {
	if ($isAuthenticated) {
		navigate("/", { replace: true });
	} else {
		navigate("/login", { replace: true });
	}
}
</script>

<QueryClientProvider client={queryClient}>
  {#if $isLoading}
    <main>
      <p>Loading...</p>
    </main>
  {:else}
    <Router>
      <Route path="/" component={Home} />
      <Route path="/login" component={Login} />
    </Router>
  {/if}
</QueryClientProvider>
