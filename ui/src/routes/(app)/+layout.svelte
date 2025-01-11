<script lang="ts">
	import { onMount } from 'svelte';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
    import Header from '$lib/components/layout/Header.svelte';

	onMount(() => {
		document.documentElement.setAttribute('data-theme', 'dark');
	});
</script>

<div class=" block h-screen ">
    <div class="flex w-full h-16 bg-gray-800 items-center justify-between">
        <Header />
    </div>
	<div class="flex flex-row w-full h-full">
        <Sidebar />
        <slot></slot>
    </div>
	
</div>
