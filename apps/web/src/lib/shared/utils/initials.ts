export function getInitials(name: string): string {
	const words = name.split(" ").filter(Boolean);

	if (words.length >= 2) {
		return `${words[0][0]}${words[words.length - 1][0]}`.toUpperCase();
	}

	if (words.length === 1) {
		return words[0].slice(0, 2).toUpperCase();
	}

	return "?";
}
