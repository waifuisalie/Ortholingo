/** Manifest loading and content helpers. */

export const LESSON_SIZE = { nartex: 6, nave: 3 };

export async function loadManifest(fetchFn = fetch) {
	const res = await fetchFn('/assets/manifest.json');
	if (!res.ok) throw new Error('manifest.json não encontrado — rode pipeline/build_assets.py');
	return res.json();
}

export function unitById(manifest, unitId) {
	return manifest.units.find((u) => u.id === unitId);
}

/** Split a unit's items into lesson-sized chunks. Returns [[id,...],...]. */
export function lessonChunks(manifest, unitId) {
	const unit = unitById(manifest, unitId);
	const size = LESSON_SIZE[unit.section] ?? 4;
	const chunks = [];
	for (let i = 0; i < unit.items.length; i += size) {
		chunks.push(unit.items.slice(i, i + size));
	}
	return chunks;
}

export function phraseAudio(id, speed = 'normal') {
	return `/assets/audio/phrases/${id}_${speed}.mp3`;
}

export function wordAudio(key) {
	return `/assets/audio/words/${key}.mp3`;
}

export async function loadTimings(id, fetchFn = fetch) {
	const res = await fetchFn(`/assets/timings/${id}.json`);
	return res.ok ? res.json() : null;
}
