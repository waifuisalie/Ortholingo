<script>
	import { goto } from '$app/navigation';
	import { dueIds, rate } from '$lib/srs.svelte.js';
	import { stop } from '$lib/audio.js';
	import QuizCard from '$lib/components/QuizCard.svelte';
	import Mascot from '$lib/components/Mascot.svelte';

	let { data } = $props();
	const manifest = data.manifest;

	const SESSION_MAX = 10;

	function shuffle(arr) {
		const a = [...arr];
		for (let i = a.length - 1; i > 0; i--) {
			const j = Math.floor(Math.random() * (i + 1));
			[a[i], a[j]] = [a[j], a[i]];
		}
		return a;
	}

	function buildSteps() {
		const due = dueIds()
			.filter((id) => manifest.items[id])
			.slice(0, SESSION_MAX);
		const pool = Object.entries(manifest.items).map(([id, it]) => ({ id, ...it }));
		return due.map((id, i) => {
			const item = { id, ...manifest.items[id] };
			const others = shuffle(pool.filter((x) => x.id !== id && x.kind === item.kind)).slice(0, 3);
			const isLetter = item.kind === 'letter';
			const listen = isLetter || i % 2 === 0;
			const mk = (x) => ({
				id: x.id,
				label: listen ? (isLetter ? x.greek : x.pt) : x.greek,
				sub: listen && isLetter ? x.words[0].tl : null
			});
			return {
				type: listen ? 'listen-choose' : 'choose-greek',
				item,
				options: shuffle([mk(item), ...others.map(mk)]),
				answer: id
			};
		});
	}

	const steps = buildSteps();
	let idx = $state(0);
	let hits = $state(0);
	let done = $state(steps.length === 0);

	const step = $derived(steps[idx]);
	const pct = $derived(done ? 100 : Math.round((idx / steps.length) * 100));

	function onResult(ok) {
		if (ok) hits += 1;
		rate(steps[idx].item.id, ok);
	}

	function advance() {
		stop();
		if (idx + 1 < steps.length) idx += 1;
		else done = true;
	}

	function exit() {
		stop();
		goto('/');
	}
</script>

{#if done}
	<section class="donebox">
		{#if steps.length === 0}
			<p class="eyebrow">Revisão</p>
			<Mascot mood="content" size={120} />
			<p class="msg">Nada para revisar agora — a memória descansa. Volte mais tarde, ou avance no caminho.</p>
		{:else}
			<p class="eyebrow">Revisão concluída</p>
			<Mascot mood="wave" size={120} />
			<p class="msg">{hits} de {steps.length} — cada acerto empurra a próxima revisão para mais longe.</p>
		{/if}
		<button class="btn" onclick={exit}>Voltar ao caminho</button>
	</section>
{:else}
	<div class="bar">
		<button class="close" onclick={exit} aria-label="Sair da revisão">×</button>
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
