<script lang="ts">
import '../app.css';
import Navbar from '$lib/components/layout/Navbar.svelte';
let isDark: Boolean = true; 

  const toggleTheme = (): void => {
    const link = document.getElementById('theme-style') as HTMLLinkElement | null;

    if (link) {
      let currentTheme = isDark ? '-dark' : '';
      link.href = `smui${currentTheme}.css`;
    } else {
      console.error('Theme link element not found');
    }
	isDark = !isDark;
  };
  

  

</script>

<svelte:head>
	<title>Blacksmith</title>
	<link id="theme-style" rel="stylesheet" type="text/css" href="/smui.css" />
</svelte:head>

<div class="container">
	<section class="left">
		<button on:click={toggleTheme}>
			Toggle Theme
		  </button>
		<Navbar/>
	</section>
	<section class="right">
		<slot/>
	</section>
</div>



<style>
	.container {
		display: flex;
		height: 100%;
	}
	.left {
		width: 30%;
		float: left;
		border: 1px solid #000;
		height: 100%;
	}
	.right {
		width: 70%;
		float: right;
	}
</style>