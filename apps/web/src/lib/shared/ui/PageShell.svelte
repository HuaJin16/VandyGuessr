<script lang="ts">
import { cn } from "$lib/shared/utils";

export let size: "narrow" | "content" | "wide" = "content";
export let flushTop = false;

let className = "";
export { className as class };
</script>

<div
	class={cn(
		"page-shell",
		size === "narrow" && "page-shell--narrow",
		size === "content" && "page-shell--content",
		size === "wide" && "page-shell--wide",
		flushTop && "page-shell--flush",
		className,
	)}
	{...$$restProps}
>
	<slot />
</div>
