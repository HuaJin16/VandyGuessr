<script lang="ts">
export let code: string;

let copied = false;

async function copyCode() {
	await navigator.clipboard.writeText(code);
	copied = true;
	setTimeout(() => {
		copied = false;
	}, 2000);
}
</script>

<div class="glass-card invite-card">
	<p class="label">Invite Code</p>
	<button class="code" on:click={copyCode} title="Click to copy">
		{code}
	</button>
	<p class="hint">{copied ? "Copied!" : "Click to copy"}</p>
</div>

<style>
	.invite-card {
		padding: 24px;
		text-align: center;
		max-width: 320px;
		margin: 0 auto;
	}
	.label {
		font-family: "Rubik", sans-serif;
		font-size: 0.875rem;
		font-weight: 500;
		color: #636363;
		margin-bottom: 8px;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.code {
		font-family: "Rubik Mono One", monospace;
		font-size: 2.5rem;
		letter-spacing: 0.15em;
		color: #18181b;
		background: none;
		border: none;
		cursor: pointer;
		padding: 8px 16px;
		border-radius: 12px;
		transition: background 0.15s;
	}
	.code:hover {
		background: rgba(0, 0, 0, 0.05);
	}
	.hint {
		font-size: 0.75rem;
		color: #9a9a9a;
		margin-top: 4px;
	}
</style>
