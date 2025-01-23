<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$lib/utils.js';

    let accessToken: string | null = null;
    onMount(async () => {
        const urlParams = new URLSearchParams(window.location.search);
        accessToken = urlParams.get('access_token');
        console.log('access_token: ', accessToken)
        if (accessToken) {
            localStorage.setItem('accessToken', accessToken);
            await goto('/');
        } else {
            await goto('/auth');
        }
        
    });
</script>

<div>
    <h1>Callback</h1>
    <p>Access Token: {accessToken}</p>
</div>