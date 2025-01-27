<script lang="ts">
import '../app.css';
import { onMount, onDestroy, tick } from 'svelte';
import { goto } from '$lib/utils.js';
import {  getUser } from '$lib/api/auth/index.js';
import { ModeWatcher } from "mode-watcher";
import { authToken } from '../stores/auth.js';
// import { authToken } from "~/stores/auth.js";

let user = null;
let accessToken;
const unsubscribe = authToken.subscribe(value => {
	accessToken = value;
});
async function getUserInfo() {
        try {
			if (!accessToken) {
				goto('/auth');
			} else {
				const response = await getUser(accessToken);
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

onDestroy(() => {
	unsubscribe();
});
  

</script>

<svelte:head>
	<title>Blacksmith</title>
</svelte:head>
<ModeWatcher defaultMode={"dark"} themeColors={{ dark: "#000000", light: "#ffffff" }} />
{#if loaded}
	<slot />
{/if}
