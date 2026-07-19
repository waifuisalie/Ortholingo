<script>
	import Mascot from './Mascot.svelte';

	/** @type {{ step: any, onResult: (ok: boolean) => void, onDone: () => void }} */
	let { step, onResult, onDone } = $props();

	function shuffle(arr) {
		const a = [...arr];
		for (let i = a.length - 1; i > 0; i--) {
			const j = Math.floor(Math.random() * (i + 1));
			[a[i], a[j]] = [a[j], a[i]];
		}
		return a;
	}

	let left = $state([]);
	let right = $state([]);
	let sel = $state(null); // {side, id}
	let matched = $state({});
	let shake = $state(null);
	let mood = $state('content');
	let missed = false;

	$effect(() => {
		step;
		left = shuffle(step.pairs.map((p) => ({ id: p.id, label: p.el })));
		right = shuffle(step.pairs.map((p) => ({ id: p.id, label: p.pt })));
		sel = null;
		matched = {};
		mood = 'content';
		missed = false;
	});

	const allDone = $derived(Object.keys(matched).length === step.pairs.length);

	function pick(side, id) {
		if (matched[id] && side === 'left') return;
		if (matched[id] && side === 'right') return;
		if (!sel) {
			sel = { side, id };
			return;
		}
		if (sel.side === side) {
			sel = { side, id };
			return;
		}
		// cross-side pick: check match
		if (sel.id === id) {
			matched = { ...matched, [id]: true };
			mood = 'happy';
			if (Object.keys(matched).length === step.pairs.length) onResult(!missed);
		} else {
			missed = true;
			shake = id;
			mood = 'sadtear';
			setTimeout(() => (shake = null), 350);
		}
		sel = null;
	}
</script>

<section>
	<p class="eyebrow center">Ligue os pares</p>
	<Mascot {mood} size={90} />

	<div class="cols">
		<div class="col">
			{#each left as o}
				<button
					class="opt greek"
					class:sel={sel?.side === 'left' && sel.id === o.id}
					class:done={matched[o.id]}
					class:shake={shake === o.id}
					onclick={() => pick('left', o.id)}
					disabled={matched[o.id]}>{o.label}</button>
			{/each}
		</div>
		<div class="col">
			{#each right as o}
				<button
					class="opt"
					class:sel={sel?.side === 'right' && sel.id === o.id}
					class:done={matched[o.id]}
					class:shake={shake === o.id}
					onclick={() => pick('right', o.id)}
					disabled={matched[o.id]}>{o.label}</button>
			{/each}
		</div>
	</div>

	<button class="btn" disabled={!allDone} onclick={onDone}>Continuar</button>
</section>

<style>
	.center { text-align: center; }
	.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 16px 0 14px; }
	.col { display: flex; flex-direction: column; gap: 10px; }
	.opt {
		font-size: 15px; padding: 12px 8px; border-radius: 14px; text-align: center;
		background: var(--nave); border: 1.5px solid var(--line); color: var(--parch);
		cursor: pointer; transition: border-color 0.15s, opacity 0.2s;
	}
	.opt.greek { font-family: var(--serif); font-size: 18px; }
	.opt.sel { border-color: var(--gold2); background: var(--raised); }
	.opt.done { border-color: var(--good); background: #82a85c1e; opacity: 0.65; cursor: default; }
	.opt.shake { border-color: var(--bad); animation: shake 0.3s; }
	@keyframes shake {
		0%, 100% { transform: translateX(0); }
		25% { transform: translateX(-5px); }
		75% { transform: translateX(5px); }
	}
</style>
