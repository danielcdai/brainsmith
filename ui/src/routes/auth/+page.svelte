<script lang="ts">
	import { login } from '$lib/api/auth/index.js';
    import { onMount } from 'svelte';
    let githubAuthUrl = '';
    onMount(async () => {
        const res = await login();
        const data = await res.json();
        githubAuthUrl = data.githubAuthUrl;
    });
    const handleLogin = () => {
        window.location.href = githubAuthUrl;
    };
</script>

<div class="block h-screen bg-white p-4 text-black">
	<div class="flex h-40 items-center justify-center">
		<span class="text-2xl font-bold">Wellcome to Brainsmith Dashboard </span>
	</div>
	<div class="m-auto block h-72 w-96 rounded-lg border-2 border-purple-500 bg-purple-400 p-2">
		<div class="m-auto flex h-1/2 w-72 items-center justify-center text-xl font-bold">
			<span> Log in to BrainSmith </span>
		</div>
		<div class="m-auto flex w-72 items-center justify-center">
			<button
				class="rounded
             bg-blue-500
            px-4 py-2 font-bold text-white hover:bg-blue-700"
				on:click={handleLogin}
			>
				Sign in with Github
			</button>
		</div>
	</div>
</div>
