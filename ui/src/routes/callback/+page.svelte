<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$lib/utils.js';
    import { authToken } from '$lib/../stores/auth.js';
    
    let accessToken: string | null = null;
    onMount(async () => {
        const urlParams = new URLSearchParams(window.location.search);
        accessToken = urlParams.get('access_token');
        if (accessToken) {
            authToken.set(accessToken);
            await goto('/');
        } else {
            await goto('/auth');
        }
        
    });
</script>

<div>
    <h1>Callback</h1>
</div>