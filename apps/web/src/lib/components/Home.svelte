<script lang="ts">
import { auth, currentUser } from "../stores/auth";
</script>

<div>
  {#if $currentUser}
    <h1>Welcome, {$currentUser.name}!</h1>
    <p>Email: {$currentUser.email}</p>
    <p>Username: {$currentUser.username}</p>
    <button on:click={() => auth.logout()}>Logout</button>
  {/if}
</div>
