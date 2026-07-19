<script>
	import Mascot from './Mascot.svelte';
	import { play } from '$lib/audio.js';
	import { phraseAudio } from '$lib/content.js';

	/** listen-choose: hear audio, pick label. choose-greek: see PT, pick Greek.
	 * @type {{ step: any, onResult: (ok: boolean) => void, onDone: () => void }} */
	let { step, onResult, onDone } = $props();

	let picked = $state(null);
	let mood = $state('content');
	const isListen = step.type === 'listen-choose';

	$effect(() => {
		step; // new step: reset and (for listen) autoplay once
		picked = null;
		mood = 'content';
		if (isListen) setTimeout(() => play(phraseAudio(step.item.id)), 250);
	});

	function choose(opt) {
		if (picked) return;
		picked = opt.id;
		const ok = opt.id === step.answer;
		mood = ok ? 'happy' : 'sadtear';
		onResult(ok);
	}

	function stateOf(opt) {
		if (!picked) return '';
		if (opt.id === step.answer) return 'right';
		if (opt.id === picked) return 'wrong';
		return '';
	}
</script>

<section>
	<p class="eyebrow center">{isListen ? 'O que você ouviu?' : 'Como se diz em grego?'}</p>
	<Mascot {mood} size={90} />

	{#if isListen}
		<div class="controls">
			<button class="playbtn" onclick={() => play(phraseAudio(step.item.id))} aria-label="Ouvir de novo">
				<svg width="16" height="18" viewBox="0 0 20 22"><path d="M2 2 L18 11 L2 20 Z" fill="#241c08" /></svg>
			</button>
			<button class="slowbtn" onclick={() => play(phraseAudio(step.item.id, 'slow'))}>lento</button>
		</div>
	{:else}
		<p class="prompt">«{step.item.pt}»</p>
	{/if}

	<div class="opts">
		{#each step.options as opt}
			<button class="opt {stateOf(opt)}" class:greek={!isListen || step.item.kind === 'letter'} onclick={() => choose(opt)} disabled={Boolean(picked)}>
				<span>{opt.label}</span>
				{#if opt.sub}<small>{opt.sub}</small>{/if}
			</button>
		{/each}
	</div>

	<p class="verdict" class:ok={picked && picked === step.answer} class:err={picked && picked !== step.answer}>
		{#if picked}
			{picked === step.answer ? 'Isso!' : 'Quase — a resposta certa está em verde.'}
		{/if}
	</p>

	<button class="btn" disabled={!picked} onclick={onDone}>Continuar</button>
</section>

<style>
	.center { text-align: center; }
	.controls { display: flex; gap: 12px; justify-content: center; align-items: center; margin: 14px 0; }
	.playbtn {
		width: 48px; height: 48px; border-radius: 50%; border: 0;
		background: var(--gold); cursor: pointer; display: grid; place-items: center;
	}
	.slowbtn {
		font-size: 12px; border: 1px solid var(--line); color: var(--gold2);
		background: none; border-radius: 999px; padding: 5px 12px; cursor: pointer;
	}
	.prompt { text-align: center; font-size: 17px; margin: 14px 0; }
	.opts { display: flex; flex-direction: column; gap: 10px; margin: 8px 0 4px; }
	.opt {
		font-size: 17px; padding: 12px; border-radius: 16px; text-align: center;
		background: var(--nave); border: 1.5px solid var(--line); color: var(--parch);
		cursor: pointer; display: flex; flex-direction: column; gap: 2px; align-items: center;
		transition: border-color 0.15s;
	}
	.opt.greek { font-family: var(--serif); font-size: 19px; }
	.opt:hover:not(:disabled) { border-color: var(--gold); }
	.opt small { font-size: 11.5px; font-style: italic; color: var(--dim); font-family: var(--sans); }
	.opt.right { border-color: var(--good); background: #82a85c22; }
	.opt.wrong { border-color: var(--bad); background: #c05a4422; }
	.opt:disabled { cursor: default; }
	.verdict { text-align: center; font-size: 13.5px; min-height: 21px; margin: 6px 0 10px; color: var(--dim); }
	.verdict.ok { color: var(--good); }
	.verdict.err { color: var(--bad); }
</style>
