<script>
	import { onDestroy } from 'svelte';
	import Mascot from './Mascot.svelte';
	import { play, stop } from '$lib/audio.js';
	import { phraseAudio, wordAudio, loadTimings } from '$lib/content.js';

	/** @type {{ item: any, onDone: () => void }} */
	let { item, onDone } = $props();

	let timings = $state(null);
	let hot = $state(-1);
	let mood = $state('content');
	let raf = null;

	$effect(() => {
		item.id; // re-fetch when the item changes
		timings = null;
		loadTimings(item.id).then((t) => (timings = t));
	});

	function playPhrase(speed) {
		clearHL();
		const a = play(phraseAudio(item.id, speed));
		const marks = timings?.[speed];
		if (!marks) return;
		const tick = () => {
			const t = a.currentTime;
			hot = marks.findIndex(([s, e]) => t >= s && t <= e + 0.05);
			if (!a.paused && !a.ended) raf = requestAnimationFrame(tick);
			else hot = -1;
		};
		raf = requestAnimationFrame(tick);
	}

	function playWord(i) {
		clearHL();
		stop();
		hot = i;
		const a = play(wordAudio(item.wordkeys[i]));
		a.onended = () => (hot = -1);
	}

	function clearHL() {
		if (raf) cancelAnimationFrame(raf);
		hot = -1;
	}

	onDestroy(() => {
		clearHL();
		stop();
	});
</script>

<section>
	<p class="eyebrow center">{item.kind === 'letter' ? 'Nova letra' : 'Nova frase'}</p>
	<Mascot {mood} />

	<div class="lines">
		<div class="gr greek" class:big={item.kind === 'letter'}>
			{#each item.words as w, i}
				<button class="w" class:hot={hot === i} onclick={() => playWord(i)}>{w.el}</button>
			{/each}
		</div>
		<div class="tl">
			{#each item.words as w, i}
				<button class="w" class:hot={hot === i} onclick={() => playWord(i)}>{w.tl}</button>
			{/each}
		</div>
		<p class="pt">{item.pt}</p>
	</div>

	{#if item.gloss?.length && item.kind !== 'letter'}
		<div class="gloss">
			{#each item.gloss as g}
				<span class="g"><b class="greek">{g.el}</b> · {g.pt}</span>
			{/each}
		</div>
	{/if}

	<div class="controls">
		<button class="playbtn" onclick={() => playPhrase('normal')} aria-label="Ouvir">
			<svg width="18" height="20" viewBox="0 0 20 22"><path d="M2 2 L18 11 L2 20 Z" fill="#241c08" /></svg>
		</button>
		<button class="slowbtn" onclick={() => playPhrase('slow')}>lento</button>
	</div>

	{#if item.context_pt}
		<p class="ctx">{item.context_pt}</p>
	{/if}
	{#if item.source}
		<p class="src">{item.source}</p>
	{/if}

	<button class="btn" onclick={onDone}>Continuar</button>
</section>

<style>
	.center { text-align: center; }
	.lines { margin: 14px 0 6px; }
	.gr, .tl { display: flex; flex-wrap: wrap; gap: 4px 8px; justify-content: center; }
	.gr { font-size: 30px; }
	.gr.big { font-size: 44px; }
	.tl { font-size: 14px; font-style: italic; color: var(--dim); margin-top: 2px; }
	.w {
		background: none;
		border: 0;
		color: inherit;
		font: inherit;
		cursor: pointer;
		border-radius: 8px;
		padding: 1px 6px;
		transition: background 0.12s, color 0.12s;
	}
	.w:hover { background: var(--raised); }
	.w.hot { background: var(--gold); color: #241c08; }
	.pt { text-align: center; font-size: 15px; margin: 10px 0 0; }
	.gloss { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 12px 0 0; }
	.g {
		font-size: 12px;
		color: var(--dim);
		border: 1px dashed var(--line);
		border-radius: 10px;
		padding: 4px 9px;
	}
	.g b { color: var(--parch); font-weight: 500; font-size: 13px; }
	.controls { display: flex; gap: 12px; justify-content: center; align-items: center; margin: 16px 0; }
	.playbtn {
		width: 54px;
		height: 54px;
		border-radius: 50%;
		border: 0;
		background: var(--gold);
		cursor: pointer;
		display: grid;
		place-items: center;
	}
	.playbtn svg { margin-left: 3px; }
	.playbtn:active { transform: scale(0.93); }
	.slowbtn {
		font-size: 12px;
		border: 1px solid var(--line);
		color: var(--gold2);
		background: none;
		border-radius: 999px;
		padding: 5px 12px;
		cursor: pointer;
	}
	.ctx { font-size: 13px; color: var(--dim); text-align: center; margin: 0 0 4px; }
	.src { font-size: 11px; color: var(--dim); text-align: center; opacity: 0.7; margin: 0 0 14px; }
</style>
