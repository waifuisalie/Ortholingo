<script>
	import { isKnown } from '$lib/srs.svelte.js';

	let { data } = $props();
	const manifest = data.manifest;

	let map = $state(null);
	$effect(() => {
		fetch('/assets/liturgy-map.json').then((r) => r.json()).then((m) => (map = m));
	});

	function chipLabel(it) {
		return it.future ? it.label_el : manifest.items[it.ref].greek;
	}

	const stats = $derived.by(() => {
		if (!map) return { pct: 0, sections: [] };
		let total = 0;
		let known = 0;
		const sections = map.sections.map((sec) => {
			const items = sec.items.map((it) => {
				const lit = !it.future && isKnown(it.ref);
				total += it.weight;
				if (lit) known += it.weight;
				return { ...it, lit };
			});
			return { ...sec, items, done: items.every((i) => i.lit) };
		});
		return { pct: total ? Math.round((known / total) * 100) : 0, sections };
	});

	// semicircle gauge: pathLength=283 (approx arc length), dash = pct
	const dash = $derived((stats.pct / 100) * 283);
</script>

<p class="eyebrow">{map?.liturgy?.title_pt ?? 'Divina Liturgia'}</p>
<h2>Seu mapa da Liturgia</h2>
<p class="sub">Frases acesas são as que você já conhece. As apagadas ainda esperam por você — algumas nem chegaram ao app.</p>

<div class="gauge" role="img" aria-label="Você já entende {stats.pct}% da Divina Liturgia">
	<svg width="210" height="120" viewBox="0 0 210 120">
		<path d="M15 110 A90 90 0 0 1 195 110" fill="none" stroke="#2a3557" stroke-width="12" stroke-linecap="round" />
		<path d="M15 110 A90 90 0 0 1 195 110" fill="none" stroke="var(--gold)" stroke-width="12" stroke-linecap="round"
			stroke-dasharray="{dash} 283" pathLength="283" />
		<text x="105" y="88" text-anchor="middle" class="num">{stats.pct}%</text>
		<text x="105" y="106" text-anchor="middle" class="lbl">da Liturgia</text>
	</svg>
</div>
<p class="gnote">ponderado pela frequência real de cada frase no rito</p>

{#each stats.sections as sec}
	<div class="arch lsec">
		<div class="head">
			<b>{sec.title_pt}</b>
			{#if sec.done}<span class="pill full">completa</span>{/if}
		</div>
		<div class="chips">
			{#each sec.items as it}
				<span class="chip greek" class:lit={it.lit} class:future={it.future}
					title={it.future ? `${it.label_pt} — em breve no app` : manifest.items[it.ref].pt}>
					{chipLabel(it)}
				</span>
			{/each}
		</div>
	</div>
{/each}

<a class="btn ghost back" href="/">Voltar ao caminho</a>

<style>
	h2 { font-size: 22px; }
	.sub { color: var(--dim); font-size: 13px; margin: 0 0 14px; }
	.gauge { display: grid; place-items: center; }
	.num { font-family: var(--serif); font-size: 34px; fill: var(--gold2); }
	.lbl { font-size: 10.5px; letter-spacing: 0.12em; text-transform: uppercase; fill: var(--dim); }
	.gnote { text-align: center; color: var(--dim); font-size: 11.5px; margin: 2px 0 18px; }
	.lsec { margin-bottom: 12px; }
	.head { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; margin-bottom: 8px; }
	.head b { font-size: 13.5px; }
	.pill.full {
		font-size: 11px; color: #241c08; background: var(--gold);
		padding: 1px 8px; border-radius: 999px; font-weight: 600;
	}
	.chips { display: flex; flex-wrap: wrap; gap: 6px; }
	.chip {
		font-size: 13px; padding: 4px 10px; border-radius: 999px;
		border: 1px solid #3a466e; color: var(--dim);
	}
	.chip.lit { color: var(--gold2); border-color: var(--gold); background: #c9a24b1a; }
	.chip.future { opacity: 0.45; border-style: dashed; }
	.back { margin-top: 20px; text-align: center; text-decoration: none; }
</style>
