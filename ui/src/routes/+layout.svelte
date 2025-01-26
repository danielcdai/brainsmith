<script lang="ts">
import '../app.css';
import { onMount, tick } from 'svelte';
import { goto } from '$lib/utils.js';
import {  getUser } from '$lib/api/auth/index.js';
import { ModeWatcher } from "mode-watcher";

let user = null;

async function getUserInfo() {
        try {
			if (localStorage.getItem('accessToken') === null || localStorage.getItem('accessToken') === '') {
				goto('/auth');
			} else {
				const response = await getUser(localStorage.getItem('accessToken'));
				if (response.ok) {
					const data = await response.json();
					user = data.user;
					goto('/');
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
</svelte:head>
<ModeWatcher defaultMode={"dark"} themeColors={{ dark: "#000000", light: "#ffffff" }} />
{#if loaded}
	<slot />
{/if}
