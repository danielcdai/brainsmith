<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { authToken } from '../stores/auth';

	// If you want to call your protected FastAPI endpoint:
	const BACKEND_URL = 'http://localhost:8000';

	let tokenValue: string | null = null;
	const unsubscribe = authToken.subscribe((val) => {
		tokenValue = val;
	});

	let loaded = false;
	// On mount, check if we have a token. If not, redirect to /auth.
	onMount(() => {
		if (!tokenValue) {
			// If we also stored the token in localStorage, you could read it:
			// tokenValue = localStorage.getItem('my_app_token');

			if (!tokenValue) {
				loaded = false;
				window.location.href = '/ui/auth';
			} else {
				// If we found a token in localStorage, re-set in store for reactivity
				authToken.set(tokenValue);
				loaded = true;
			}
		}
	});

	// Cleanup subscription
	onDestroy(() => {
		unsubscribe();
	});

	// Example protected fetch
	// let greeting = '';

	// async function fetchProtectedResource(): Promise<void> {
	// if (!tokenValue) return;

	// try {
	// 	const res = await fetch(`${BACKEND_URL}/protected-resource`, {
	// 	headers: {
	// 		Authorization: `Bearer ${tokenValue}`
	// 	}
	// 	});

	// 	if (!res.ok) {
	// 	throw new Error('Unauthorized or other error.');
	// 	}

	// 	const data = await res.json();
	// 	greeting = data.message; // e.g. "You are authorized!"
	// } catch (err) {
	// 	console.error(err);
	// 	// If token is invalid, redirect user back to /auth
	// 	window.location.href = '/auth';
	// }
	// }

	// Initiate the protected request on mount
	//   onMount(fetchProtectedResource);
	// import '../app.css';
	// import { onMount, tick } from 'svelte';
	// import { goto } from '$lib/utils.js';
	// import {  getUser } from '$lib/api/auth/index.js';
	// import { ModeWatcher } from "mode-watcher";

	// let user = null;

	// async function getUserInfo() {
	//         try {
	// 			if (localStorage.getItem('accessToken') === null || localStorage.getItem('accessToken') === '') {
	// 				goto('/auth');
	// 			} else {
	// 				const response = await getUser(localStorage.getItem('accessToken'));
	// 				if (response.ok) {
	// 					const data = await response.json();
	// 					user = data.user;
	// 					goto('/');
	// 				} else {
	// 					goto('/auth');
	// 				}
	// 			}

	//         } catch (error) {
	//             console.error("Failed to fetch user:", error);
	// 			goto('/auth');
	//         }
	//     }

	// let loaded = false;
	// onMount(async () => {

	// 	getUserInfo();
	// 	await tick();
	// 	loaded = true;
	// });
</script>

<svelte:head>
	<title>Blacksmith</title>
</svelte:head>
<!-- <ModeWatcher defaultMode={'dark'} themeColors={{ dark: '#000000', light: '#ffffff' }} /> -->
{#if loaded}
	<slot />
{/if}
