"""WebSocket connection manager with Redis pub/sub for cross-worker routing."""

import asyncio
import contextlib
import json
import uuid

import redis.asyncio as redis
import structlog
from starlette.websockets import WebSocket, WebSocketState

logger = structlog.get_logger()


class ConnectionManager:
    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis = redis_client
        self._worker_id = str(uuid.uuid4())
        self._local: dict[str, dict[str, WebSocket]] = {}
        self._pubsub: redis.client.PubSub | None = None
        self._subscribed_channels: set[str] = set()
        self._listener_task: asyncio.Task | None = None
        self._heartbeat_tasks: dict[str, asyncio.Task] = {}

    async def start(self) -> None:
        self._pubsub = self.redis.pubsub()
        self._listener_task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        if self._listener_task:
            self._listener_task.cancel()
        for task in self._heartbeat_tasks.values():
            task.cancel()
        if self._pubsub:
            await self._pubsub.close()

    async def connect(self, game_id: str, user_id: str, ws: WebSocket) -> None:
        if game_id not in self._local:
            self._local[game_id] = {}

        old_ws = self._local[game_id].get(user_id)
        if old_ws and old_ws.client_state == WebSocketState.CONNECTED:
            with contextlib.suppress(Exception):
                await old_ws.close(code=1000, reason="Replaced by new connection")

        self._local[game_id][user_id] = ws

        channel = f"multiplayer:{game_id}"
        if channel not in self._subscribed_channels and self._pubsub:
            await self._pubsub.subscribe(channel)
            self._subscribed_channels.add(channel)

        hb_key = f"{game_id}:{user_id}"
        if hb_key in self._heartbeat_tasks:
            self._heartbeat_tasks[hb_key].cancel()
        self._heartbeat_tasks[hb_key] = asyncio.create_task(
            self._heartbeat(game_id, user_id, ws)
        )

    async def disconnect(self, game_id: str, user_id: str, ws: WebSocket) -> bool:
        if game_id not in self._local:
            return False

        stored = self._local[game_id].get(user_id)
        if stored is not ws:
            return False

        hb_key = f"{game_id}:{user_id}"
        if hb_key in self._heartbeat_tasks:
            self._heartbeat_tasks[hb_key].cancel()
            del self._heartbeat_tasks[hb_key]

        del self._local[game_id][user_id]
        if not self._local[game_id]:
            del self._local[game_id]
            channel = f"multiplayer:{game_id}"
            if channel in self._subscribed_channels and self._pubsub:
                await self._pubsub.unsubscribe(channel)
                self._subscribed_channels.discard(channel)

        return True

    async def broadcast(
        self, game_id: str, message: dict, *, exclude: str | None = None
    ) -> None:
        payload = json.dumps(message)

        if game_id in self._local:
            for uid, ws in list(self._local[game_id].items()):
                if uid == exclude:
                    continue
                await self._safe_send(ws, payload)

        try:
            await self.redis.publish(
                f"multiplayer:{game_id}",
                json.dumps(
                    {"_origin": self._worker_id, "_exclude": exclude, **message}
                ),
            )
        except Exception:
            logger.error("redis_publish_failed", game_id=game_id)

    async def send_to_player(self, game_id: str, user_id: str, message: dict) -> None:
        payload = json.dumps(message)

        if game_id in self._local and user_id in self._local[game_id]:
            await self._safe_send(self._local[game_id][user_id], payload)
            return

        try:
            await self.redis.publish(
                f"multiplayer:{game_id}",
                json.dumps({"_origin": self._worker_id, "_target": user_id, **message}),
            )
        except Exception:
            logger.error("redis_publish_failed", game_id=game_id, target=user_id)

    def get_local_connections(self, game_id: str) -> dict[str, WebSocket]:
        return dict(self._local.get(game_id, {}))

    def has_local_connection(self, game_id: str, user_id: str) -> bool:
        return game_id in self._local and user_id in self._local[game_id]

    async def _safe_send(self, ws: WebSocket, data: str) -> None:
        try:
            if ws.client_state == WebSocketState.CONNECTED:
                await ws.send_text(data)
        except Exception:
            pass

    async def _listen(self) -> None:
        if not self._pubsub:
            return
        while True:
            try:
                async for raw_message in self._pubsub.listen():
                    if raw_message["type"] != "message":
                        continue
                    try:
                        data = json.loads(raw_message["data"])
                    except (json.JSONDecodeError, TypeError):
                        continue

                    if data.pop("_origin", None) == self._worker_id:
                        continue

                    channel = raw_message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode()
                    game_id = channel.replace("multiplayer:", "")

                    target = data.pop("_target", None)
                    exclude = data.pop("_exclude", None)

                    if target:
                        if game_id in self._local and target in self._local[game_id]:
                            await self._safe_send(
                                self._local[game_id][target], json.dumps(data)
                            )
                    elif game_id in self._local:
                        payload = json.dumps(data)
                        for uid, ws in list(self._local[game_id].items()):
                            if uid == exclude:
                                continue
                            await self._safe_send(ws, payload)
            except asyncio.CancelledError:
                return
            except Exception:
                logger.exception("pubsub_listener_error")
                await asyncio.sleep(1)

    async def _heartbeat(self, game_id: str, user_id: str, ws: WebSocket) -> None:
        try:
            while True:
                await asyncio.sleep(15)
                if ws.client_state != WebSocketState.CONNECTED:
                    break
                try:
                    await asyncio.wait_for(ws.send_json({"type": "ping"}), timeout=10)
                except (TimeoutError, Exception):
                    logger.info("heartbeat_failed", game_id=game_id, user_id=user_id)
                    break
        except asyncio.CancelledError:
            pass
