/** localStorage-backed progress (device-local for the prototype). */

const KEY = 'ortholingo-progress-v1';

function read() {
	if (typeof localStorage === 'undefined') return { lessons: {}, xp: 0 };
	try {
		return JSON.parse(localStorage.getItem(KEY)) ?? { lessons: {}, xp: 0 };
	} catch {
		return { lessons: {}, xp: 0 };
	}
}

export const progress = $state(read());

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
		localStorage.setItem(KEY, JSON.stringify({ lessons: progress.lessons, xp: progress.xp }));
	} catch {
		/* quota/private mode: progress lives for the session only */
	}
}
