<script lang="ts">
import { auth } from "$lib/shared/auth/auth.store";
import type { User } from "../types";

export let user: User;
</script>

<div class="user-profile">
  <h1>Welcome, {user.name}!</h1>
  <p>Email: {user.email}</p>
  <p>Username: @{user.username}</p>
  <button on:click={() => auth.logout()}>Logout</button>
</div>

<style>
  .user-profile {
    padding: 1rem;
  }
</style>
