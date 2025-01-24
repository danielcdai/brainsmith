<script lang="ts">
	import Button from '../ui/button/button.svelte';

	let uploadDocInputElement;
	let files;
</script>

<div class="items-center justify-between">
	<div
		role="button"
		aria-label="Choose a file"
		class="item-center flex justify-center rounded-lg border p-4 dark:border-white"
		tabindex="0"
	>
		<input
			bind:this={uploadDocInputElement}
			bind:files
			accept=".txt,.pdf,.docx"
			multiple
			type="file"
			tabindex="-1"
			style="display: none;"
		/>
		<div class="mr-auto flex items-center">
			<!--
                icon
            -->
			<div class="flex flex-col">
				<span class="mb-1">Drag and drop file here</span>
				<small class="text-xs leading-tight text-opacity-60"
					>Limit 200MB per file • TXT, PDF, DOCX</small
				>
			</div>
		</div>
		<div class="flex items-center">
			<Button
				onclick={() => {
					uploadDocInputElement.click();
				}}>Browse file</Button
			>
		</div>
	</div>
</div>
