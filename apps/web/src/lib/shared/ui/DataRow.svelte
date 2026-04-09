<script lang="ts">
import { cn } from "$lib/shared/utils";

let className = "";
export { className as class };
</script>

<div class={cn("data-row", className)} {...$$restProps}>
	<slot />
</div>
