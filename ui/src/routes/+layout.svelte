<script lang="ts">
import '../app.css';
import { onMount, tick } from 'svelte';
import { goto } from '$app/navigation';
import {  getUser } from '$lib/api/auth/index.js';

let user = null;

async function getUserInfo() {
        try {
			if (localStorage.getItem('accessToken') === null) {
				goto('/auth');
			} else {
				const response = await getUser(localStorage.getItem('accessToken')!);
				if (response.ok) {
					const data = await response.json();
					user = data.user;
				} else {
					goto('/auth');
				}
			}
        
        } catch (error) {
            console.error("Failed to fetch user:", error);
			goto('/auth');
        }
    }

let loaded = false;
onMount(async () => {

	getUserInfo();
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
