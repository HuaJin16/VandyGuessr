<script lang="ts">
export let open: boolean;
export let title: string;
export let description = "";
export let variant: "warning" | "success" | "info" = "warning";
export let confirmLabel = "Confirm";
export let cancelLabel = "Cancel";
export let onConfirm: () => void;
export let onCancel: () => void;

const confirmBg: Record<string, string> = {
	warning: "var(--danger)",
	success: "var(--brand)",
	info: "var(--gold)",
};

const confirmHover: Record<string, string> = {
	warning: "var(--danger-dark)",
	success: "var(--brand-dark)",
	info: "var(--gold-dark)",
};

const confirmColor: Record<string, string> = {
	warning: "#fff",
	success: "#fff",
	info: "var(--ink)",
};

const iconBg: Record<string, string> = {
	warning: "var(--danger-light)",
	success: "var(--brand-light)",
	info: "var(--gold-light)",
};

function handleKeydown(e: KeyboardEvent) {
	if (e.key === "Escape") onCancel();
}
</script>

<svelte:window on:keydown={open ? handleKeydown : undefined} />

{#if open}
	<div class="backdrop">
		<button class="backdrop-hit" type="button" aria-label="Close dialog" on:click={onCancel} />
		<div
			class="dialog"
			role="dialog"
			aria-modal="true"
			aria-labelledby="confirm-dialog-title"
		>
			<div class="icon-circle" style="background: {iconBg[variant]};">
				{#if variant === "warning"}
					<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
						<line x1="12" y1="9" x2="12" y2="13" />
						<line x1="12" y1="17" x2="12.01" y2="17" />
					</svg>
				{:else if variant === "success"}
					<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
						<polyline points="22 4 12 14.01 9 11.01" />
					</svg>
				{:else}
					<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<circle cx="12" cy="12" r="10" />
						<line x1="12" y1="16" x2="12" y2="12" />
						<line x1="12" y1="8" x2="12.01" y2="8" />
					</svg>
				{/if}
			</div>

			<h2 id="confirm-dialog-title" class="text-2xl font-bold text-ink text-center">
				{title}
			</h2>

			{#if description}
				<p class="text-muted text-center text-sm mt-2">{description}</p>
			{/if}

			<div class="dialog-content">
				<slot />
			</div>

			<div class="actions">
				<button class="btn-cancel" on:click={onCancel}>{cancelLabel}</button>
				<button
					class="btn-confirm"
					style="background: {confirmBg[variant]}; color: {confirmColor[variant]};"
					on:click={onConfirm}
					on:mouseenter={(e) => { e.currentTarget.style.background = confirmHover[variant]; }}
					on:mouseleave={(e) => { e.currentTarget.style.background = confirmBg[variant]; }}
				>
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

	.backdrop-hit {
		position: absolute;
		inset: 0;
		border: none;
		background: transparent;
		cursor: default;
	}

	.dialog {
		position: relative;
		width: 100%;
		max-width: 28rem;
		margin: 0 16px;
		padding: 24px;
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-lg);
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
		color: var(--ink);
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: border-color var(--duration) var(--ease),
			background var(--duration) var(--ease);
	}

	.btn-cancel:hover {
		border-color: var(--line-strong);
		background: var(--canvas);
	}

	.btn-confirm {
		flex: 1;
		padding: 12px;
		font-size: 14px;
		font-weight: 700;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		box-shadow: var(--shadow-sm);
		transition: background var(--duration-fast) var(--ease);
	}
</style>
