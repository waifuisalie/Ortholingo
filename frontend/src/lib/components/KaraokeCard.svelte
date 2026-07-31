<script>
	import { onDestroy } from 'svelte';
	import Mascot from './Mascot.svelte';
	import { play, stop } from '$lib/audio.js';
	import { phraseAudio, wordAudio, segmentAudio, loadTimings } from '$lib/content.js';
	import { ensureCard, fadeTranslit } from '$lib/srs.svelte.js';

	/** @type {{ item: any, onDone: () => void, seg?: number|null }} */
	let { item, onDone, seg = null } = $props();

	let timings = $state(null);
	let hot = $state(-1);
	let mood = $state('content');
	let peek = $state(false);
	let raf = null;

	const faded = $derived(fadeTranslit(item.id) && !peek);

	/** long phrases carry sense-parts; short ones don't (empty = behaves as before) */
	const segs = $derived(item.segments ?? []);
	/** which part the currently-highlighted word belongs to (-1 = none playing) */
	const hotSeg = $derived.by(() =>
		hot < 0 || !segs.length ? -1 : segs.findIndex((s) => hot >= s.words[0] && hot <= s.words[1])
	);
	/** word indices a part covers, e.g. [3,4,…,11] */
	const segWords = (s) => Array.from({ length: s.words[1] - s.words[0] + 1 }, (_, k) => s.words[0] + k);
	/** part mode renders just this segment; whole mode renders the assembled phrase */
	const part = $derived(seg != null && segs.length ? segs[seg] : null);
	const wrange = $derived(part ? segWords(part) : item.words.map((_, i) => i));

	const speaker = $derived(
		item.tags?.includes('sacerdote') ? 'O sacerdote diz'
		: item.tags?.includes('diacono') ? 'O diácono diz'
		: item.tags?.includes('hino') ? 'O povo canta'
		: item.tags?.includes('resposta-do-povo') ? 'O povo responde'
		: item.tags?.includes('povo') ? 'O povo diz'
		: null
	);

	$effect(() => {
		item.id; // re-fetch when the item changes
		timings = null;
		peek = false;
		ensureCard(item.id); // meeting an item enrolls it in spaced repetition
		loadTimings(item.id).then((t) => (timings = t));
	});

	/** highlight the word under the playhead until paused/ended. `offset` maps a
	    part clip's local time back onto the phrase timeline (parts start at 0). */
	function runTick(a, marks, offset = 0) {
		const tick = () => {
			const t = a.currentTime + offset;
			hot = marks.findIndex(([s, e]) => t >= s && t <= e + 0.05);
			if (!a.paused && !a.ended) raf = requestAnimationFrame(tick);
			else hot = -1;
		};
		raf = requestAnimationFrame(tick);
	}

	function playPhrase(speed) {
		clearHL();
		const a = play(phraseAudio(item.id, speed));
		const marks = timings?.[speed];
		if (marks) runTick(a, marks);
	}

	/** play one sense-part: its own clip, words still highlighting within */
	function playSegment(i, speed = 'normal') {
		clearHL();
		const s = segs[i];
		const marks = timings?.[speed];
		if (!s || !marks) return;
		const a = play(segmentAudio(item.id, i, speed));
		runTick(a, marks, s[speed][0]);
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
	{#if segs.length}
		<p class="crumb center">{part ? `Parte ${seg + 1} de ${segs.length}` : 'A frase completa'}{item.title ? ` · ${item.title}` : ''}</p>
	{:else}
		<p class="eyebrow center">{item.kind === 'letter' ? 'Nova letra' : 'Nova frase'}</p>
	{/if}
	<Mascot {mood} size={64} />
	{#if speaker}
		<p class="speaker">{speaker}</p>
	{/if}

	<div class="lines">
		<div class="words" class:big={item.kind === 'letter'}>
			{#each wrange as i}
				<button class="wcol" class:hot={hot === i} onclick={() => playWord(i)}>
					<span class="el greek">{item.words[i].el}</span>
					{#if !faded}<span class="tl">{item.words[i].tl}</span>{/if}
				</button>
			{/each}
		</div>
		{#if faded}
			<button class="peek" onclick={() => (peek = true)}
				title="Você já domina esta frase — a transliteração se despediu. Toque para espiar.">Aa</button>
		{/if}
		{#if part}
			<div class="ptrow">
				{#each wrange as wi}
					<button class="pw" class:hot={hot === wi} onclick={() => playWord(wi)}
						title="Ouvir a palavra grega">{item.words[wi].pt}</button>
				{/each}
			</div>
		{:else if segs.length}
			<div class="parts">
				{#each segs as s, si}
					<div class="part" class:hot={hotSeg === si}>
						<button class="partplay" onclick={() => playSegment(si)} aria-label="Ouvir esta parte">
							<svg width="9" height="11" viewBox="0 0 9 11"><path d="M0 0 L9 5.5 L0 11 Z" fill="currentColor" /></svg>
						</button>
						{#each segWords(s) as wi}
							<button class="pw" class:hot={hot === wi} onclick={() => playWord(wi)}
								title="Ouvir a palavra grega">{item.words[wi].pt}</button>
						{/each}
					</div>
				{/each}
			</div>
		{:else}
			<p class="pt">{item.pt}</p>
		{/if}
	</div>

	{#if item.gloss?.length && item.kind !== 'letter' && !segs.length}
		<div class="gloss">
			{#each item.gloss as g}
				<span class="g"><b class="greek">{g.el}</b> · {g.pt}</span>
			{/each}
		</div>
	{/if}

	<div class="controls">
		<button class="playbtn" onclick={() => (part ? playSegment(seg) : playPhrase('normal'))} aria-label="Ouvir">
			<svg width="18" height="20" viewBox="0 0 20 22"><path d="M2 2 L18 11 L2 20 Z" fill="#241c08" /></svg>
		</button>
		<button class="slowbtn" onclick={() => (part ? playSegment(seg, 'slow') : playPhrase('slow'))}>lento</button>
	</div>

	{#if item.context_pt && !part}
		<p class="ctx">{item.context_pt}</p>
	{/if}
	{#if item.source && !part}
		<p class="src">{item.source}</p>
	{/if}

	<div class="continue">
		<button class="btn" onclick={onDone}>Continuar</button>
	</div>
</section>

<style>
	.center { text-align: center; }
	/* breadcrumb for a segmented phrase: "Parte 1 de 3 · a bênção de abertura" */
	.crumb { font-size: 12px; color: var(--gold2); letter-spacing: 0.02em; margin: 0 0 6px; }
	.speaker {
		text-align: center; font-size: 11.5px; color: var(--gold2);
		border: 1px solid var(--line); border-radius: 999px;
		width: fit-content; margin: 6px auto 0; padding: 2px 12px;
	}
	.lines { margin: 10px 0 4px; }
	/* each word is a column: Greek with its reading tucked beneath, so the two
	   fuse into one block instead of two separate wrapping rows */
	.words { display: flex; flex-wrap: wrap; gap: 1px 4px; justify-content: center; align-items: flex-start; }
	.wcol {
		display: inline-flex; flex-direction: column; align-items: center;
		background: none; border: 0; color: inherit; font: inherit;
		cursor: pointer; border-radius: 8px; padding: 1px 4px 2px;
		transition: background 0.12s, color 0.12s;
	}
	.wcol .el { font-size: 23px; line-height: 1.12; }
	.words.big .wcol .el { font-size: 42px; }
	.wcol .tl { font-size: 11px; font-style: italic; color: var(--dim); line-height: 1.05; margin-top: 1px; }
	.wcol:hover { background: var(--raised); }
	.wcol.hot { background: var(--gold); color: #241c08; }
	.wcol.hot .tl { color: #241c08; }
	.pt { text-align: center; font-size: 15px; margin: 10px 0 0; }
	/* when a phrase is broken into parts, the parts carry the meaning (the full
	   translation line is dropped as redundant) */
	/* part mode: the single part's per-word pt, tappable (no chip container) */
	.ptrow { display: flex; flex-wrap: wrap; gap: 2px 4px; justify-content: center; margin: 12px 0 0; }
	.parts { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin: 12px 0 0; }
	.part {
		display: inline-flex; flex-wrap: wrap; align-items: center; gap: 1px;
		background: var(--raised); border: 1px solid var(--line);
		border-radius: 10px; padding: 2px 6px 2px 4px;
		transition: border-color 0.12s;
	}
	.part.hot { border-color: var(--gold2); }
	.partplay {
		display: inline-grid; place-items: center; width: 18px; height: 18px;
		border: 0; background: none; color: var(--gold2); cursor: pointer; padding: 0;
	}
	.pw {
		background: none; border: 0; color: var(--parch); font: inherit; font-size: 13px;
		cursor: pointer; border-radius: 6px; padding: 1px 5px; white-space: nowrap;
		transition: background 0.12s, color 0.12s;
	}
	.pw:hover { background: var(--nave); }
	.pw.hot { background: var(--gold); color: #241c08; }
	.peek {
		display: block; margin: 6px auto 0; font-size: 11px; background: none;
		border: 1px dashed var(--line); color: var(--dim); border-radius: 999px;
		padding: 2px 10px; cursor: pointer;
	}
	.gloss { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 12px 0 0; }
	.g {
		font-size: 12px;
		color: var(--dim);
		border: 1px dashed var(--line);
		border-radius: 10px;
		padding: 4px 9px;
	}
	.g b { color: var(--parch); font-weight: 500; font-size: 13px; }
	.controls { display: flex; gap: 12px; justify-content: center; align-items: center; margin: 12px 0; }
	.playbtn {
		width: 48px;
		height: 48px;
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
	.ctx { font-size: 12px; color: var(--dim); text-align: center; margin: 0 0 4px; line-height: 1.4; }
	.src { font-size: 11px; color: var(--dim); text-align: center; opacity: 0.7; margin: 0 0 10px; }
	/* pin Continuar to the bottom so it's reachable on any phrase length; the
	   card content scrolls under a fade of the page background */
	.continue {
		position: sticky; bottom: 0; margin-top: 12px;
		padding: 10px 0 max(6px, env(safe-area-inset-bottom));
		background: linear-gradient(to top, var(--night) 62%, transparent);
	}
</style>
