<script lang="ts">
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

	const copied = document.execCommand("copy");
	textArea.remove();

	if (!copied) {
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

<section class="card text-center">
	<p class="section-label">Invite Code</p>

	<div class="mt-3 flex justify-center gap-1.5 sm:gap-2">
		{#each chars as char}
			<span class="code-char">{char}</span>
		{/each}
	</div>

	<div class="actions mt-3.5">
		<button class="copy-btn" type="button" on:click={copyCode}>
			<svg
				class="h-3.5 w-3.5"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<rect x="9" y="9" width="13" height="13" rx="2" />
				<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
			</svg>
			{copied ? "Copied!" : "Copy Code"}
		</button>
		<button class="copy-btn" type="button" on:click={copyLink}>
			<svg
				class="h-3.5 w-3.5"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<path d="M10 13a5 5 0 0 0 7.54.54l2.92-2.92a5 5 0 0 0-7.07-7.07L11.7 5.24" />
				<path d="M14 11a5 5 0 0 0-7.54-.54l-2.92 2.92a5 5 0 1 0 7.07 7.07l1.69-1.69" />
			</svg>
			{copiedLink ? "Copied!" : "Copy Link"}
		</button>
	</div>
</section>

<style>
	.section-label {
		margin: 0;
		color: var(--muted);
		font-size: 11px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.code-char {
		width: 44px;
		height: 52px;
		border: 2px solid var(--mp);
		border-radius: var(--radius-sm);
		background: var(--surface);
		box-shadow: var(--shadow-sm);
		display: grid;
		place-items: center;
		font-family: "IBM Plex Mono", monospace;
		font-size: 24px;
		font-weight: 600;
		color: var(--ink);
		transition: transform 100ms var(--ease);
	}

	.code-char:hover {
		transform: translateY(-2px);
	}

	.actions {
		display: flex;
		justify-content: center;
		gap: 8px;
		flex-wrap: wrap;
	}

	.copy-btn {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		border: 1px solid var(--line);
		border-radius: var(--radius-sm);
		background: var(--surface);
		padding: 7px 14px;
		font-size: 13px;
		font-weight: 600;
		color: var(--muted);
		cursor: pointer;
		transition: all 120ms var(--ease);
	}

	.copy-btn:hover {
		border-color: var(--brand);
		color: var(--brand);
		background: var(--brand-light);
	}

	.copy-btn:focus-visible {
		outline: none;
		box-shadow: var(--ring);
	}

	@media (min-width: 700px) {
		.code-char {
			width: 48px;
			height: 56px;
			font-size: 26px;
		}
	}

	@media (max-width: 400px) {
		.code-char {
			width: 38px;
			height: 46px;
			font-size: 20px;
		}
	}
</style>
