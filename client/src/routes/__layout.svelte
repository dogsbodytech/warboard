<slot />

<style>
	:global(body) {
		padding-left: 1rem;
		padding-right: 1rem;
		font-family: Helvetica, Arial, sans-serif;
	}
	@media (min-width: 640px) {
		:global(body) {
			padding-left: 1.5rem;
			padding-right: 1.5rem;
		}
	}
	@media (min-width: 1024px) {
		:global(body) {
			padding-left: 2rem;
			padding-right: 2rem;
		}
	}
	:global(body) {
		margin-left: auto;
		margin-right: auto;
	}
</style>
