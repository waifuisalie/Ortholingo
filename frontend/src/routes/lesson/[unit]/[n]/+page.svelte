<script>
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { buildLesson } from '$lib/lesson.js';
	import { completeLesson } from '$lib/progress.svelte.js';
	import { rate } from '$lib/srs.svelte.js';
	import { stop } from '$lib/audio.js';
	import KaraokeCard from '$lib/components/KaraokeCard.svelte';
	import QuizCard from '$lib/components/QuizCard.svelte';
	import MatchPairs from '$lib/components/MatchPairs.svelte';
	import SpeakCheck from '$lib/components/SpeakCheck.svelte';
	import Mascot from '$lib/components/Mascot.svelte';

	let { data } = $props();
	const unitId = page.params.unit;
	const n = Number(page.params.n);
	const lesson = buildLesson(data.manifest, unitId, n);

	let idx = $state(0);
	let hits = $state(0);
	let done = $state(false);

	const total = lesson ? lesson.steps.length : 0;
	const step = $derived(lesson?.steps[idx]);
	const pct = $derived(done ? 100 : Math.round((idx / total) * 100));

	function onResult(ok) {
		if (ok) hits += 1;
		const s = lesson.steps[idx];
		if (s.type === 'match') for (const p of s.pairs) rate(p.id, ok);
		else if (s.item) rate(s.item.id, ok);
	}

	function advance() {
		stop();
		if (idx + 1 < total) {
			idx += 1;
		} else {
			done = true;
			completeLesson(unitId, n);
		}
	}

	function exit() {
		stop();
		goto('/');
	}
</script>

{#if !lesson}
	<p>Lição não encontrada.</p>
	<button class="btn ghost" onclick={exit}>Voltar</button>
{:else if done}
	<section class="donebox">
		<p class="eyebrow">Lição concluída</p>
		<Mascot mood="wave" size={130} />
		<p class="xp">+20 <small>XP</small></p>
		<p class="score">Você acertou {hits} de {lesson.items.length + (lesson.steps.some((s) => s.type === 'match') ? 1 : 0)} exercícios.</p>
		<button class="btn" onclick={exit}>Voltar ao caminho</button>
	</section>
{:else}
	<div class="bar">
		<button class="close" onclick={exit} aria-label="Sair da lição">×</button>
		<div class="prog"><i style="width:{pct}%"></i></div>
	</div>

	{#key idx}
		{#if step.type === 'karaoke'}
			<KaraokeCard item={step.item} onDone={advance} />
		{:else if step.type === 'speak'}
			<SpeakCheck item={step.item} {onResult} onDone={advance} />
		{:else if step.type === 'match'}
			<MatchPairs {step} {onResult} onDone={advance} />
		{:else}
			<QuizCard {step} {onResult} onDone={advance} />
		{/if}
	{/key}
{/if}

<style>
	.bar { display: flex; align-items: center; gap: 12px; padding: 2px 0 14px; }
	.close {
		background: none; border: 0; color: var(--dim);
		font-size: 22px; cursor: pointer; padding: 2px 6px; line-height: 1;
	}
	.prog { flex: 1; height: 8px; border-radius: 99px; background: #2a3557; overflow: hidden; }
	.prog i { display: block; height: 100%; background: var(--gold); border-radius: 99px; transition: width 0.4s; }
	.donebox { text-align: center; padding-top: 30px; }
	.xp {
		font-family: var(--serif); font-size: 40px; color: var(--gold2);
		margin: 14px 0 2px; font-variant-numeric: tabular-nums;
	}
	.xp small {
		font-family: var(--sans); font-size: 11px; letter-spacing: 0.16em;
		text-transform: uppercase; color: var(--dim); display: block;
	}
	.score { color: var(--dim); font-size: 14px; margin: 6px 0 24px; }
</style>
