"""State sync and helper behavior for multiplayer game manager."""

import time

import structlog

from app.domains.multiplayer.events import ServerEvent
from app.domains.multiplayer.game_manager_shared import (
    RATE_LIMIT_MAX,
    RATE_LIMIT_WINDOW,
    READY_ADVANCE_LOCK_TTL_SECONDS,
    READY_BARRIER_TTL_SECONDS,
    iso_utc,
)

logger = structlog.get_logger()


class GameManagerStateMixin:
    def _build_round_result_payload(
        self,
        doc: dict,
        round_index: int,
        *,
        include_forfeited: bool = False,
    ) -> dict:
        rd = doc["rounds"][round_index]
        guesses = rd.get("guesses", {})

        players = (
            doc["players"]
            if include_forfeited
            else [p for p in doc["players"] if p["status"] != "forfeited"]
        )

        results = []
        for p in players:
            g = guesses.get(p["user_id"])
            if g:
                results.append(
                    {
                        "userId": p["user_id"],
                        "name": p["name"],
                        "score": g["score"],
                        "distanceMeters": g["distance_meters"],
                        "guess": {"lat": g["lat"], "lng": g["lng"]},
                    }
                )
            else:
                results.append(
                    {
                        "userId": p["user_id"],
                        "name": p["name"],
                        "score": 0,
                        "distanceMeters": None,
                        "guess": None,
                    }
                )
        results.sort(key=lambda result: result["score"], reverse=True)

        standings = []
        for player in players:
            total_score = 0
            for prior_round in doc["rounds"][: round_index + 1]:
                guess = prior_round.get("guesses", {}).get(player["user_id"])
                if guess:
                    total_score += guess["score"]
            standings.append(
                {
                    "userId": player["user_id"],
                    "name": player["name"],
                    "totalScore": total_score,
                }
            )

        standings.sort(key=lambda standing: standing["totalScore"], reverse=True)
        for i, standing in enumerate(standings):
            standing["rank"] = i + 1

        return {
            "round": round_index + 1,
            "results": results,
            "actual": {"lat": rd["actual_lat"], "lng": rd["actual_lng"]},
            "locationName": rd.get("location_name"),
            "standings": standings,
        }

    async def _send_game_state(self, game_id: str, user_id: str, doc: dict) -> None:
        current_round = doc.get("current_round", 0)
        round_index = current_round - 1

        round_data = None
        players_guessed: list[str] = []
        has_guessed = False
        previous_rounds: list[dict] = []

        if 0 <= round_index < len(doc["rounds"]):
            rd = doc["rounds"][round_index]
            if not rd.get("_resolved"):
                round_data = {
                    "round": current_round,
                    "imageUrl": rd["image_url"],
                    "expiresAt": iso_utc(rd["expires_at"])
                    if rd.get("expires_at")
                    else None,
                }
                guesses = rd.get("guesses", {})
                players_guessed = list(guesses.keys())
                has_guessed = user_id in guesses

        for i, rd in enumerate(doc["rounds"]):
            if i > round_index:
                break
            if rd.get("_resolved"):
                previous_rounds.append(
                    self._build_round_result_payload(doc, i, include_forfeited=True)
                )

        players = [
            {
                "userId": p["user_id"],
                "name": p["name"],
                "status": p["status"],
                "totalScore": p.get("total_score", 0),
            }
            for p in doc["players"]
        ]

        ready_players = [
            p["user_id"]
            for p in doc["players"]
            if p["status"] == "connected"
            and p["user_id"] in self._lobby_ready.get(game_id, set())
        ]

        await self.cm.send_to_player(
            game_id,
            user_id,
            {
                "type": ServerEvent.GAME_STATE,
                "status": doc["status"],
                "currentRound": current_round,
                "totalRounds": len(doc["rounds"]),
                "round": round_data,
                "playersGuessed": players_guessed,
                "hasGuessedThisRound": has_guessed,
                "players": players,
                "readyPlayers": ready_players,
                "previousRounds": previous_rounds,
            },
        )

    def _ready_barrier_key(self, game_id: str, round_number: int) -> str:
        return f"mp:ready:{game_id}:{round_number}"

    def _ready_barrier_lock_key(self, game_id: str, round_number: int) -> str:
        return f"mp:ready-lock:{game_id}:{round_number}"

    async def _mark_player_ready_for_next_round(
        self,
        game_id: str,
        round_number: int,
        user_id: str,
    ) -> None:
        ready_key = self._ready_barrier_key(game_id, round_number)
        await self.redis.sadd(ready_key, user_id)
        await self.redis.expire(ready_key, READY_BARRIER_TTL_SECONDS)

    async def _clear_ready_barrier_for_round(
        self,
        game_id: str,
        round_number: int,
    ) -> None:
        await self.redis.delete(
            self._ready_barrier_key(game_id, round_number),
            self._ready_barrier_lock_key(game_id, round_number),
        )

    async def _clear_all_ready_barriers(self, game_id: str) -> None:
        keys: list[str] = []
        async for key in self.redis.scan_iter(match=f"mp:ready:{game_id}:*"):
            keys.append(key)
        async for key in self.redis.scan_iter(match=f"mp:ready-lock:{game_id}:*"):
            keys.append(key)
        if keys:
            await self.redis.delete(*keys)

    async def _maybe_advance_ready_barrier(
        self,
        game_id: str,
        doc: dict | None,
    ) -> None:
        if not doc:
            doc = await self._load(game_id)

        if not doc or doc["status"] != "active":
            return

        round_number = doc.get("current_round", 0)
        round_index = round_number - 1
        if round_index < 0 or round_index >= len(doc["rounds"]):
            return

        round_data = doc["rounds"][round_index]
        if not round_data.get("_resolved"):
            return

        next_round_index = round_index + 1
        if next_round_index >= len(doc["rounds"]):
            return

        required_ready_players = {
            p["user_id"] for p in doc["players"] if p["status"] == "connected"
        }
        if not required_ready_players:
            return

        ready_key = self._ready_barrier_key(game_id, round_number)
        ready_players = set(await self.redis.smembers(ready_key))
        ready_count = len(ready_players & required_ready_players)

        logger.info(
            "ready_barrier_evaluated",
            game_id=game_id,
            round=round_number,
            required_count=len(required_ready_players),
            ready_count=ready_count,
            worker_id=self.cm.worker_id,
        )

        if not ready_players >= required_ready_players:
            return

        lock_key = self._ready_barrier_lock_key(game_id, round_number)
        acquired = await self.redis.set(
            lock_key,
            self.cm.worker_id,
            ex=READY_ADVANCE_LOCK_TTL_SECONDS,
            nx=True,
        )
        if not acquired:
            logger.info(
                "ready_barrier_lock_not_acquired",
                game_id=game_id,
                round=round_number,
                worker_id=self.cm.worker_id,
            )
            return

        logger.info(
            "ready_barrier_lock_acquired",
            game_id=game_id,
            round=round_number,
            worker_id=self.cm.worker_id,
        )

        fresh = await self._load(game_id)
        if not fresh or fresh["status"] != "active":
            await self._clear_ready_barrier_for_round(game_id, round_number)
            return

        fresh_round_number = fresh.get("current_round", 0)
        fresh_round_index = fresh_round_number - 1
        if fresh_round_number != round_number:
            await self._clear_ready_barrier_for_round(game_id, round_number)
            return

        if (
            fresh_round_index < 0
            or fresh_round_index >= len(fresh["rounds"])
            or not fresh["rounds"][fresh_round_index].get("_resolved")
        ):
            await self.redis.delete(lock_key)
            return

        await self._start_round(game_id, next_round_index)
        await self._clear_ready_barrier_for_round(game_id, round_number)

        logger.info(
            "ready_barrier_round_advanced",
            game_id=game_id,
            round=round_number,
            next_round=next_round_index + 1,
            worker_id=self.cm.worker_id,
        )

    async def _load(self, game_id: str) -> dict | None:
        doc = await self.repo.find_by_id(game_id)
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def _check_rate_limit(self, key: str) -> bool:
        now = time.monotonic()
        if key not in self._rate_limits:
            self._rate_limits[key] = []

        timestamps = self._rate_limits[key]
        cutoff = now - RATE_LIMIT_WINDOW
        self._rate_limits[key] = [t for t in timestamps if t > cutoff]

        if len(self._rate_limits[key]) >= RATE_LIMIT_MAX:
            return False

        self._rate_limits[key].append(now)
        return True
