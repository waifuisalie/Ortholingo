/** localStorage-backed progress (device-local for the prototype). */

const KEY = 'ortholingo-progress-v1';

const EMPTY = { lessons: {}, xp: 0, streak: { count: 0, last: null } };

function read() {
	if (typeof localStorage === 'undefined') return structuredClone(EMPTY);
	try {
		const p = JSON.parse(localStorage.getItem(KEY)) ?? {};
		return { ...structuredClone(EMPTY), ...p, streak: p.streak ?? { count: 0, last: null } };
	} catch {
		return structuredClone(EMPTY);
	}
}

export const progress = $state(read());

function dayKey(d) {
	return d.toISOString().slice(0, 10);
}

/** One practice per day keeps the candle lit. Missing days resets silently —
 * no guilt, no crying mascot (ARCHITECTURE D8). */
export function touchStreak() {
	const today = dayKey(new Date());
	if (progress.streak.last === today) return;
	const yesterday = dayKey(new Date(Date.now() - 864e5));
	progress.streak.count = progress.streak.last === yesterday ? progress.streak.count + 1 : 1;
	progress.streak.last = today;
	persist();
}

export function completeLesson(unitId, n, xp = 20) {
	const key = `${unitId}/${n}`;
	if (!progress.lessons[key]) {
		progress.lessons[key] = { at: Date.now(), xp };
		progress.xp += xp;
		persist();
	}
}

export function isDone(unitId, n) {
	return Boolean(progress.lessons[`${unitId}/${n}`]);
}

function persist() {
	try {
		localStorage.setItem(
			KEY,
			JSON.stringify({ lessons: progress.lessons, xp: progress.xp, streak: progress.streak })
		);
	} catch {
		/* quota/private mode: progress lives for the session only */
	}
}
