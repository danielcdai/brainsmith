<script lang="ts">
	import Calendar from 'lucide-svelte/icons/calendar';
	import House from 'lucide-svelte/icons/house';
	import Inbox from 'lucide-svelte/icons/inbox';
    import Chat from "lucide-svelte/icons/message-circle";
	import Search from 'lucide-svelte/icons/search';
	import Settings from 'lucide-svelte/icons/settings';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import { base } from '$app/paths';

	const items = [
		{
			title: 'Chat',
			url: `${base}/chat`,
			icon: Chat
		},
		{
			title: 'Embedding',
			url: '#',
			icon: Inbox
		},
		{
			title: 'Playground',
			url: '#',
			icon: Calendar
		},
		{
			title: 'Settings',
			url: '#',
			icon: Settings
		}
	];
</script>

<Sidebar.Group>
	<Sidebar.GroupLabel>Application</Sidebar.GroupLabel>
	<Sidebar.GroupContent>
		<Sidebar.Menu>
			{#each items as item (item.title)}
				<Sidebar.MenuItem>
					<Sidebar.MenuButton>
						{#snippet child({ props })}
							<a href={item.url} {...props}>
								<item.icon />
								<span>{item.title}</span>
							</a>
						{/snippet}
					</Sidebar.MenuButton>
				</Sidebar.MenuItem>
			{/each}
		</Sidebar.Menu>
	</Sidebar.GroupContent>
</Sidebar.Group>
