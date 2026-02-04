<script lang="ts">
import { auth, authError, isLoading } from "$lib/shared/auth/auth.store";
</script>

<div class="login-page">
  <h1>Welcome to VandyGuessr</h1>
  <p>A GeoGuessr-style game for Vanderbilt students</p>

  {#if $authError}
    <p class="error">
      {$authError}
      <button on:click={() => auth.clearError()}>Dismiss</button>
    </p>
  {/if}

  <button on:click={() => auth.login()} disabled={$isLoading}>
    {$isLoading ? "Loading..." : "Log in with Vanderbilt"}
  </button>
</div>

<style>
  .login-page {
    padding: 2rem;
    text-align: center;
  }

  .error {
    color: red;
    margin-bottom: 1rem;
  }
</style>
