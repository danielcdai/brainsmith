<script lang="ts">
	import { Icons } from "$lib/components/ui/icons/index.js";
	import { Button } from "$lib/components/ui/button/index.js";
	import * as Card from "$lib/components/ui/card/index.js";
	import { Label } from "$lib/components/ui/label/index.js";
	import { Input } from "$lib/components/ui/input/index.js";

    import { login } from '$lib/api/auth/index.js';
	async function handleLogin(event: Event) {
        event.preventDefault();
		const response = await login();
		console.log('response', response);
		if (response.ok) {
			const data = await response.json();
			console.log('data', data);
			window.location.href = data;
		}
    }

</script>

<Card.Root>
	<Card.Header class="space-y-1">
		<Card.Title class="text-2xl text-center">Brainsmith Dashboard</Card.Title>
		<Card.Description>Enter your email below to create your account</Card.Description>
	</Card.Header>
	<Card.Content class="grid gap-4">
		<div class="grid gap-2">
			<Label for="email">Email</Label>
			<Input id="email" type="email" placeholder="m@example.com" />
		</div>
		<div class="grid gap-2">
			<Label for="password">Password</Label>
			<Input id="password" type="password" />
		</div>
		<Button class="w-full">Sign In</Button>
		<Button class="w-full" variant="secondary">Create account</Button>
		<div class="relative">
			<div class="absolute inset-0 flex items-center">
				<!-- svelte-ignore element_invalid_self_closing_tag -->
				<span class="w-full border-t" />
			</div>
			<div class="relative flex justify-center text-xs uppercase">
				<span class="bg-card text-muted-foreground px-2"> Or continue with </span>
			</div>
		</div>
		<div class="grid grid-cols-1 gap-6">
			<Button variant="outline" onclick={handleLogin}>
				<Icons.gitHub class="mr-2 h-4 w-4" />
				GitHub
			</Button>
		</div>
		<div class="grid grid-cols-1 gap-6">
			<Button variant="outline">
				<Icons.google class="mr-2 h-4 w-4" />
				Google
			</Button>
		</div>
	</Card.Content>
</Card.Root>