"""Connection lifecycle behavior for multiplayer game manager."""

import asyncio
from datetime import UTC, datetime, timedelta

from app.domains.multiplayer.events import ServerEvent
from app.domains.multiplayer.game_manager_shared import (
    RECONNECT_TIMEOUT_SECONDS,
    iso_utc,
)


class GameManagerLifecycleMixin:
    async def on_player_connected(self, game_id: str, user_id: str) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        player = next((p for p in doc["players"] if p["user_id"] == user_id), None)
        if not player:
            return

        reconnect_key = f"{game_id}:{user_id}"
        if reconnect_key in self._reconnect_tasks:
            self._reconnect_tasks[reconnect_key].cancel()
            del self._reconnect_tasks[reconnect_key]

        if player.get("status") == "disconnected":
            await self.repo.update_player(
                game_id,
                user_id,
                {
                    "status": "connected",
                    "disconnected_at": None,
                },
            )

            await self.cm.broadcast(
                game_id,
                {
                    "type": ServerEvent.PLAYER_RECONNECTED,
                    "userId": user_id,
                },
                exclude=user_id,
            )

        abandon_key = game_id
        if abandon_key in self._abandon_tasks:
            self._abandon_tasks[abandon_key].cancel()
            del self._abandon_tasks[abandon_key]

        if doc["status"] in ("active", "waiting"):
            await self._send_game_state(game_id, user_id, doc)

        if doc["status"] == "waiting" and game_id not in self._lobby_tasks:
            self._lobby_tasks[game_id] = asyncio.create_task(
                self._lobby_expiry_watcher(game_id, doc["invite_code"], doc["host_id"])
            )

    async def on_player_disconnected(self, game_id: str, user_id: str) -> None:
        doc = await self._load(game_id)
        if not doc:
            return

        player = next((p for p in doc["players"] if p["user_id"] == user_id), None)
        if not player:
            return

        if player["status"] == "forfeited":
            return

        if player["status"] == "disconnected":
            return

        if self.cm.has_local_connection(game_id, user_id):
            return

        if doc["status"] == "waiting":
            lobby_ready = self._lobby_ready.setdefault(game_id, set())
            if user_id in lobby_ready:
                lobby_ready.discard(user_id)
                await self.cm.broadcast(
                    game_id,
                    {
                        "type": ServerEvent.PLAYER_UNREADY,
                        "userId": user_id,
                    },
                )

        await self.repo.update_player(
            game_id,
            user_id,
            {
                "status": "disconnected",
                "disconnected_at": datetime.now(UTC),
            },
        )

        updated_doc = await self._load(game_id)
        await self._maybe_release_ready_event(game_id, updated_doc)

        deadline = datetime.now(UTC) + timedelta(seconds=RECONNECT_TIMEOUT_SECONDS)

        await self.cm.broadcast(
            game_id,
            {
                "type": ServerEvent.PLAYER_DISCONNECTED,
                "userId": user_id,
                "reconnectDeadline": iso_utc(deadline),
            },
        )

        reconnect_key = f"{game_id}:{user_id}"
        self._reconnect_tasks[reconnect_key] = asyncio.create_task(
            self._reconnect_timeout(game_id, user_id)
        )

        fresh = await self._load(game_id)
        active_players = [
            p for p in (fresh["players"] if fresh else []) if p["status"] != "forfeited"
        ]
        if (
            fresh
            and fresh["status"] == "active"
            and active_players
            and all(p["status"] == "disconnected" for p in active_players)
            and game_id not in self._abandon_tasks
        ):
            self._abandon_tasks[game_id] = asyncio.create_task(
                self._abandon_timeout(game_id)
            )
