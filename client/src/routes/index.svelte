<script lang="ts">
	// import ScatterChart from "@onsvisual/svelte-charts/src/charts/ScatterChart.svelte"

	import { LayerCake, Svg } from 'layercake';
	import PercentLayer from '$lib/percentLayer.svelte';
	import merge from 'lodash.merge';
	import colours from '$lib/colours';

	import { onMount } from 'svelte';

	let chDown = colours.red[600];
	let chWarn = colours.yellow[600];
	let chUp = colours.green[600];
	let chInfo = colours.sky[600];

	export let data: any = {};

	let dataError: boolean | any = false;
	// $: console.log(data);

	let portmon_modules_checked = 0;

	let portmon: {
		lastresponsetime: number;
		mod: string;
		name: string;
		status: 'up' | 'paused' | 'down';
		type: string;
	}[] = [];

	$: {
		let t: any[] = [];
		Object.entries(data.port_monitoring).forEach((e) => {
			let [mod, element]: [string, any[]] = e as [string, any[]];
			t.push(
				element.map((i: any) => {
					i.mod = mod;
					return i;
				})
			);
		});

		portmon = t.flat(1);
		portmon_modules_checked = t.length;

		// console.log(portmon);
	}

	let portmon_ag_results = {
		up: 0,
		down: 0,
		paused: 0,

		total_accounts: 0,
		failed_accounts: 0
	};

	$: {
		let t = {
			up: 0,
			down: 0,
			paused: 0,

			total_accounts: 0,
			failed_accounts: 0
		};
		Object.entries(data.port_monitoring_success).forEach((e) => {
			let [mod, dat]: [string, any] = e;
			t.up += dat.up;
			t.down += dat.down;
			t.paused += dat.paused;
			t.total_accounts += dat.total_accounts;
			// console.log(mod, dat.valid_until < Date.now())
			if (dat.valid_until < Date.now()) {
				t.failed_accounts += dat.total_accounts;
			} else {
				t.failed_accounts += dat.failed_accounts;
			}
		});
		portmon_ag_results = t;
	}

	let resmon_green = 0;
	let resmon_orange = 0;
	let resmon_blue = 0;
	let resmon_red = 0;

	let resmon: any[] = [];

	$: {
		let t: any[] = [];
		Object.entries(data.resources).forEach((e) => {
			let [mod, element]: [string, any] = e;
			Object.entries(element).forEach((res) => {
				let [id, dat]: [string, any] = res;
				t.push(dat);
				switch (dat.health_status) {
					case 'green':
						resmon_green += 1;
						break;
					case 'orange':
						resmon_orange += 1;
						break;
					case 'red':
						resmon_red += 1;
						break;
					case 'blue':
						resmon_blue += 1;
						break;

					default:
						break;
				}
			});
		});
		resmon = t;
	}

	function getIcon(mod: string): string {
		switch (mod) {
			case 'rapidspike':
				return 'rapidspike.png';
				break;
			case 'appbeat':
				return 'appbeat.ico';
				break;
			case 'pingdom':
				return 'pingdom.png';
				break;

			default:
				return 'unknown.png';
				break;
		}
	}

	async function streamDat() {
		dataError = false;
		let response = await fetch('./stream').catch((e: Error) => {
			console.error('stream start', e);
			dataError = e.message;
			setTimeout(streamDat, 500);
		});
		// Retrieve its body as ReadableStream
		const reader = response?.body?.getReader();
		if (!reader) return;

		// console.log(response)

		let decoder = new TextDecoder();

		let done,
			value,
			textbuf = '';
		while (!done) {
			({ value, done } = await reader?.read().catch((e) => {
				console.error('stream continuity', e);
				dataError = e.message;
				setTimeout(streamDat, 500);
				return { done: true, value: undefined }
			}));

			if (done) {
				break;
			}
			textbuf += decoder.decode(value);
			let arr = textbuf.split('\n');
			if (arr.length) textbuf = arr.pop() as string;

			arr.forEach((s) => {
				// console.log(JSON.parse(s))
				try {
					data = merge(data, JSON.parse(s));
				} catch (error) {
					console.log('stream error', s, error);
				}
			});
		}
	}
	onMount(streamDat);
</script>

