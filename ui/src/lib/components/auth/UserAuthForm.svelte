<script lang="ts">
    import { Button } from "../ui/button/index.js";
    import Input from "../ui/input/input.svelte";
    import Label from "../ui/label/label.svelte";
    import { Icons } from "../icons/index.js";
	import { cn } from "$lib/utils.js";
    import { login } from '$lib/api/auth/index.js';
	import { onMount } from 'svelte';
	import { authToken } from '$lib/../stores/auth';
	const BACKEND_URL = 'http://localhost:8000';
	async function handleLogin(event: Event) {
        // event.preventDefault();
		// const response = await login();
		// console.log('response', response);
		// if (response.ok) {
		// 	const data = await response.json();
		// 	console.log('data', data);
		// 	window.location.href = data;
		// }
		window.location.href = `${BACKEND_URL}/auth/github/login`;
    }

	let className: string | undefined | null = undefined;
	export { className as class };

	let isLoading = false;
	async function onSubmit() {
		isLoading = true;

		setTimeout(() => {
			isLoading = false;
		}, 3000);
	}
	onMount(() => {
		const urlParams = new URLSearchParams(window.location.search);
		const token = urlParams.get('access_token');

		if (token) {
		authToken.set(token);

		// Optionally persist the token in localStorage:
		// localStorage.setItem('my_app_token', token);

		// Redirect to home ("/") or anywhere else you like:
		window.location.href = '/';
		}
	});
</script>

<div class={cn("grid gap-6", className)} {...$$restProps}>
	<form on:submit|preventDefault={onSubmit}>
		<div class="grid gap-2">
			<div class="grid gap-1">
				<Label class="sr-only" for="email">Email</Label>
				<Input
					id="email"
					placeholder="name@example.com"
					type="email"
					autocapitalize="none"
					autocomplete="email"
					autocorrect="off"
					disabled={isLoading}
				/>
			</div>
			<Button type="submit" disabled={isLoading}>
				{#if isLoading}
					<Icons.spinner class="mr-2 h-4 w-4 animate-spin" />
				{/if}
				Sign In with Email
			</Button>
		</div>
	</form>
	<div class="relative">
		<div class="absolute inset-0 flex items-center">
			<span class="w-full border-t" ></span>
		</div>
		<div class="relative flex justify-center text-xs uppercase">
			<span class="bg-background text-muted-foreground px-2"> Or continue with </span>
		</div>
	</div>
	<Button variant="outline" type="button" disabled={isLoading} onclick={handleLogin}>
		{#if isLoading}
			<Icons.spinner class="mr-2 h-4 w-4 animate-spin" />
		{:else}
			<Icons.gitHub class="mr-2 h-4 w-4" />
		{/if}
		GitHub
	</Button>
</div>
