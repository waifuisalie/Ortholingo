<script>
	import { onDestroy } from 'svelte';
	import Mascot from './Mascot.svelte';
	import { play, stop } from '$lib/audio.js';
	import { phraseAudio } from '$lib/content.js';

	/** @type {{ item: any, onResult: (ok: boolean) => void, onDone: () => void }} */
	let { item, onResult, onDone } = $props();

	const PASS = 0.75;
	const MAX_MS = 10000;

	let phase = $state('idle'); // idle | rec | busy | result | error
	let result = $state(null);
	let mood = $state('content');
	let answered = false;
	let recorder = null;
	let chunks = [];
	let timer = null;

	$effect(() => {
		item.id;
		phase = 'idle';
		result = null;
		mood = 'content';
		answered = false;
	});

	async function toggleRec() {
		if (phase === 'rec') return stopRec();
		try {
			stop();
			const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
			chunks = [];
			recorder = new MediaRecorder(stream);
			recorder.ondataavailable = (e) => chunks.push(e.data);
			recorder.onstop = () => {
				stream.getTracks().forEach((t) => t.stop());
				submit(new Blob(chunks, { type: recorder.mimeType }));
			};
			recorder.start();
			phase = 'rec';
			mood = 'surprised';
			timer = setTimeout(stopRec, MAX_MS);
		} catch {
			phase = 'error';
		}
	}

	function stopRec() {
		clearTimeout(timer);
		if (recorder?.state === 'recording') recorder.stop();
	}

	async function submit(blob) {
		phase = 'busy';
		try {
			const form = new FormData();
			form.append('audio', blob, 'take.webm');
			form.append('expected', item.wordkeys.join(' '));
			form.append('lang', item.voice === 'athina' ? 'el' : 'en');
			const res = await fetch('/api/speech/score', { method: 'POST', body: form });
			if (!res.ok) throw new Error();
			result = await res.json();
			phase = 'result';
			const ok = result.score >= PASS;
			mood = ok ? 'happy' : 'sadtear';
			if (!answered) {
				answered = true;
				onResult(ok);
			}
		} catch {
			phase = 'error';
		}
	}

	function retry() {
		result = null;
		phase = 'idle';
		mood = 'content';
	}

	onDestroy(() => {
		clearTimeout(timer);
		if (recorder?.state === 'recording') recorder.stop();
		stop();
	});
</script>

<section>
	<p class="eyebrow center">Agora você</p>
	<Mascot {mood} size={96} />

	<div class="target">
		<div class="gr greek">
			{#each item.words as w, i}
				<span class="w" class:ok={result && result.words[i]} class:err={result && !result.words[i]}>{w.el}</span>
			{/each}
		</div>
		<div class="tl">
			{#each item.words as w, i}
				<span class="w" class:ok={result && result.words[i]} class:err={result && !result.words[i]}>{w.tl}</span>
			{/each}
		</div>
		<button class="hearbtn" onclick={() => play(phraseAudio(item.id, 'slow'))}>ouvir de novo (lento)</button>
	</div>

	{#if phase === 'idle' || phase === 'rec'}
		<button class="recbtn" class:listening={phase === 'rec'} onclick={toggleRec}
			aria-label={phase === 'rec' ? 'Parar gravação' : 'Gravar'}>
			<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
				<rect x="9" y="2.5" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0 0 14 0" /><path d="M12 18v3.5" />
			</svg>
		</button>
		<p class="hint">{phase === 'rec' ? 'Fale a frase… toque para parar' : 'Toque, fale a frase, toque para parar'}</p>
	{:else if phase === 'busy'}
		<p class="hint busy">Ouvindo com atenção…</p>
	{:else if phase === 'error'}
		<p class="hint">Não consegui usar o microfone (ou o servidor está desligado).</p>
	{:else if phase === 'result'}
		<p class="heard">Ouvi: <i class="greek">«{result.transcript || '…silêncio'}»</i></p>
		<p class="score" class:good={result.score >= PASS}>Pronúncia: {Math.round(result.score * 100)}%</p>
		<div class="row">
			<button class="btn ghost half" onclick={retry}>Tentar de novo</button>
			<button class="btn half" onclick={onDone}>Continuar</button>
		</div>
	{/if}

	{#if phase !== 'result'}
		<button class="skip" onclick={onDone}>Agora não — praticar depois (sem penalidade)</button>
	{/if}
</section>

<style>
	.center { text-align: center; }
	.target { margin: 14px 0 4px; }
	.gr, .tl { display: flex; flex-wrap: wrap; gap: 4px 8px; justify-content: center; }
	.gr { font-size: 27px; }
	.tl { font-size: 13.5px; font-style: italic; color: var(--dim); margin-top: 2px; }
	.w { border-radius: 8px; padding: 1px 6px; }
	.w.ok { background: #82a85c26; box-shadow: inset 0 0 0 1.5px var(--good); }
	.w.err { background: #c05a4426; box-shadow: inset 0 0 0 1.5px var(--bad); }
	.hearbtn {
		display: block; margin: 10px auto 0; font-size: 12px; background: none;
		border: 1px solid var(--line); color: var(--gold2); border-radius: 999px;
		padding: 5px 12px; cursor: pointer;
	}
	.recbtn {
		width: 88px; height: 88px; border-radius: 50%; border: 3px solid var(--gold);
		background: var(--nave); color: var(--gold2); display: grid; place-items: center;
		margin: 18px auto 8px; cursor: pointer;
	}
	.recbtn.listening { border-color: var(--bad); color: var(--parch); animation: pulse 1.1s infinite; }
	@keyframes pulse {
		0% { box-shadow: 0 0 0 0 #c05a4455; }
		100% { box-shadow: 0 0 0 22px #c05a4400; }
	}
	.hint { text-align: center; font-size: 12.5px; color: var(--dim); margin: 4px 0 10px; min-height: 19px; }
	.busy { color: var(--gold2); }
	.heard { text-align: center; color: var(--dim); font-size: 13px; margin: 12px 0 2px; }
	.heard i { font-style: normal; color: var(--parch); }
	.score { text-align: center; font-size: 15px; font-weight: 700; color: var(--bad); margin: 0 0 14px; }
	.score.good { color: var(--good); }
	.row { display: flex; gap: 10px; }
	.half { flex: 1; }
	.skip {
		display: block; width: 100%; text-align: center; font-size: 12.5px; color: var(--dim);
		margin-top: 6px; background: none; border: 0; cursor: pointer;
		text-decoration: underline; text-underline-offset: 3px;
	}
</style>
