<script lang="ts">
    import Tooltip from '../common/Tooltip.svelte';
    let sources = [];
</script>


<div class="w-1/5 border-r border-gray-700 p-5">
    <h3 class="text-lg font-semibold mb-4">Sources</h3>
    <button
      class="w-full bg-gray-800 hover:bg-gray-700 text-white py-2 px-4 rounded mb-4"
      on:click={() => sources.push('New Source')}
    >
      + Add Source
    </button>
    <ul class="space-y-2">
      {#each sources as source, i}
        <li class="bg-gray-800 p-2 rounded">📄 {source} (Source {i + 1})</li>
      {/each}
    </ul>
  </div>