{#if dataError}
	<div style="background-color: lightcoral;">{JSON.stringify(dataError)}</div>
{/if}

<div class="grid">
	<!-- {#each portmon as table} -->
	<div class="panel portmon-panel">
		<div class="percent-container">
			<!-- 800 -->
			<LayerCake
				ssr={true}
				percentRange={false}
				data={[
					{ w: portmon_ag_results.down, c: chDown },
					{ w: portmon_ag_results.paused, c: chInfo },
					{ w: portmon_ag_results.up, c: chUp }
				]}
				x="w"
				z="c"
			>
				<Svg>
					<PercentLayer />
				</Svg>
			</LayerCake>
		</div>
		<div class="panel-inner">
			<table class="portmon">
				<thead>
					<td class="icon" />
					<td class="name l">Name</td>
					<td class="time r">Latency</td>
					<td class="type l">Type</td>
				</thead>
				<tbody>
					{#each portmon
						.sort((a, b) => b.lastresponsetime - a.lastresponsetime)
						.sort((a, b) => {
							if (a.status === b.status) {
								return 0;
							} else if (a.status > b.status) {
								return 1;
							} else {
								return -1;
							}
						}) as item}
						<tr class={item.status}>
							<td class="icon"><img width="20" src="/{getIcon(item.mod)}" alt={item.mod} /></td>
							<td class="name l">{item.name}</td>
							<td class="time r">{item.lastresponsetime}ms</td>
							<td class="type l">{item.type.toUpperCase()}</td>
							<!-- {#each Object.keys(item).sort() as key}
						<td>{JSON.stringify(key)}: {JSON.stringify(item[key])}</td>
					{/
				ssr={true}each} -->
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
	<!-- {/each} -->
	<div class="panel resmon-panel">
		<div class="percent-container">
			<LayerCake
				ssr={true}
				data={[
					{ w: resmon_red, c: chDown },
					{ w: resmon_orange, c: chWarn },
					{ w: resmon_blue, c: chInfo },
					{ w: resmon_green, c: chUp }
				]}
				x="w"
				z="c"
			>
				<Svg>
					<PercentLayer />
				</Svg>
			</LayerCake>
		</div>
		<div class="panel-inner">
			<table class="resmon">
				<thead>
					<td class="name l">Name</td>
					<td class="cpu r">CPU</td>
					<td class="memory r">Memory</td>
					<td class="fullest_disk r" title="Fullest Disk">Space</td>
					<td class="disk_io r">Disk IO</td>
				</thead>
				<tbody>
					{#each resmon.sort((a, b) => b.orderby - a.orderby)
						.sort((b, a) => {
							if (a.health_status === b.health_status) {
								return 0;
							} else if (a.health_status > b.health_status) {
								return 1;
							} else {
								return -1;
							}
						}) as item}
						<tr class={item.health_status}>
							<!-- {#each Object.keys(item).sort() as key}
							<td>{JSON.stringify(key)}: {JSON.stringify(item[key])}</td>
						{/each} -->
							<td class="name l">{item.name}</td>
							<td class="cpu r">{Math.round(item.summary.cpu)}%</td>
							<td class="memory r">{Math.round(item.summary.memory)}%</td>
							<td class="fullest_disk r">{Math.round(item.summary.fullest_disk)}%</td>
							<td class="disk_io r">{Math.round(item.summary.disk_io)}%</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
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
			grid-template-columns: repeat(2, 1fr);
		}
	}
	.panel {
		background-color: white;
		overflow: hidden;
		box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
		border-radius: 0.5rem;
	}
	.panel-inner {
		border-top: rgb(211, 213, 218);
		/* padding-top: 1.25rem;
		padding-bottom: 1.25rem;
		padding-left: 1rem;
		padding-right: 1rem; */
	}

	/* @media (min-width: 640px) {
		.panel-inner {
			padding: 1.5rem;
		}
	} */

	.percent-container {
		height: 24px;
		width: 100%;
	}
	table,
	td {
		text-overflow: ellipsis;
		white-space: nowrap;
		overflow: hidden;
	}
	tr {
		border-top: 1px solid rgb(208, 208, 208);
	}

	table {
		border-collapse: collapse;
		table-layout: fixed;
		border-spacing: 0;
		width: 100%;
		max-width: 100%;
	}

	.icon {
		text-align: center;
		vertical-align: middle;
		width: 25px;
	}
	.type {
		width: 5rem;
		padding-left: 0.5rem;
		padding-right: 0.5rem;
	}

	.time {
		width: 6em;
	}

	.cpu,
	.memory,
	.fullest_disk,
	.disk_io {
		width: 4em;
	}

	@keyframes downBlink {
		0% {
			background-color: #fef2f2;
		}
		100% {
			background-color: #fee2e2;
		}
	}
	.up,
	.green {
		background-color: rgb(220 252 231);
	}
	.paused,
	.blue {
		background-color: #e0f2fe;
	}
	.orange {
		background-color: #fef9c3;
	}
	.down,
	.red {
		background-color: rgb(254 226 226); /* 100 */
		animation: downBlink 1s infinite alternate-reverse;
	}
	.r {
		text-align: right;
	}
	.l {
		text-align: lefft;
	}
</style>
