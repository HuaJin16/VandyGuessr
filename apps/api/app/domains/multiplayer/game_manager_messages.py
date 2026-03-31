"""Inbound WebSocket message handling for multiplayer game manager."""

import contextlib
import json

from app.domains.multiplayer.events import ClientEvent, ServerEvent


class GameManagerMessagesMixin:
    async def handle_message(self, game_id: str, user_id: str, raw: str) -> None:
        if not self._check_rate_limit(f"{game_id}:{user_id}"):
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "RATE_LIMITED",
                    "message": "Too many messages",
                },
            )
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "INVALID_JSON",
                    "message": "Message is not valid JSON",
                },
            )
            return

        msg_type = data.get("type")
        if not isinstance(msg_type, str):
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "MISSING_TYPE",
                    "message": "Message must include a 'type' field",
                },
            )
            return

        try:
            event = ClientEvent(msg_type)
        except ValueError:
            await self.cm.send_to_player(
                game_id,
                user_id,
                {
                    "type": ServerEvent.ERROR,
                    "code": "UNKNOWN_TYPE",
                    "message": f"Unknown message type: {msg_type}",
                },
            )
            return

        if event not in (ClientEvent.PONG, ClientEvent.REFRESH_TOKEN):
            doc = await self._load(game_id)
            if not doc:
                await self.cm.send_to_player(
                    game_id,
                    user_id,
                    {
                        "type": ServerEvent.ERROR,
                        "code": "INVALID_ACTION",
                        "message": "Game not found",
                    },
                )
                return

            if not any(p["user_id"] == user_id for p in doc["players"]):
                await self.cm.send_to_player(
                    game_id,
                    user_id,
                    {
                        "type": ServerEvent.ERROR,
                        "code": "UNAUTHORIZED",
                        "message": "You are not a participant in this game",
                    },
                )

                ws = self.cm.get_local_connections(game_id).get(user_id)
                if ws:
                    with contextlib.suppress(Exception):
                        await ws.close(code=4003, reason="Not a participant")
                return

        if event == ClientEvent.START_GAME:
            await self._handle_start_game(game_id, user_id)
        elif event == ClientEvent.SUBMIT_GUESS:
            lat = data.get("lat")
            lng = data.get("lng")
            if lat is None or lng is None:
                await self.cm.send_to_player(
                    game_id,
                    user_id,
                    {
                        "type": ServerEvent.ERROR,
                        "code": "MISSING_FIELD",
                        "message": "lat and lng are required for submit_guess",
                    },
                )
                return
            if not isinstance(lat, int | float) or not (-90 <= lat <= 90):
                await self.cm.send_to_player(
                    game_id,
                    user_id,
                    {
                        "type": ServerEvent.ERROR,
                        "code": "INVALID_FIELD",
                        "message": "lat must be a number between -90 and 90",
                    },
                )
                return
            if not isinstance(lng, int | float) or not (-180 <= lng <= 180):
                await self.cm.send_to_player(
                    game_id,
                    user_id,
                    {
                        "type": ServerEvent.ERROR,
                        "code": "INVALID_FIELD",
                        "message": "lng must be a number between -180 and 180",
                    },
                )
                return
            await self._handle_submit_guess(game_id, user_id, float(lat), float(lng))
        elif event == ClientEvent.FORFEIT:
            await self._handle_forfeit(game_id, user_id)
        elif event == ClientEvent.EXTEND_LOBBY:
            await self._handle_extend_lobby(game_id, user_id)
        elif event == ClientEvent.LEAVE_LOBBY:
            await self._handle_leave_lobby(game_id, user_id)
        elif event == ClientEvent.READY_NEXT:
            await self._handle_ready_next(game_id, user_id)
        elif event == ClientEvent.PONG:
            self.cm.mark_pong(game_id, user_id)
        elif event == ClientEvent.READY_UP:
            await self._handle_ready_up(game_id, user_id)
        elif event == ClientEvent.UNREADY:
            await self._handle_unready(game_id, user_id)
        elif event == ClientEvent.KICK:
            target_user_id = data.get("userId")
            if not isinstance(target_user_id, str) or not target_user_id.strip():
                await self.cm.send_to_player(
                    game_id,
                    user_id,
                    {
                        "type": ServerEvent.ERROR,
                        "code": "MISSING_FIELD",
                        "message": "userId is required for kick",
                    },
                )
                return
            await self._handle_kick(game_id, user_id, target_user_id)
        elif event == ClientEvent.REQUEST_REMATCH:
            await self._handle_request_rematch(game_id, user_id)
        elif event == ClientEvent.REFRESH_TOKEN:
            pass  # Token refresh handled at WS layer
