<script lang="ts">
import { onMount } from "svelte";
import Home from "./lib/components/Home.svelte";
import Login from "./lib/components/Login.svelte";
import { auth, isAuthenticated, isLoading } from "./lib/stores/auth";

onMount(() => {
	auth.initialize();
});
</script>

<main>
  {#if $isLoading}
    <p>Loading...</p>
  {:else if $isAuthenticated}
    <Home />
  {:else}
    <Login />
  {/if}
</main>
