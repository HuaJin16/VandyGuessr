/**
 * Route definitions for svelte-spa-router.
 */

import Home from "$lib/pages/Home.svelte";
import Login from "$lib/pages/Login.svelte";

export const routes = {
	"/": Home,
	"/login": Login,
};
