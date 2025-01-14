<script context="module">
    export async function load({ url }) {
        const code = url.searchParams.get('code');
        return { props: { code }}
    }
</script>

<script lang="ts">
    import { onMount } from 'svelte';
    import { callback } from '$lib/api/auth/index.js';
    import {VITE_GITHUB_CLIENT_ID, VITE_GITHUB_SECRET} from '$lib/constants.js';

    export let code;
    let user = null;
    onMount(async () => {
        console.log('code: ',code);
        if (code) {
            const response = await callback({
                client_id: VITE_GITHUB_CLIENT_ID,
                client_secret: VITE_GITHUB_SECRET,
                code: code
            });
            user = await response.json();
            if (user) {
                localStorage.setItem('user', JSON.stringify(user));
                console.log(user);
                window.location.href = '/';
            }
        }
        
    });
</script>
<div>
    <p>Code: {code}</p>
</div>