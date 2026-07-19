/** Builds the step list for one lesson from manifest items.
 *
 * Shape per step:
 *   { type: 'karaoke', item }
 *   { type: 'listen-choose', item, options: [{id, label, sub}], answer }
 *   { type: 'choose-greek', item, options: [...], answer }
 *   { type: 'match', pairs: [{id, el, pt}] }
 */
import { lessonChunks } from '$lib/content.js';

function shuffle(arr) {
	const a = [...arr];
	for (let i = a.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[a[i], a[j]] = [a[j], a[i]];
	}
	return a;
}

function pickOthers(all, item, n) {
	return shuffle(all.filter((x) => x.id !== item.id)).slice(0, n);
}

function greekLabel(item) {
	return item.greek;
}

/** Options: hear the audio, pick the right Greek (letters) or right PT (phrases). */
function listenChooseStep(item, poolItems) {
	const others = pickOthers(poolItems, item, 3);
	const isLetter = item.kind === 'letter';
	const mk = (x) => ({
		id: x.id,
		label: isLetter ? greekLabel(x) : x.pt,
		sub: isLetter ? x.words[0].tl : null
	});
	const options = shuffle([mk(item), ...others.map(mk)]);
	return { type: 'listen-choose', item, options, answer: item.id };
}

/** Options: see the PT meaning, pick the right Greek. */
function chooseGreekStep(item, poolItems) {
	const others = pickOthers(poolItems, item, 3);
	const mk = (x) => ({ id: x.id, label: greekLabel(x), sub: null });
	const options = shuffle([mk(item), ...others.map(mk)]);
	return { type: 'choose-greek', item, options, answer: item.id };
}

function matchStep(items) {
	const pairs = items.slice(0, 4).map((x) => ({
		id: x.id,
		el: x.kind === 'letter' ? x.greek : x.words[0].el.replace(/[.,·;]$/, ''),
		pt: x.kind === 'letter' ? x.words[0].tl : x.pt
	}));
	return { type: 'match', pairs };
}

export function buildLesson(manifest, unitId, n) {
	const chunk = lessonChunks(manifest, unitId)[n - 1];
	if (!chunk) return null;
	const items = chunk.map((id) => ({ id, ...manifest.items[id] }));
	// pool for wrong answers: whole unit, so early lessons still get 4 options
	const pool = manifest.units
		.find((u) => u.id === unitId)
		.items.map((id) => ({ id, ...manifest.items[id] }));

	const steps = [];
	for (const item of items) steps.push({ type: 'karaoke', item });
	const quizzes = items.map((item, i) =>
		item.kind === 'letter' || i % 2 === 0 ? listenChooseStep(item, pool) : chooseGreekStep(item, pool)
	);
	// phrases get a speak check (skippable, never penalized); letters don't
	for (const item of items) {
		if (item.kind === 'phrase') quizzes.push({ type: 'speak', item });
	}
	steps.push(...shuffle(quizzes));
	if (items.length >= 3) steps.push(matchStep(shuffle(items)));
	return { items, steps };
}
