<script lang="ts">
import Button from "$lib/shared/ui/Button.svelte";
import { toast } from "svelte-sonner";

export let code: string;

let copied = false;
let copiedLink = false;

function getErrorMessage(error: unknown): string {
	if (error instanceof Error && error.message) {
		return error.message;
	}
	return "Clipboard is not available on this device";
}

async function copyText(value: string) {
	if (navigator.clipboard?.writeText) {
		await navigator.clipboard.writeText(value);
		return;
	}

	const textArea = document.createElement("textarea");
	textArea.value = value;
	textArea.setAttribute("readonly", "");
	textArea.style.position = "fixed";
	textArea.style.opacity = "0";
	document.body.append(textArea);
	textArea.select();

	const isCopied = document.execCommand("copy");
	textArea.remove();

	if (!isCopied) {
		throw new Error("Clipboard is not available on this device");
	}
}

async function copyCode() {
	try {
		await copyText(code);
		copied = true;
		setTimeout(() => {
			copied = false;
		}, 2000);
	} catch (error) {
		toast.error(getErrorMessage(error));
	}
}

async function copyLink() {
	try {
		const link = `${window.location.origin}/multiplayer/join/${code}`;
		await copyText(link);
		copiedLink = true;
		setTimeout(() => {
			copiedLink = false;
		}, 2000);
	} catch (error) {
		toast.error(getErrorMessage(error));
	}
}

$: chars = code.split("");
</script>

<section class="invite-card">
	<div class="invite-card__copy">
		<p class="section-label">Invite code</p>
		<h2>Bring in the rest of the lobby</h2>
		<p>Share the code or copy the direct join link for a faster handoff.</p>
	</div>

	<div class="invite-card__code" aria-label={`Invite code ${code}`}>
		{#each chars as char}
			<span class="code-char">{char}</span>
		{/each}
	</div>

	<div class="invite-card__actions">
		<Button variant="outline" type="button" on:click={copyCode}>
			{copied ? "Copied code" : "Copy Code"}
		</Button>
		<Button variant="secondary" type="button" on:click={copyLink}>
			{copiedLink ? "Copied link" : "Copy Link"}
		</Button>
	</div>
</section>

<style>
	.invite-card {
		display: grid;
		gap: 18px;
	}

	.invite-card__copy {
		display: grid;
		gap: 8px;
	}

	.section-label,
	h2,
	.invite-card__copy p:last-child {
		margin: 0;
	}

	.section-label {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	h2 {
		font-size: 24px;
		font-weight: 800;
		line-height: 1.1;
		letter-spacing: -0.03em;
	}

	.invite-card__copy p:last-child {
		font-size: 14px;
		line-height: 1.55;
		color: var(--muted);
	}

	.invite-card__code {
		display: flex;
		justify-content: center;
		gap: 8px;
		flex-wrap: wrap;
	}

	.code-char {
		width: 48px;
		height: 56px;
		display: grid;
		place-items: center;
		border: 1px solid color-mix(in srgb, var(--brand) 30%, var(--line));
		border-radius: var(--radius-md);
		background: var(--surface-subtle);
		font-family: "IBM Plex Mono", monospace;
		font-size: 24px;
		font-weight: 700;
		color: var(--ink);
	}

	.invite-card__actions {
		display: flex;
		flex-wrap: wrap;
		gap: 10px;
	}

	@media (max-width: 420px) {
		.code-char {
			width: 42px;
			height: 50px;
			font-size: 20px;
		}
	}
</style>
