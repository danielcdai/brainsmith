<!-- <script context="module">
    export async function load({ url }) {
      const accessToken = url.searchParams.get('access_token');
      console.log(accessToken); // 这将输出URL中的`access_token`参数
      return { accessToken };
    }
</script> -->

<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
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

<main>
    <h1>Auth Callback</h1>
    <p>Access Token: {accessToken}</p>
</main>