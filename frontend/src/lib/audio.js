/** Single shared audio player so sounds never overlap. */

let el = null;

function ensure() {
	if (!el) el = new Audio();
	return el;
}

/** Play a URL. Returns the element so callers can track currentTime/ended. */
export function play(url) {
	const a = ensure();
	a.pause();
	a.src = url;
	a.currentTime = 0;
	void a.play().catch(() => {});
	return a;
}

export function stop() {
	if (el) el.pause();
}
