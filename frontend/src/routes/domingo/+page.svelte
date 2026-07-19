<script>
	import { goto } from '$app/navigation';
	import { isKnown, rate } from '$lib/srs.svelte.js';
	import { touchStreak } from '$lib/progress.svelte.js';
	import { stop } from '$lib/audio.js';
	import QuizCard from '$lib/components/QuizCard.svelte';
	import Mascot from '$lib/components/Mascot.svelte';

	let { data } = $props();
	const manifest = data.manifest;

	const SESSION_MAX = 8;

	function shuffle(arr) {
		const a = [...arr];
		for (let i = a.length - 1; i > 0; i--) {
			const j = Math.floor(Math.random() * (i + 1));
			[a[i], a[j]] = [a[j], a[i]];
		}
		return a;
	}

	let steps = $state(null);
	let idx = $state(0);
	let hits = $state(0);
	let done = $state(false);

	$effect(() => {
		fetch('/assets/liturgy-map.json')
			.then((r) => r.json())
			.then((map) => {
				// the phrases you'll actually say tomorrow, heaviest first
				const refs = map.sections
					.flatMap((s) => s.items)
					.filter((it) => !it.future && isKnown(it.ref))
					.sort((a, b) => b.weight - a.weight)
					.slice(0, SESSION_MAX)
					.map((it) => it.ref);
				const pool = Object.entries(manifest.items)
					.map(([id, it]) => ({ id, ...it }))
					.filter((x) => x.kind === 'phrase');
				steps = refs.map((id, i) => {
					const item = { id, ...manifest.items[id] };
					const others = shuffle(pool.filter((x) => x.id !== id)).slice(0, 3);
					// audio-recognition first: in church you HEAR it before you say it
					const listen = i % 3 !== 2;
					const mk = (x) => ({ id: x.id, label: listen ? x.pt : x.greek, sub: null });
					return {
						type: listen ? 'listen-choose' : 'choose-greek',
						item,
						options: shuffle([mk(item), ...others.map(mk)]),
						answer: id
					};
				});
				done = steps.length === 0;
			});
	});

	const step = $derived(steps?.[idx]);
	const pct = $derived(!steps || done ? 100 : Math.round((idx / steps.length) * 100));

	function onResult(ok) {
		if (ok) hits += 1;
		rate(steps[idx].item.id, ok);
	}

	function advance() {
		stop();
		if (idx + 1 < steps.length) idx += 1;
		else {
			done = true;
			touchStreak();
		}
	}

	function exit() {
		stop();
		goto('/');
	}
</script>

{#if !steps}
	<p class="eyebrow">Preparação para o domingo</p>
{:else if done}
	<section class="donebox">
		{#if steps.length === 0}
			<p class="eyebrow">Preparação para o domingo</p>
			<Mascot mood="content" size={120} />
			<p class="msg">Você ainda não conheceu as respostas da Liturgia — comece pelas lições da Nave, e volte aqui no fim de semana.</p>
		{:else}
			<p class="eyebrow">Pronto para o domingo</p>
			<Mascot mood="wave" size={120} />
			<p class="msg">{hits} de {steps.length}. Amanhã, quando o sacerdote disser as palavras, você vai reconhecê-las. Καλή Κυριακή!</p>
		{/if}
		<button class="btn" onclick={exit}>Voltar ao caminho</button>
	</section>
{:else}
	<div class="bar">
		<button class="close" onclick={exit} aria-label="Sair">×</button>
		<div class="prog"><i style="width:{pct}%"></i></div>
	</div>
	{#key idx}
		<QuizCard {step} {onResult} onDone={advance} />
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
	.msg { color: var(--dim); font-size: 14px; margin: 14px auto 24px; max-width: 34ch; }
</style>
