<script lang="ts" module>
	import GalleryVerticalEnd from "lucide-svelte/icons/gallery-vertical-end";
	
	// This is sample data.
	const data = {
		teams: [
			{
				name: "Brainsmith",
				logo: GalleryVerticalEnd,
				plan: "Dashboard",
			},
		],
	};
</script>

<script lang="ts">
	import NavMain from "./NavMain.svelte";
	import NavUser from "./NavUser.svelte";
	import TeamSwitcher from "$lib/components/layout/TeamSwitcher.svelte";
    import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import type { ComponentProps } from "svelte";
	

	let {
		ref = $bindable(null),
		collapsible = "icon",
		...restProps
	}: ComponentProps<typeof Sidebar.Root> = $props();
	/**
	 * Trial for user data binding
	*/
	// let {
	// 	ref = $bindable(null),
	// 	collapsible = "icon",
	// 	user,
	// 	...restProps
	// }: ComponentProps<typeof Sidebar.Root> & { user: { name: string; email: string; avatar: string } } = $props();
</script>

<Sidebar.Root bind:ref {collapsible} {...restProps}>
	<Sidebar.Header>
		<TeamSwitcher teams={data.teams} />
	</Sidebar.Header>
	<Sidebar.Content>
		<NavMain/>
	</Sidebar.Content>
	<Sidebar.Footer>
		<NavUser />
	</Sidebar.Footer>
	<Sidebar.Rail />
</Sidebar.Root>
