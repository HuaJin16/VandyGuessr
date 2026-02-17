export type ResizeTarget = HTMLElement | null | undefined;

export function observeResize(targets: ResizeTarget[], onResize: () => void) {
	const observer = new ResizeObserver(() => onResize());

	for (const target of targets) {
		if (target) {
			observer.observe(target);
		}
	}

	return () => observer.disconnect();
}
