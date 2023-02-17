<!-- { filename: './components/Scatter.svelte' } -->
<script lang=ts>
	// Import the getContext function from svelte
	import { getContext } from 'svelte';

	// Access the context using the 'LayerCake' keyword
	// Grab some helpful functions
	const { data, x, z } = getContext('LayerCake');

	// Customizable defaults
	export let height = 24;

	let percents: {
		xDist: number;
		width: number;
		fill: string;
	}[] = [];

	let w = 1;

	$: {
		let xDist = 0;
		percents = $data
			// .sort((a, b) => {
			//     if (a.name === b.name) {
			//         return 0;
			//     } else if (a.name > b.name) {
			//         return 1;
			//     } else {
			//         return -1;
			//     }
			// 	})
			.map((d: any) => {
				let i: any = {};
				i.xDist = xDist;
				i.width = $x(d);
				i.fill = $z(d);
				xDist += i.width;
				return i;
			});
		w = xDist;
	}
</script>

<g>
	{#each percents as d, i}
		<rect
			class="percentage-segment"
			fill={d.fill}
			{height}
			x="{(d.xDist * 100) / w}%"
			y="0"
			width="{(d.width * 100) / w}%"
		/>
	{/each}
</g>
