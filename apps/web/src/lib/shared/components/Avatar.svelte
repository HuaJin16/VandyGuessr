<script lang="ts">
import { getInitials } from "$lib/shared/utils/initials";

export let name: string;
export let size: "sm" | "md" | "lg" = "md";
export let color: string | undefined = undefined;

$: initials = getInitials(name);

const sizes: Record<string, string> = {
	sm: "w-8 h-8 text-xs",
	md: "w-[44px] h-[44px] text-sm",
	lg: "w-14 h-14 text-lg",
};
</script>

<div
	class="flex-shrink-0 rounded-full font-semibold text-white flex items-center justify-center {sizes[size]}"
	style="background: {color ?? 'var(--brand)'};"
>
	{initials}
</div>
