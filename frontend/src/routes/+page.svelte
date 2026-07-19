<script>
	import { lessonChunks } from '$lib/content.js';
	import { progress, isDone } from '$lib/progress.svelte.js';
	import { dueIds, deck } from '$lib/srs.svelte.js';

	let { data } = $props();
	const manifest = data.manifest;

	const GLYPHS = { 'unit0-alfabeto': 'Α', 'unit1-respostas': 'Κ' };
	const SECTION_PT = { nartex: 'Nártex', nave: 'Nave' };

	const units = manifest.units.map((u) => ({
		...u,
		lessons: lessonChunks(manifest, u.id).map((chunk, i) => ({
			n: i + 1,
			done: isDone(u.id, i + 1),
			preview: chunk
				.slice(0, 3)
				.map((id) => manifest.items[id].greek.split(' ')[0])
				.join(' · ')
		}))
	}));

	/** first not-done lesson across all units */
	function nextLesson() {
		for (const u of units)
			for (const l of u.lessons) if (!isDone(u.id, l.n)) return { unit: u.id, n: l.n };
		return null;
	}
	const next = $derived(nextLesson());
	const due = dueIds().length;

	// Sunday-prep window: Friday through Sunday, once any phrase is known
	const day = new Date().getDay();
	const sundayPrep = (day === 5 || day === 6 || day === 0) && Object.keys(deck.cards).length > 0;
</script>

<header class="top">
	<span class="brand">
		<svg width="10" height="15" viewBox="0 0 22 34" aria-hidden="true"><g stroke="currentColor" stroke-width="3"><line x1="11" y1="1.5" x2="11" y2="33" /><line x1="6.2" y1="6.5" x2="15.8" y2="6.5" /><line x1="2.5" y1="12.5" x2="19.5" y2="12.5" /><line x1="4.5" y1="23" x2="17.5" y2="27" /></g></svg>
		Ortholingo
	</span>
	<span class="stats">
		{#if progress.streak.count > 0}
			<span class="streak" title="Vela acesa: dias seguidos de prática">
				<svg width="12" height="16" viewBox="0 0 14 18" aria-hidden="true">
					<path d="M7 1C8.8 3.2 10.4 4.9 10.4 7A3.4 3.4 0 0 1 3.6 7C3.6 4.9 5.2 3.2 7 1Z" fill="#E7C97D" />
					<rect x="4.6" y="11" width="4.8" height="6" rx="1.4" fill="#C9A24B" />
				</svg>
				{progress.streak.count}
			</span>
		{/if}
		<span class="xp">{progress.xp} XP</span>
	</span>
</header>

<nav class="navrow">
	<a class="navchip" href="/liturgia">Mapa da Liturgia</a>
	<a class="navchip" class:hasdue={due > 0} href="/review">
		Revisar{#if due > 0}&nbsp;· {due}{/if}
	</a>
</nav>

{#if sundayPrep}
	<a class="sunday arch" href="/domingo">
		<span class="eyebrow">Preparação para o domingo</span>
		<b>Revise as respostas do povo antes da Liturgia</b>
		<span class="meta">5 min · as frases mais frequentes do rito</span>
	</a>
{/if}

{#if next}
	<a class="continue arch" href="/lesson/{next.unit}/{next.n}">
		<span class="eyebrow">Continuar</span>
		<b>{manifest.units.find((u) => u.id === next.unit).title} — lição {next.n}</b>
	</a>
{:else}
	<div class="continue arch"><b>Todas as lições concluídas — καλή δύναμη!</b></div>
{/if}

{#each units as unit}
	<p class="section-label">{SECTION_PT[unit.section] ?? unit.section} · {unit.title}</p>
	<ul class="path">
		{#each unit.lessons as l}
			<li>
				<a class="node" class:done={l.done} href="/lesson/{unit.id}/{l.n}">
					<span class="glyph greek">{l.done ? '✓' : (GLYPHS[unit.id] ?? 'Ω')}</span>
					<span class="info">
						<b>Lição {l.n}</b>
						<span class="greek preview">{l.preview}</span>
					</span>
				</a>
			</li>
		{/each}
	</ul>
{/each}

<style>
	.top { display: flex; justify-content: space-between; align-items: center; padding: 4px 2px 16px; }
	.brand {
		font-size: 12px; letter-spacing: 0.22em; text-transform: uppercase;
		color: var(--gold); font-weight: 700; display: flex; align-items: center; gap: 6px;
	}
	.xp { font-size: 13px; color: var(--gold2); font-variant-numeric: tabular-nums; }
	.navrow { display: flex; gap: 8px; margin-bottom: 14px; }
	.navchip {
		flex: 1; text-align: center; font-size: 13px; font-weight: 600;
		color: var(--dim); text-decoration: none; padding: 9px 6px;
		border: 1.5px solid var(--line); border-radius: 999px;
	}
	.navchip.hasdue { color: var(--gold2); border-color: var(--gold); }
	.stats { display: flex; align-items: center; gap: 12px; }
	.streak {
		display: flex; align-items: center; gap: 4px; font-size: 13px;
		color: var(--gold2); font-variant-numeric: tabular-nums;
	}
	.sunday {
		display: block; text-decoration: none; color: inherit; margin-bottom: 14px;
		border-color: var(--gold);
		background: linear-gradient(180deg, #c9a24b14, var(--nave) 55%);
	}
	.sunday b { font-size: 14.5px; }
	.sunday .meta { display: block; color: var(--dim); font-size: 12px; margin-top: 2px; }
	.continue { display: block; text-decoration: none; color: inherit; margin-bottom: 20px; border-color: var(--gold); }
	.continue b { font-size: 15px; }
	.section-label {
		font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase;
		color: var(--dim); margin: 18px 0 6px 2px;
	}
	.path { list-style: none; margin: 0; padding: 0; position: relative; }
	.path::before {
		content: ''; position: absolute; left: 26px; top: 12px; bottom: 12px;
		border-left: 2px dotted #3a466e;
	}
	.node {
		display: flex; gap: 14px; align-items: center; padding: 8px 0;
		text-decoration: none; color: inherit; position: relative;
	}
	.glyph {
		width: 52px; height: 52px; border-radius: 50%; flex: none;
		display: grid; place-items: center; font-size: 21px;
		background: var(--nave); border: 2px solid #3a466e; color: var(--dim); z-index: 1;
	}
	.node.done .glyph { background: var(--gold); border-color: var(--gold); color: #241c08; }
	.info b { display: block; font-size: 14px; }
	.preview { font-size: 12px; color: var(--dim); }
</style>
