<script lang="ts">
	import { onMount } from 'svelte';
	import AppSidebar from '$lib/components/layout/AppSidebar.svelte';
	// import { Separator } from "$lib/registry/new-york/ui/separator/index.js";
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import ToggleTheme from '$lib/components/mode/ToggleTheme.svelte';

	onMount(() => {
		document.documentElement.setAttribute('data-theme', 'dark');
	});
</script>

<Sidebar.Provider>
	<AppSidebar />
	<Sidebar.Inset>
		<header
			class="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12"
		>
			<div class="flex items-center gap-2 px-4">
				<Sidebar.Trigger class="-ml-1" />
                <div class="">
                    <ToggleTheme />
                </div>
				
			</div>
		</header>
		<slot />
	</Sidebar.Inset>
</Sidebar.Provider>
