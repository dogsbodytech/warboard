<script lang="ts">

	import { LayerCake, Svg } from 'layercake';
	import PercentLayer from '$lib/PercentLayer.svelte';
	import colours from '$lib/colours';

	let red = colours.red[600];
	let orange = colours.yellow[600];
	let green = colours.green[600];
	let blue = colours.sky[600];

	export let data;
	
	let dataDestructured: any = data?.data || {};

	$: console.log(dataDestructured);

	$: total_filter = dataDestructured.filters.find((e: any[]) => e[0] == "total_filter")[1]

	$: orange_filter = dataDestructured.filters.find((e: any[]) => e[0] == "orange_filter")[1]
	$: red_filter = dataDestructured.filters.find((e: any[]) => e[0] == "red_filter")[1]
	$: blue_filter = dataDestructured.filters.find((e: any[]) => e[0] == "blue_filter")[1]

	$: sirportlyData = [
		{
			w:
				orange_filter.pagination.total_records ,
			c: orange
		},
		{
			w:
				red_filter.pagination.total_records ,
			c: red
		},
		{
			w:
				blue_filter.pagination.total_records,
			c: blue
		},
		{
			w: total_filter.pagination.total_records - (
				orange_filter.pagination.total_records +
				red_filter.pagination.total_records +
				blue_filter.pagination.total_records 
			),
			c: green
		}
	];

	$: console.log(sirportlyData);
</script>

<div class="grid">
	<div>
		<h2>Sirportly</h2>
		<div class="panel portmon-panel">
			<div class="percent-container">
				<!-- 800 -->
				<LayerCake
					ssr={true}
					percentRange={false}
					data={sirportlyData}
					x="w"
					z="c"
				>
					<Svg>
						<PercentLayer />
					</Svg>
				</LayerCake>
			</div>
			<div class="panel-inner" />
		</div>
		{#each dataDestructured.filters as filter}
			<section>
				<hgroup>
					<h3>{filter[1].filter.name} ({filter[1].filter.id})</h3>
					<p>{filter[1].filter.description}</p>
				</hgroup>
				<p>{filter[1]?.pagination?.total_records}</p>
			</section>
		{/each}
	</div>
	<div>calendar 1</div>
	<div>calendar 2</div>
	<div>calendar n</div>
</div>

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(1, 1fr);
		gap: 1rem;
		grid-auto-rows: minmax(100px, auto);
	}
	@media (min-width: 1024px) {
		.grid {
			grid-template-columns: repeat(3, 1fr);
		}
	}

	div > h2 {
		margin: 0;
		margin-bottom: 0.5rem;
	}

	.panel {
		background-color: white;
		overflow: hidden;
		box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
		border-radius: 0.5rem;
	}

	.percent-container {
		height: 1.5rem;
		width: 100%;
	}
</style>
