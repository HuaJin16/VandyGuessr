import type { Round } from "./types";

const ROUND_MAX = 5000;

export interface ScoreQuality {
	word: string;
	color: string;
}

export function getRoundQuality(score: number | null): ScoreQuality {
	if (score === null) return { word: "Skipped", color: "var(--muted)" };
	if (score >= ROUND_MAX) return { word: "Perfect!", color: "var(--brand)" };
	if (score >= 4000) return { word: "Incredible!", color: "var(--brand)" };
	if (score >= 3000) return { word: "Great!", color: "var(--brand)" };
	if (score >= 2000) return { word: "Good", color: "var(--gold-dark)" };
	if (score >= 1000) return { word: "Not bad", color: "var(--gold-dark)" };
	return { word: "Way off", color: "var(--danger)" };
}

export function getGameQuality(
	totalScore: number,
	roundCount: number,
): ScoreQuality & { confetti: boolean } {
	const max = roundCount * ROUND_MAX;
	if (totalScore >= max) return { word: "Flawless!", color: "var(--brand)", confetti: true };
	if (totalScore >= max * 0.8)
		return { word: "Amazing Game!", color: "var(--brand)", confetti: true };
	if (totalScore >= max * 0.64)
		return { word: "Great Game!", color: "var(--brand)", confetti: false };
	if (totalScore >= max * 0.48)
		return { word: "Good Game", color: "var(--gold-dark)", confetti: false };
	if (totalScore >= max * 0.32)
		return { word: "Keep Going", color: "var(--gold-dark)", confetti: false };
	return { word: "Better Luck Next Time", color: "var(--muted)", confetti: false };
}

export function getBarColor(score: number | null): string {
	if (score === null) return "var(--line)";
	if (score >= 4000) return "var(--brand)";
	if (score >= 2000) return "var(--gold)";
	if (score >= 1000) return "var(--line-strong)";
	return "var(--danger)";
}

export function formatDistance(meters: number | null): string {
	if (meters === null) return "\u2014";
	if (meters < 1000) return `${Math.round(meters)}m`;
	return `${(meters / 1000).toFixed(1)}km`;
}

export function computeTimeTaken(round: Round): string {
	if (!round.startedAt) return "\u2014";
	const start = new Date(round.startedAt).getTime();
	const end = round.guessedAt ? new Date(round.guessedAt).getTime() : Date.now();
	const diffMs = Math.max(0, end - start);
	const totalSec = Math.floor(diffMs / 1000);
	const mins = String(Math.floor(totalSec / 60)).padStart(2, "0");
	const secs = String(totalSec % 60).padStart(2, "0");
	return `${mins}:${secs}`;
}
