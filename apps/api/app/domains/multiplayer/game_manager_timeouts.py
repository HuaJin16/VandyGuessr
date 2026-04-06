"""Timeout and cleanup behavior for multiplayer game manager."""

import asyncio
from datetime import UTC, datetime

import structlog

from app.domains.multiplayer.events import ServerEvent
from app.domains.multiplayer.game_manager_shared import (
    ABANDON_TIMEOUT_SECONDS,
    LOBBY_EXPIRY_WARNING_SECONDS,
    RECONNECT_TIMEOUT_SECONDS,
)

logger = structlog.get_logger()


class GameManagerTimeoutsMixin:
    async def cleanup_game(self, game_id: str) -> None:
        self._round_locks.pop(game_id, None)
        for key in [k for k in self._timer_tasks if k.startswith(game_id)]:
            self._timer_tasks[key].cancel()
            del self._timer_tasks[key]
        for key in [k for k in self._reconnect_tasks if k.startswith(game_id)]:
            self._reconnect_tasks[key].cancel()
            del self._reconnect_tasks[key]
        if game_id in self._abandon_tasks:
            self._abandon_tasks[game_id].cancel()
            del self._abandon_tasks[game_id]
        if game_id in self._lobby_tasks:
            self._lobby_tasks[game_id].cancel()
            del self._lobby_tasks[game_id]
        await self._clear_all_ready_barriers(game_id)
        for key in [k for k in self._rate_limits if k.startswith(f"{game_id}:")]:
            del self._rate_limits[key]
        self._lobby_ready.pop(game_id, None)

    async def _reconnect_timeout(self, game_id: str, user_id: str) -> None:
        try:
            await asyncio.sleep(RECONNECT_TIMEOUT_SECONDS)

            doc = await self._load(game_id)
            if not doc:
                return

            player = next((p for p in doc["players"] if p["user_id"] == user_id), None)
            if not player:
                return

            if player["status"] != "disconnected":
                return

            if self.cm.has_local_connection(game_id, user_id):
                return

            if doc["status"] == "waiting":
                if doc["host_id"] == user_id:
                    await self.repo.update_game(game_id, {"status": "cancelled"})
                    await self.cm.broadcast(
                        game_id,
                        {
                            "type": ServerEvent.GAME_CANCELLED,
                            "reason": "Host disconnected",
                        },
                    )
                    await self.cleanup_game(game_id)
                else:
                    await self.repo.remove_player(game_id, user_id)
                    fresh = await self._load(game_id)
                    remaining = (
                        len(fresh["players"])
                        if fresh
                        else max(0, len(doc["players"]) - 1)
                    )
                    await self.cm.broadcast(
                        game_id,
                        {
                            "type": ServerEvent.PLAYER_LEFT,
                            "userId": user_id,
                            "playerCount": remaining,
                        },
                    )
            elif doc["status"] == "active":
                await self.repo.update_player(game_id, user_id, {"status": "forfeited"})
                await self.cm.broadcast(
                    game_id,
                    {
                        "type": ServerEvent.PLAYER_FORFEITED,
                        "userId": user_id,
                    },
                )
                fresh_doc = await self._load(game_id)
                if fresh_doc:
                    await self._check_last_player_standing(game_id, fresh_doc)
                    updated_doc = await self._load(game_id)
                    await self._maybe_advance_ready_barrier(game_id, updated_doc)
        except asyncio.CancelledError:
            pass
        finally:
            reconnect_key = f"{game_id}:{user_id}"
            self._reconnect_tasks.pop(reconnect_key, None)

    async def _abandon_timeout(self, game_id: str) -> None:
        try:
            await asyncio.sleep(ABANDON_TIMEOUT_SECONDS)

            doc = await self._load(game_id)
            if not doc or doc["status"] != "active":
                return

            active_players = [p for p in doc["players"] if p["status"] != "forfeited"]
            if not active_players:
                return
            if any(p["status"] != "disconnected" for p in active_players):
                return

            abandoned = await self.repo.update_game_if_status(
                game_id,
                "active",
                {
                    "status": "abandoned",
                    "last_activity_at": datetime.now(UTC),
                },
            )
            if not abandoned:
                return

            logger.info("game_abandoned", game_id=game_id)
            await self.cleanup_game(game_id)
        except asyncio.CancelledError:
            pass
        finally:
            self._abandon_tasks.pop(game_id, None)

    async def _lobby_expiry_watcher(
        self, game_id: str, invite_code: str, host_id: str
    ) -> None:
        try:
            last_warned_extension = -1
            while True:
                await asyncio.sleep(30)

                doc = await self._load(game_id)
                if not doc or doc["status"] != "waiting":
                    return

                ttl = await self.redis.ttl(f"mp:lobby:{invite_code}")

                if ttl < 0:
                    if doc["status"] == "waiting":
                        await self.repo.update_game(
                            game_id,
                            {
                                "status": "cancelled",
                                "last_activity_at": datetime.now(UTC),
                            },
                        )
                        await self.cm.broadcast(
                            game_id,
                            {
                                "type": ServerEvent.GAME_CANCELLED,
                                "reason": "Lobby expired",
                            },
                        )
                        await self.cleanup_game(game_id)
                    return

                extension_count = doc.get("lobby_extensions", 0)
                if (
                    ttl <= LOBBY_EXPIRY_WARNING_SECONDS
                    and extension_count != last_warned_extension
                ):
                    last_warned_extension = extension_count
                    await self.cm.send_to_player(
                        game_id,
                        host_id,
                        {
                            "type": ServerEvent.LOBBY_EXPIRING,
                        },
                    )
        except asyncio.CancelledError:
            pass
        finally:
            self._lobby_tasks.pop(game_id, None)
