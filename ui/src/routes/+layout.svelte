<script lang="ts">
import '../app.css';
import { onMount, tick } from 'svelte';
import { goto } from '$app/navigation';

let loaded = false;
onMount(async () => {
	// goto('/');
	if (localStorage.token) {
		goto('/');
	} else {
		goto('/auth');
	}
	await tick();
	loaded = true;
});


  

</script>

<svelte:head>
	<title>Blacksmith</title>
	<link id="theme-style" rel="stylesheet" type="text/css" href="/smui.css" />
</svelte:head>

{#if loaded}
	<slot />
{/if}
