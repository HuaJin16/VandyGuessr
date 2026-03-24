import type { Game, Round } from "./types";

const ROUND_MAX_SCORE = 5000;
const scoreFormatter = new Intl.NumberFormat("en-US");

export function getRoundShareEmoji(round: Round): string {
	if (round.skipped) return "⬜";

	const score = round.score ?? 0;

	if (score >= 4000) return "🟩";
	if (score >= 3000) return "🟨";
	if (score >= 1000) return "🟧";
	return "🟥";
}

export function buildGameShareText(game: Game, appUrl: string): string {
	const maxScore = game.rounds.length * ROUND_MAX_SCORE;
	const emojiGrid = game.rounds.map(getRoundShareEmoji).join("");

	return [
		`VandyGuessr — ${scoreFormatter.format(game.totalScore)} / ${scoreFormatter.format(maxScore)}`,
		emojiGrid,
		`Play at ${appUrl}`,
	].join("\n");
}
