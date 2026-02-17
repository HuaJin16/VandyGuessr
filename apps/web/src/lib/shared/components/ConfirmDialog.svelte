<script lang="ts">
export let open: boolean;
export let title: string;
export let description = "";
export let variant: "warning" | "success" | "info" = "warning";
export let confirmLabel = "Confirm";
export let cancelLabel = "Cancel";
export let onConfirm: () => void;
export let onCancel: () => void;

const iconColors = {
	warning: "icon-circle--warning",
	success: "icon-circle--success",
	info: "icon-circle--info",
};

const confirmStyles = {
	warning: "btn-confirm--destructive",
	success: "btn-confirm--success",
	info: "btn-confirm--info",
};

function handleKeydown(e: KeyboardEvent) {
	if (e.key === "Escape") onCancel();
}
</script>

<svelte:window on:keydown={open ? handleKeydown : undefined} />

{#if open}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div class="backdrop" on:click={onCancel}>
		<div
			class="dialog"
			on:click|stopPropagation
			role="dialog"
			aria-modal="true"
			aria-labelledby="confirm-dialog-title"
		>
			<div class="icon-circle {iconColors[variant]}">
				{#if variant === "warning"}
					<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#D95D39" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
						<line x1="12" y1="9" x2="12" y2="13" />
						<line x1="12" y1="17" x2="12.01" y2="17" />
					</svg>
				{:else if variant === "success"}
					<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2E933C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
						<polyline points="22 4 12 14.01 9 11.01" />
					</svg>
				{:else}
					<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#F4C430" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<circle cx="12" cy="12" r="10" />
						<line x1="12" y1="16" x2="12" y2="12" />
						<line x1="12" y1="8" x2="12.01" y2="8" />
					</svg>
				{/if}
			</div>

			<h2 id="confirm-dialog-title" class="font-heading text-2xl font-bold text-charcoal text-center">
				{title}
			</h2>

			{#if description}
				<p class="text-charcoal/60 text-center text-sm mt-2">{description}</p>
			{/if}

			<div class="dialog-content">
				<slot />
			</div>

			<div class="actions">
				<button class="btn-cancel" on:click={onCancel}>{cancelLabel}</button>
				<button class="btn-confirm {confirmStyles[variant]}" on:click={onConfirm}>
					{confirmLabel}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.backdrop {
		position: fixed;
		inset: 0;
		z-index: 100;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(4px);
	}

	.dialog {
		width: 100%;
		max-width: 28rem;
		margin: 0 16px;
		padding: 24px;
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(24px);
		border-radius: 16px;
		border: 1px solid rgba(255, 255, 255, 0.5);
		box-shadow: 6px 6px 0px 0px rgba(0, 0, 0, 0.15);
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	@media (min-width: 640px) {
		.dialog {
			padding: 32px;
		}
	}

	.icon-circle {
		width: 56px;
		height: 56px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 16px;
	}

	.icon-circle--warning {
		background: rgba(217, 93, 57, 0.1);
	}

	.icon-circle--success {
		background: rgba(46, 147, 60, 0.1);
	}

	.icon-circle--info {
		background: rgba(244, 196, 48, 0.1);
	}

	.dialog-content {
		width: 100%;
	}

	.dialog-content:empty {
		display: none;
	}

	.actions {
		width: 100%;
		margin-top: 24px;
		display: flex;
		gap: 12px;
	}

	.btn-cancel {
		flex: 1;
		padding: 12px;
		font-size: 14px;
		font-weight: 600;
		color: #18181b;
		background: rgba(255, 255, 255, 0.8);
		border: 2px solid rgba(24, 24, 27, 0.2);
		border-radius: 12px;
		cursor: pointer;
		transition: background 0.15s;
	}

	.btn-cancel:hover {
		background: rgba(24, 24, 27, 0.05);
	}

	.btn-confirm {
		flex: 1;
		padding: 12px;
		font-size: 14px;
		font-weight: 600;
		color: white;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		box-shadow: 4px 4px 0px 0px rgba(0, 0, 0, 0.1);
		transition: background 0.15s;
	}

	.btn-confirm--destructive {
		background: #d95d39;
	}

	.btn-confirm--destructive:hover {
		background: #c14e2e;
	}

	.btn-confirm--success {
		background: #2e933c;
	}

	.btn-confirm--success:hover {
		background: #236e2d;
	}

	.btn-confirm--info {
		background: #f4c430;
		color: #18181b;
	}

	.btn-confirm--info:hover {
		background: #ddb12a;
	}
</style>
