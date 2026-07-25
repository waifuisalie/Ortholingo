/** Single shared audio player so sounds never overlap. */

let el = null;
let rangeToken = 0; // invalidates any in-flight playRange guard

function ensure() {
	if (!el) el = new Audio();
	return el;
}

/** Play a URL from the start. Returns the element so callers can track currentTime/ended. */
export function play(url) {
	const a = ensure();
	rangeToken++; // cancel any segment guard still watching for an end time
	a.pause();
	a.src = url;
	a.currentTime = 0;
	void a.play().catch(() => {});
	return a;
}

/** Play just [start,end] (seconds) of a URL and auto-pause at end. Seeks only
 *  once metadata is ready — mobile Safari ignores currentTime set too early.
 *  Returns the element so callers can track currentTime for highlighting. */
export function playRange(url, start, end) {
	const a = ensure();
	const my = ++rangeToken;
	a.pause();
	const guard = () => {
		if (my !== rangeToken) return; // superseded by another play/playRange/stop
		if (a.paused || a.ended || a.currentTime >= end) {
			a.pause();
			return;
		}
		requestAnimationFrame(guard);
	};
	const begin = () => {
		if (my !== rangeToken) return;
		try {
			a.currentTime = start;
		} catch {
			/* not seekable yet — guard/end still bounds it */
		}
		void a.play().catch(() => {});
		requestAnimationFrame(guard);
	};
	if (a.src && a.src.indexOf(url) !== -1 && a.readyState >= 1) {
		begin(); // same file already loaded — seek immediately
	} else {
		a.src = url;
		const onMeta = () => {
			a.removeEventListener('loadedmetadata', onMeta);
			begin();
		};
		a.addEventListener('loadedmetadata', onMeta);
		a.load();
	}
	return a;
}

export function stop() {
	rangeToken++; // stop bounding any segment
	if (el) el.pause();
}
