"""Round lifecycle behavior for multiplayer game manager."""

import asyncio
from datetime import UTC, datetime, timedelta

from app.domains.leaderboard.cache import invalidate_leaderboard_cache
from app.domains.multiplayer.events import ServerEvent
from app.domains.multiplayer.game_manager_shared import ROUND_DURATION_SECONDS, iso_utc


class GameManagerRoundsMixin:
    async def _start_round(self, game_id: str, round_index: int) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        if round_index >= len(doc["rounds"]):
            await self._complete_game(game_id)
            return

        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ROUND_DURATION_SECONDS)

        await self.repo.update_round(
            game_id,
            round_index,
            {
                "started_at": now,
                "expires_at": expires_at,
            },
        )
        await self.repo.update_game(
            game_id,
            {
                "current_round": round_index + 1,
                "last_activity_at": now,
            },
        )

        rd = doc["rounds"][round_index]

        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.ROUND_START,
                "round": round_index + 1,
                "totalRounds": len(doc["rounds"]),
                "imageUrl": rd["image_url"],
                "expiresAt": iso_utc(expires_at),
            },
        )

        timer_key = f"{game_id}:round:{round_index}"
        if timer_key in self._timer_tasks:
            self._timer_tasks[timer_key].cancel()
        self._timer_tasks[timer_key] = asyncio.create_task(
            self._round_timer(game_id, round_index, ROUND_DURATION_SECONDS)
        )

    async def _round_timer(
        self, game_id: str, round_index: int, seconds: float
    ) -> None:
        try:
            await asyncio.sleep(seconds)
            await self._try_resolve_round(game_id, round_index)
        except asyncio.CancelledError:
            pass

    async def _try_resolve_round(self, game_id: str, round_index: int) -> None:
        lock = self._get_lock(game_id)
        async with lock:
            doc = await self._load(game_id)
            if not doc or doc["status"] != "active":
                return

            if round_index >= len(doc["rounds"]):
                return

            resolved = await self.repo.mark_round_resolved(game_id, round_index)
            if not resolved:
                return

            timer_key = f"{game_id}:round:{round_index}"
            if timer_key in self._timer_tasks:
                self._timer_tasks[timer_key].cancel()
                del self._timer_tasks[timer_key]

            doc = await self._load(game_id)
            if not doc:
                return
            round_payload = self._build_round_result_payload(doc, round_index)

            await self.cm.broadcast(
                game_id,
                {
                    "type": ServerEvent.ROUND_RESULT,
                    **round_payload,
                },
            )

            await self.repo.update_game(
                game_id, {"last_activity_at": datetime.now(UTC)}
            )

            next_index = round_index + 1
            if next_index >= len(doc["rounds"]):
                await self._complete_game(game_id)

    async def _complete_game(self, game_id: str) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        await self.repo.update_game(
            game_id,
            {
                "status": "completed",
                "last_activity_at": datetime.now(UTC),
            },
        )

        await invalidate_leaderboard_cache(self.redis)

        player_distances: dict[str, float] = {}
        player_times: dict[str, float] = {}
        for p in doc["players"]:
            total_dist = 0.0
            total_time = 0.0
            for rd in doc["rounds"]:
                g = rd.get("guesses", {}).get(p["user_id"])
                if g:
                    total_dist += g.get("distance_meters", 0)
                    if g.get("submitted_at") and rd.get("started_at"):
                        submitted = g["submitted_at"]
                        started = rd["started_at"]
                        if isinstance(submitted, datetime):
                            total_time += (submitted - started).total_seconds()
            player_distances[p["user_id"]] = total_dist
            player_times[p["user_id"]] = total_time

        standings = [
            {
                "userId": p["user_id"],
                "name": p["name"],
                "totalScore": p.get("total_score", 0),
            }
            for p in doc["players"]
        ]
        standings.sort(
            key=lambda s: (
                -s["totalScore"],
                player_distances.get(s["userId"], float("inf")),
                player_times.get(s["userId"], float("inf")),
            )
        )
        for i, s in enumerate(standings):
            s["rank"] = i + 1

        winner_id = standings[0]["userId"] if standings else None

        round_results = []
        for ri, rd in enumerate(doc["rounds"]):
            guesses = rd.get("guesses", {})
            player_results = []
            for p in doc["players"]:
                g = guesses.get(p["user_id"])
                if g:
                    player_results.append(
                        {
                            "userId": p["user_id"],
                            "name": p["name"],
                            "score": g["score"],
                            "distanceMeters": g["distance_meters"],
                            "guess": {"lat": g["lat"], "lng": g["lng"]},
                        }
                    )
                else:
                    player_results.append(
                        {
                            "userId": p["user_id"],
                            "name": p["name"],
                            "score": 0,
                            "distanceMeters": None,
                            "guess": None,
                        }
                    )
            player_results.sort(key=lambda r: r["score"], reverse=True)
            round_results.append(
                {
                    "round": ri + 1,
                    "results": player_results,
                    "actual": {"lat": rd["actual_lat"], "lng": rd["actual_lng"]},
                    "locationName": rd.get("location_name"),
                }
            )

        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.GAME_OVER,
                "winnerId": winner_id,
                "standings": standings,
                "rounds": round_results,
            },
        )

        await self.cleanup_game(game_id)

    async def _check_last_player_standing(self, game_id: str, doc: dict) -> None:
        if doc["status"] != "active":
            return

        active = [p for p in doc["players"] if p["status"] != "forfeited"]
        if len(active) <= 1:
            await self._complete_game(game_id)
