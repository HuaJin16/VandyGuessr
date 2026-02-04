<script lang="ts">
import UserProfile from "$lib/domains/users/components/UserProfile.svelte";
import { userQueries } from "$lib/domains/users/queries/users.queries";
import { createQuery } from "@tanstack/svelte-query";

const user = createQuery(userQueries.me());
</script>

<div class="home-page">
  {#if $user.isLoading}
    <p>Loading...</p>
  {:else if $user.isError}
    <div class="error">
      <p>Error loading profile: {$user.error?.message}</p>
      <button on:click={() => $user.refetch()}>Retry</button>
    </div>
  {:else if $user.data}
    <UserProfile user={$user.data} />
  {/if}
</div>

<style>
  .home-page {
    padding: 2rem;
  }

  .error {
    color: red;
  }
</style>
