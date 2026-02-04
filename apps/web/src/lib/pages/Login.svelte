<script lang="ts">
import { auth, authError, isLoading } from "$lib/shared/auth/auth.store";
import { Button, Card, CardContent } from "$lib/shared/ui";
</script>

<div class="flex min-h-screen items-center justify-center p-4">
	<Card class="w-full max-w-md">
		<CardContent class="text-center">
			<h1 class="mb-2 text-2xl font-bold">Welcome to VandyGuessr</h1>
			<p class="mb-6 text-neutral-600">A GeoGuessr-style game for Vanderbilt students</p>

			{#if $authError}
				<div class="mb-4 rounded-md bg-red-50 p-3 text-red-700">
					<p>{$authError}</p>
					<Button variant="ghost" size="sm" class="mt-2" on:click={() => auth.clearError()}>
						Dismiss
					</Button>
				</div>
			{/if}

			<Button on:click={() => auth.login()} disabled={$isLoading} class="w-full">
				{$isLoading ? "Loading..." : "Log in with Vanderbilt"}
			</Button>
		</CardContent>
	</Card>
</div>
