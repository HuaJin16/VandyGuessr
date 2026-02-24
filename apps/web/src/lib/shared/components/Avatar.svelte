<script lang="ts">
import { getInitials } from "$lib/shared/utils/initials";

export let name: string;
export let size: "sm" | "md" | "lg" = "md";

$: initials = getInitials(name);

const sizes = {
	sm: "w-8 h-8 text-xs",
	md: "w-10 h-10 text-sm",
	lg: "w-14 h-14 text-lg",
};
</script>

<div
	class="avatar-initials flex-shrink-0 rounded-full font-heading font-bold text-white flex items-center justify-center shadow-hard {sizes[size]}"
>
	{initials}
</div>

<style>
	.avatar-initials {
		background: linear-gradient(135deg, #2e933c 0%, #236e2d 100%);
	}
</style>
