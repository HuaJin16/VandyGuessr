<script lang="ts">
import { queryClient } from "$lib/shared/api/queryClient";
import { auth, isAuthenticated, isLoading } from "$lib/shared/auth/auth.store";
import { QueryClientProvider } from "@tanstack/svelte-query";
import { onMount } from "svelte";
import Router, { replace } from "svelte-spa-router";
import { routes } from "./routes";

onMount(() => {
	auth.initialize();
});

// Reactive navigation based on auth state
$: if (!$isLoading) {
	if ($isAuthenticated) {
		replace("/");
	} else {
		replace("/login");
	}
}
</script>

<QueryClientProvider client={queryClient}>
  {#if $isLoading}
    <main>
      <p>Loading...</p>
    </main>
  {:else}
    <Router {routes} />
  {/if}
</QueryClientProvider>
