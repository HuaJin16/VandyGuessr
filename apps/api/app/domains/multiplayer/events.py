"""WebSocket event type enums for the multiplayer protocol."""

from enum import StrEnum


class ClientEvent(StrEnum):
    SUBMIT_GUESS = "submit_guess"
    START_GAME = "start_game"
    FORFEIT = "forfeit"
    REFRESH_TOKEN = "refresh_token"
    EXTEND_LOBBY = "extend_lobby"
    LEAVE_LOBBY = "leave_lobby"


class ServerEvent(StrEnum):
    # Lobby
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    GAME_STARTING = "game_starting"
    GAME_CANCELLED = "game_cancelled"
    LOBBY_EXPIRING = "lobby_expiring"
    # Gameplay
    ROUND_START = "round_start"
    PLAYER_GUESSED = "player_guessed"
    GUESS_ACCEPTED = "guess_accepted"
    ROUND_RESULT = "round_result"
    GAME_OVER = "game_over"
    # Connection
    PLAYER_DISCONNECTED = "player_disconnected"
    PLAYER_RECONNECTED = "player_reconnected"
    PLAYER_FORFEITED = "player_forfeited"
    GAME_STATE = "game_state"
    TOKEN_EXPIRING = "token_expiring"
    ERROR = "error"
