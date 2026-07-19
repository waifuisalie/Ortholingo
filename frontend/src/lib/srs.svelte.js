/** Spaced repetition deck: FSRS (ts-fsrs) over localStorage.
 *
 * One card per content item. Exercise results rate cards: correct -> Good,
 * wrong -> Again. Meeting an item (karaoke card) creates its card, so the
 * review queue always knows everything you've been introduced to.
 * Transliteration "training wheels" fade per item once stability crosses
 * FADE_STABILITY_DAYS (ARCHITECTURE D7).
 */
import { fsrs, generatorParameters, createEmptyCard, Rating } from 'ts-fsrs';

const KEY = 'ortholingo-srs-v1';
const FADE_STABILITY_DAYS = 4;

const f = fsrs(generatorParameters({ enable_fuzz: true }));

function load() {
	if (typeof localStorage === 'undefined') return { cards: {} };
	try {
		return JSON.parse(localStorage.getItem(KEY)) ?? { cards: {} };
	} catch {
		return { cards: {} };
	}
}

export const deck = $state(load());

function persist() {
	try {
		localStorage.setItem(KEY, JSON.stringify({ cards: deck.cards }));
	} catch {
		/* private mode: session-only */
	}
}

/** stored (ISO strings) -> live card (Date objects) for ts-fsrs */
function revive(stored) {
	return {
		...stored,
		due: new Date(stored.due),
		last_review: stored.last_review ? new Date(stored.last_review) : undefined
	};
}

export function ensureCard(id) {
	if (!deck.cards[id]) {
		deck.cards[id] = JSON.parse(JSON.stringify(createEmptyCard(new Date())));
		persist();
	}
}

export function rate(id, ok) {
	ensureCard(id);
	const { card } = f.next(revive(deck.cards[id]), new Date(), ok ? Rating.Good : Rating.Again);
	deck.cards[id] = JSON.parse(JSON.stringify(card));
	persist();
}

export function isKnown(id) {
	return Boolean(deck.cards[id]);
}

/** ids due for review right now, oldest due first */
export function dueIds() {
	const now = Date.now();
	return Object.entries(deck.cards)
		.filter(([, c]) => new Date(c.due).getTime() <= now)
		.sort(([, a], [, b]) => new Date(a.due) - new Date(b.due))
		.map(([id]) => id);
}

/** true once the item is mastered enough to drop the transliteration */
export function fadeTranslit(id) {
	const c = deck.cards[id];
	return Boolean(c && c.stability >= FADE_STABILITY_DAYS);
}
