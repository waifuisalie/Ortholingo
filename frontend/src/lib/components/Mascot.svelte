<script>
	/** @type {{ mood?: 'content'|'happy'|'surprised'|'sadtear'|'wave', size?: number }} */
	let { mood = 'content', size = 110 } = $props();
</script>

<div class="chip" style="width:{size}px; height:{size}px;">
	<img src="/mascot/{mood}.webp" alt="" style="width:{Math.round(size * 0.72)}px;" />
</div>

<style>
	.chip {
		border-radius: 50%;
		background: radial-gradient(circle at 50% 38%, #f2ead8, #d9cbaa);
		display: grid;
		place-items: center;
		overflow: hidden;
		border: 2px solid var(--gold);
		margin: 0 auto;
	}
	img {
		display: block;
		margin-top: 12%;
	}
</style>
