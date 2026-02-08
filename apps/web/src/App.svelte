<script lang="ts">
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
	if ($isAuthenticated) {
		navigate("/", { replace: true });
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
    <Route path="/login" component={Login} />
  </Router>
</QueryClientProvider>
