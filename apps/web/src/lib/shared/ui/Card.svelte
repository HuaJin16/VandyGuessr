<script lang="ts">
import { cn } from "$lib/shared/utils";

let className = "";
export { className as class };
</script>

<div class={cn("rounded-lg border border-neutral-200 bg-white shadow-sm", className)} {...$$restProps}>
	<slot />
</div>
