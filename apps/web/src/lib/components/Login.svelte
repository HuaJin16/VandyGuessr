<script lang="ts">
import { auth, authError, isLoading } from "../stores/auth";
</script>

<div>
  <h1>Welcome to VandyGuessr</h1>
  <p>A GeoGuessr-style game for Vanderbilt students</p>

  {#if $authError}
    <p style="color: red;">
      {$authError}
      <button on:click={() => auth.clearError()}>Dismiss</button>
    </p>
  {/if}

  <button on:click={() => auth.login()} disabled={$isLoading}>
    {$isLoading ? "Loading..." : "Log in with Vanderbilt"}
  </button>
</div>
