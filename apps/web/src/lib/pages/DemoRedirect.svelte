<script lang="ts">
import { onMount } from "svelte";

const demoUrl = "https://youtu.be/bLWJlXQdtcE";

onMount(() => {
	window.location.replace(demoUrl);
});
</script>
