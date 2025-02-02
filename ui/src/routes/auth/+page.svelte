<script lang="ts">
	import '../../app.css';
	import { CardsCreateAccount } from "../(components)/index.js";
</script>

<div class="app">
	<main>
		<section>
			<CardsCreateAccount />
		</section>
	</main>

	<footer>
		<p>
			&copy; {new Date().getFullYear()} Daniel Dai. All rights reserved.
		</p>
	</footer>
</div>

<style>
	section {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		flex: 0.6;
	}
	.app {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	main {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: 1rem;
		width: 100%;
		max-width: 64rem;
		margin: 0 auto;
		box-sizing: border-box;
	}

	footer {
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		padding: 12px;
	}

	@media (min-width: 480px) {
		footer {
			padding: 12px 0;
		}
	}
</style>