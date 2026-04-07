# Multiplayer

## 1. Overview

Multiplayer adds real-time competitive play to VandyGuessr. Two to five players join a shared game via invite code, see the same 360-degree images, and guess independently within a 120-second timer. Scores are compared after each round, and a winner is declared at the end of 5 rounds.

Multiplayer is gated behind the `FEATURE_MULTIPLAYER` feature flag and uses a separate MongoDB collection (`multiplayer_games`) from solo games. Real-time communication uses WebSockets with Redis pub/sub for multi-worker message routing.

**Key constraints:**

- 2-5 players per game
- Invite-code-only matchmaking (no random queue)
- Always timed (120s per round)
- Host controls when the game starts
- Redis is a hard dependency
- Multiplayer games do not affect solo player stats (gamesPlayed, totalPoints, avgScore, locationsDiscovered)

---

## 2. Feature Flag

Multiplayer is controlled by the `FEATURE_MULTIPLAYER` environment variable on both backend and frontend.

### Backend (`apps/api/`)

Add to `config.py` via pydantic-settings:

```python
feature_multiplayer: bool = False
```

When `False`:
- The multiplayer router is not registered on the FastAPI app
- All multiplayer endpoints return 404
- The WebSocket endpoint is unavailable

When `True`:
- The multiplayer router is registered under `/v1/multiplayer`
- Redis pub/sub listener state is initialized lazily when the first multiplayer WebSocket connects

### Frontend (`apps/web/`)

Add to `.env`:

```
VITE_FEATURE_MULTIPLAYER=false
```

When `false`:
- The "Create Game" and "Join Game" UI is hidden on the Home page
- Multiplayer routes are not registered

When `true`:
- Multiplayer UI appears on the Home page
- `/multiplayer/:id/lobby` and `/multiplayer/:id` routes are active

---

## 3. Game Flow

End-to-end lifecycle:

```
1. Host creates game        POST /v1/multiplayer/create
                            -> Returns game with invite_code, status="waiting"

2. Host enters lobby        WS /v1/multiplayer/{id}/ws
                            -> Host sees invite code, waiting for players

3. Players join             POST /v1/multiplayer/join { code: "ABCD12" }
                            -> Returns game state
                            -> Player connects via WS
                            -> All players receive "player_joined"

4. Host starts game         Client sends { type: "start_game" }
                            -> Server validates 2+ players
                            -> Broadcasts "game_starting" with 3s countdown
                            -> Sets status="active", starts round 1

5. Round play (x5)          Server broadcasts "round_start" with image + timer
                            -> Players submit guesses via WS
                            -> Server broadcasts "player_guessed" (no details)
                            -> When all guess or timer expires: "round_result"

6. Game ends                After round 5: server broadcasts "game_over"
                            -> Status set to "completed"
                            -> Winner determined by total score
```

---

## 4. Game States

```
             create
               |
               v
         +-----------+
         |  WAITING   |
         +-----------+
        /      |       \
       /       |        \
  host       start     10min
  30s fail  (2+ ppl)   TTL
      |         |          |
      v         v          v
+-----------+      +-----------+
| CANCELLED |      | CANCELLED |
+-----------+      +-----------+
               |
               v
         +-----------+
         |   ACTIVE   |
         +-----------+
        /      |       \
       /       |        \
  round 5   all leave   forfeit
  complete   timeout    (1 left)
      |         |          |
      v         v          v
+-----------+ +-----------+
| COMPLETED | | ABANDONED |
+-----------+ +-----------+
```

| Status | Description |
|--------|-------------|
| `waiting` | Lobby open, host waiting for players to join. Expires after 10 minutes. |
| `active` | Game in progress. Rounds are being played. |
| `completed` | All 5 rounds finished, or only 1 player remains (others forfeited). |
| `cancelled` | Host failed to reconnect within 30s during lobby, or lobby TTL expired without extension. |
| `abandoned` | All players disconnected and none reconnected within the timeout. |

### Transition Rules

| From | To | Trigger |
|------|----|---------|
| `waiting` | `active` | Host sends `start_game` with 2+ players present |
| `waiting` | `cancelled` | Host disconnects and fails to reconnect within 30s, or 10-minute TTL expires without extension |
| `active` | `completed` | Round 5 results are resolved |
| `active` | `completed` | All players except one forfeit or fail to reconnect |
| `active` | `abandoned` | All players disconnect and 60s passes with no reconnection |

---

## 5. Data Model

Multiplayer games use a dedicated `multiplayer_games` MongoDB collection, separate from the solo `games` collection.

### MultiplayerModeEntity

```python
class MultiplayerModeEntity(BaseModel):
    environment: Literal["indoor", "outdoor", "any"]
```

### MultiplayerGuessEntity

```python
class MultiplayerGuessEntity(BaseModel):
    lat: float
    lng: float
    distance_meters: float
    score: int
    submitted_at: datetime
```

### MultiplayerGameEntity

```python
class MultiplayerGameEntity(BaseModel):
    id: str | None
    host_id: str                          # Microsoft OID of the player who created the lobby
    invite_code: str                      # 6-char alphanumeric, unique index
    status: Literal["waiting", "active", "completed", "cancelled", "abandoned"]
    mode: MultiplayerModeEntity
    players: list[MultiplayerPlayerEntity]
    rounds: list[MultiplayerRoundEntity]
    current_round: int                    # 1-indexed, which round is active
    created_at: datetime
    started_at: datetime | None           # set when host starts the game
    last_activity_at: datetime
```

### MultiplayerPlayerEntity

Embedded subdocument within `MultiplayerGameEntity.players`.

```python
class MultiplayerPlayerEntity(BaseModel):
    user_id: str                          # Microsoft OID
    name: str
    avatar_url: str | None
    total_score: int                      # running total across rounds
    status: Literal["connected", "disconnected", "forfeited"]
    joined_at: datetime
    disconnected_at: datetime | None      # set on disconnect, cleared on reconnect
```

### MultiplayerRoundEntity

Embedded subdocument within `MultiplayerGameEntity.rounds`.

```python
class MultiplayerRoundEntity(BaseModel):
    round_id: int                         # 1-5
    image_id: str
    image_url: str
    image_tiles: dict | None              # tiled panorama metadata (same contract as solo imageTiles)
    actual_lat: float
    actual_lng: float
    location_name: str | None
    started_at: datetime | None
    expires_at: datetime | None           # started_at + 120s
    guesses: dict[str, MultiplayerGuessEntity]  # keyed by user_id
```

### Image Selection

All 5 round images are selected at game creation time (`POST /v1/multiplayer/create`):

1. Query the `images` collection filtered by `mode.environment` (or all images if `"any"`).
2. Randomly select 5 distinct images.
3. Store each image's `image_id`, `image_url`, `image_tiles` (if present/valid), `actual_lat`, `actual_lng`, and `location_name` on the corresponding `MultiplayerRoundEntity`.
4. The `imageUrl` and optional `imageTiles` are sent to clients at `round_start` time (and via `game_state` hydration for reconnect) — never exposed in REST responses or lobby state.

**Edge case — image deleted mid-game:** If an image is deleted from the `images` collection while a game is active, the server detects this when preparing the `round_start` payload (the URL would 404). The server selects a replacement image matching the same environment filter, updates the round entity, and proceeds. If no replacement is available, the round is skipped and all players receive 5000 for that round.

### Indexes

| Collection | Index | Type | Purpose |
|------------|-------|------|---------|
| `multiplayer_games` | `invite_code` | Unique | Fast join-by-code lookup |
| `multiplayer_games` | `host_id, status` | Compound | Find active lobbies for a user |
| `multiplayer_games` | `players.user_id, status` | Compound | Find active games a user is in |
| `multiplayer_games` | `created_at` | TTL (optional) | Auto-cleanup old games |

---

## 6. API Surface

### REST Endpoints

All endpoints require authentication (`CurrentUser`). Mounted at `/v1/multiplayer` when `FEATURE_MULTIPLAYER` is enabled.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/multiplayer/create` | Create a lobby. Returns game with invite code. |
| `POST` | `/v1/multiplayer/join` | Join a game by invite code. Body: `{"code": "ABCD12"}`. |
| `GET` | `/v1/multiplayer/{game_id}` | Get game state. Hides unresolved round answers. |
| `GET` | `/v1/multiplayer/active` | Get the user's current active or waiting multiplayer game, if any. |

### WebSocket Endpoint

| Protocol | Path | Purpose |
|----------|------|---------|
| `WS` | `/v1/multiplayer/{game_id}/ws?token=<idToken>&v=1` | Real-time gameplay communication. |

REST is used for game setup (create, join) and state recovery (get). Once connected, all gameplay flows through the WebSocket.

---

## 7. WebSocket Protocol

### Event Type Enums

All event types are defined as enums. No magic strings in the protocol handlers.

**Backend (Python):**

```python
from enum import StrEnum

class ClientEvent(StrEnum):
    SUBMIT_GUESS = "submit_guess"
    START_GAME = "start_game"
    FORFEIT = "forfeit"
    REFRESH_TOKEN = "refresh_token"
    EXTEND_LOBBY = "extend_lobby"
    LEAVE_LOBBY = "leave_lobby"
    READY_NEXT = "ready_next"
    PONG = "pong"
    READY_UP = "ready_up"
    UNREADY = "unready"
    KICK = "kick"
    REQUEST_REMATCH = "request_rematch"

class ServerEvent(StrEnum):
    # Lobby
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    PLAYER_READY = "player_ready"
    PLAYER_UNREADY = "player_unready"
    GAME_STARTING = "game_starting"
    GAME_CANCELLED = "game_cancelled"
    KICKED = "kicked"
    LOBBY_EXPIRING = "lobby_expiring"
    # Gameplay
    ROUND_START = "round_start"
    PLAYER_GUESSED = "player_guessed"
    GUESS_ACCEPTED = "guess_accepted"
    ROUND_RESULT = "round_result"
    GAME_OVER = "game_over"
    REMATCH_STARTING = "rematch_starting"
    # Connection
    PLAYER_DISCONNECTED = "player_disconnected"
    PLAYER_RECONNECTED = "player_reconnected"
    PLAYER_FORFEITED = "player_forfeited"
    GAME_STATE = "game_state"
    TOKEN_EXPIRING = "token_expiring"
    PING = "ping"
    ERROR = "error"
```

**Frontend (TypeScript):**

```typescript
enum ClientEvent {
  SubmitGuess = "submit_guess",
  StartGame = "start_game",
  Forfeit = "forfeit",
  RefreshToken = "refresh_token",
  ExtendLobby = "extend_lobby",
  LeaveLobby = "leave_lobby",
  ReadyNext = "ready_next",
  Pong = "pong",
  ReadyUp = "ready_up",
  Unready = "unready",
  Kick = "kick",
  RequestRematch = "request_rematch",
}

enum ServerEvent {
  // Lobby
  PlayerJoined = "player_joined",
  PlayerLeft = "player_left",
  PlayerReady = "player_ready",
  PlayerUnready = "player_unready",
  GameStarting = "game_starting",
  GameCancelled = "game_cancelled",
  Kicked = "kicked",
  LobbyExpiring = "lobby_expiring",
  // Gameplay
  RoundStart = "round_start",
  PlayerGuessed = "player_guessed",
  GuessAccepted = "guess_accepted",
  RoundResult = "round_result",
  GameOver = "game_over",
  RematchStarting = "rematch_starting",
  // Connection
  PlayerDisconnected = "player_disconnected",
  PlayerReconnected = "player_reconnected",
  PlayerForfeited = "player_forfeited",
  GameState = "game_state",
  TokenExpiring = "token_expiring",
  Ping = "ping",
  Error = "error",
}
```

### Client to Server

```jsonc
// Submit a guess for the current round
{"type": "submit_guess", "lat": 36.145, "lng": -86.803}

// Host starts the game from the lobby
{"type": "start_game"}

// Player forfeits and leaves the game
{"type": "forfeit"}

// Refresh authentication token mid-game
{"type": "refresh_token", "token": "<new_id_token>"}

// Host extends the lobby TTL (sent after receiving lobby_expiring)
{"type": "extend_lobby"}

// Non-host player leaves the lobby intentionally
{"type": "leave_lobby"}

// Player confirms they are ready to proceed from round results
{"type": "ready_next"}

// Heartbeat response to server ping
{"type": "pong"}

// Player marks themselves ready in lobby
{"type": "ready_up"}

// Player clears lobby ready state
{"type": "unready"}

// Host removes a player from lobby
{"type": "kick", "userId": "<target_user_id>"}

// Host starts rematch after game over
{"type": "request_rematch"}
```

### Server to Client (Lobby Phase)

```jsonc
// A new player joined the lobby
{"type": "player_joined", "player": {"userId": "...", "name": "...", "avatarUrl": "..."}, "playerCount": 3}

// A player left the lobby (explicit leave_lobby only, not on WS drop)
{"type": "player_left", "userId": "...", "playerCount": 2}

// Host started the game, countdown before round 1
{"type": "game_starting", "countdown": 3}

// Game was cancelled (host left or lobby expired)
{"type": "game_cancelled", "reason": "Host left"}

// Lobby TTL is running low (sent to host only, 5 minutes remaining)
{"type": "lobby_expiring"}
```

### Server to Client (Gameplay Phase)

```jsonc
// A new round begins
{
  "type": "round_start",
  "round": 1,
  "imageUrl": "https://spaces.example.com/images/abc.jpg",
  "imageTiles": null,
  "expiresAt": "2026-02-16T20:02:00Z"
}

// Another player submitted their guess (no details revealed)
{"type": "player_guessed", "userId": "...", "remainingPlayers": 2}

// Acknowledgment sent to the player who just guessed (sent only to them)
{"type": "guess_accepted", "round": 1}

// Round complete -- all players guessed or timer expired
{
  "type": "round_result",
  "round": 1,
  "results": [
    {
      "userId": "...",
      "name": "Alice",
      "score": 4200,
      "distanceMeters": 23.5,
      "guess": {"lat": 36.145, "lng": -86.803}
    },
    {
      "userId": "...",
      "name": "Bob",
      "score": 3100,
      "distanceMeters": 87.2,
      "guess": {"lat": 36.144, "lng": -86.801}
    }
  ],
  "actual": {"lat": 36.1453, "lng": -86.802},
  "locationName": "Kirkland Hall",
  "standings": [
    {"userId": "...", "name": "Alice", "totalScore": 4200, "rank": 1},
    {"userId": "...", "name": "Bob", "totalScore": 3100, "rank": 2}
  ]
}

// Game over after round 5 (or all opponents forfeited)
{
  "type": "game_over",
  "winnerId": "...",
  "standings": [
    {"userId": "...", "name": "Alice", "totalScore": 21500, "rank": 1},
    {"userId": "...", "name": "Bob", "totalScore": 18200, "rank": 2}
  ]
}
```

### Server to Client (Connection Events)

```jsonc
// A player disconnected mid-game
{"type": "player_disconnected", "userId": "...", "reconnectDeadline": "2026-02-16T20:01:30Z"}

// A disconnected player reconnected
{"type": "player_reconnected", "userId": "..."}

// Full game state sent to a reconnecting player (only to them)
{
  "type": "game_state",
  "status": "active",
  "currentRound": 3,
  "round": {
    "round": 3,
    "imageUrl": "https://spaces.example.com/images/xyz.jpg",
    "imageTiles": null,
    "expiresAt": "2026-02-16T20:04:00Z"
  },
  "playersGuessed": ["user_id_1", "user_id_2"],
  "hasGuessedThisRound": false,
  "players": [
    {"userId": "...", "name": "Alice", "status": "connected", "totalScore": 8500},
    {"userId": "...", "name": "Bob", "status": "connected", "totalScore": 7200},
    {"userId": "...", "name": "Carol", "status": "disconnected", "totalScore": 6100}
  ],
  "previousRounds": [
    {"round": 1, "score": 4200, "distanceMeters": 23.5},
    {"round": 2, "score": 4300, "distanceMeters": 18.1}
  ]
}

// A player forfeited (quit or failed to reconnect)
{"type": "player_forfeited", "userId": "..."}

// Token is about to expire, client should send refresh_token
{"type": "token_expiring"}

// Error
{"type": "error", "code": "INVALID_ACTION", "message": "Not your turn to start the game"}
```

### Message Validation

The server validates every incoming WebSocket message before processing it. Invalid messages receive an `error` response. Repeated violations trigger rate-limit enforcement.

| Step | Check | Failure Response |
|------|-------|------------------|
| 1 | JSON parses successfully | `{"type": "error", "code": "INVALID_JSON", "message": "Message is not valid JSON"}` |
| 2 | `type` field exists and is a string | `{"type": "error", "code": "MISSING_TYPE", "message": "Message must include a 'type' field"}` |
| 3 | `type` value is a known `ClientEvent` enum member | `{"type": "error", "code": "UNKNOWN_TYPE", "message": "Unknown message type: <value>"}` |
| 4 | Required fields are present for the given type (e.g., `lat`/`lng` for `submit_guess`, `token` for `refresh_token`) | `{"type": "error", "code": "MISSING_FIELD", "message": "<field> is required for <type>"}` |
| 5 | Field types and ranges are valid (e.g., `lat` is a float between -90 and 90, `lng` between -180 and 180) | `{"type": "error", "code": "INVALID_FIELD", "message": "<field> must be <constraint>"}` |
| 6 | Action is valid for the current game state (e.g., `start_game` only valid in `waiting` status, `submit_guess` only in `active`) | `{"type": "error", "code": "INVALID_ACTION", "message": "<description>"}` |
| 7 | Player is authorized for the action (e.g., only host can send `start_game` or `extend_lobby`; only non-host can send `leave_lobby`) | `{"type": "error", "code": "UNAUTHORIZED", "message": "Only the host can <action>"}` |
| 8 | Rate limit: max 10 messages per second per connection | `{"type": "error", "code": "RATE_LIMITED", "message": "Too many messages"}`. Connection is closed with code `1008` after 3 consecutive violations. |

### Round Resolution

A round can be resolved by two concurrent triggers: the last player submitting a guess and the round timer expiring. To prevent double-resolution, the server holds an `asyncio.Lock` per active game.

1. Both the "last guess received" path and the "timer expired" path acquire the lock before resolving the round.
2. Inside the lock, the handler checks if the round has already been resolved (i.e., `round_result` already broadcast). If so, it releases the lock and returns.
3. The round is resolved exactly once: scores are calculated and the `round_result` message is broadcast.

This lock is in-memory per worker. In a multi-worker deployment, only one worker runs the timer for a given game (the worker that created the timer task). The lock prevents races between an incoming guess on that same worker and the timer callback.

### Round Ready Barrier (`ready_next`)

For rounds 1-4, advancing from results to the next round is coordinated with a Redis-backed barrier keyed by game and round.

1. Each `ready_next` message adds the player to `mp:ready:{game_id}:{round}` using `SADD` (idempotent).
2. Required ready players are computed from authoritative game state: all players with `status == "connected"`.
3. When all required players are present in the ready set, workers compete for `mp:ready-lock:{game_id}:{round}` using `SET NX`.
4. The lock holder re-validates game/round state from MongoDB, starts the next round exactly once, and clears barrier keys.

This makes round advancement safe when players in the same game are connected to different workers.

### Countdown Behavior

When the host sends `start_game`:

1. Server validates 2+ players are present.
2. Server broadcasts a single `game_starting` message with `{"countdown": 3}`.
3. The client renders a local 3-2-1 countdown based on the message.
4. The server waits 3 seconds (via `asyncio.sleep(3)`), then broadcasts `round_start` with the first image and timer.

The server controls the actual game start time. Clients do not send any message when their local countdown finishes — they simply wait for `round_start`. Minor clock skew between clients is irrelevant because the server's `round_start` is the source of truth for when the round begins and when `expiresAt` is set.

---

## 8. WebSocket Authentication

### Connection Handshake

The ID token is passed as a query parameter because browser WebSocket APIs do not support custom headers.

```
ws://host/v1/multiplayer/{game_id}/ws?token=<idToken>&v=1
```

The `v` query parameter specifies the protocol version. The server rejects connections with an unknown or missing `v` value (see close code `4012`).

> **Logging warning:** The WebSocket endpoint URL contains the JWT in the query string. Configure the web server and any reverse proxies to exclude this endpoint from access log output to prevent token leakage in log files.

On connection, the server:

1. Checks the `v` query parameter. Rejects with `4012` if missing or unsupported.
2. Validates the JWT using the same `verify_token` logic as REST endpoints (JWKS, audience, expiry).
3. Extracts the user identity via `get_current_user` (email domain check, OID extraction).
4. Verifies the user is a participant in the specified game.
5. Accepts the connection if all checks pass.

### Close Codes

| Code | Reason | Meaning |
|------|--------|---------|
| `4001` | Authentication failed | Invalid, expired, or non-Vanderbilt token |
| `4003` | Not a participant | User is not a player in this game |
| `4004` | Game not found | No game with this ID exists |
| `4010` | Game is not active | Game is completed, cancelled, or abandoned |
| `4011` | Lobby full | Game already has 5 players |
| `4012` | Unsupported protocol version | Unknown or missing `v` query parameter |
| `1000` | Normal closure | Clean disconnect |
| `1011` | Server error | Unexpected server-side failure |

### Mid-Game Token Refresh

ID tokens last approximately 1 hour (Azure AD default). Games take at most ~12 minutes (5 rounds x 120s + overhead), so expiry during gameplay is unlikely but handled:

1. Server tracks when each connection's token will expire.
2. At 5 minutes before expiry, server sends `{"type": "token_expiring"}`.
3. Client calls `acquireTokenSilent()` and sends `{"type": "refresh_token", "token": "<new_token>"}`.
4. Server validates the new token and updates the session.
5. If no refresh is received within 60 seconds of the warning, the connection is closed with code `4001`.

---

## 9. Connection Manager

The `ConnectionManager` coordinates WebSocket connections and message routing.

### Architecture

```
                    +-----------------------+
                    |   ConnectionManager   |
                    +-----------------------+
                    | _local_connections:   |
                    |   game_id -> {        |
                    |     user_id: WS,      |
                    |     user_id: WS       |
                    |   }                   |
                    +-----------------------+
                          |           |
                     Local WS     Redis Pub/Sub
                     routing      (cross-worker)
                          |           |
                    +-----------+-----------+
                    | Worker 1  | Worker 2  |
                    +-----------+-----------+
```

### Responsibilities

| Method | Behavior |
|--------|----------|
| `connect(game_id, user_id, ws)` | Register a WebSocket connection. Subscribe to `multiplayer:{game_id}` Redis channel if first connection on this worker for this game. |
| `disconnect(game_id, user_id)` | Remove the connection. Unsubscribe from Redis channel if no more local connections for this game. |
| `broadcast(game_id, message, exclude?)` | Send to all local connections for this game (except `exclude`). Publish to `multiplayer:{game_id}` Redis channel for other workers. |
| `send_to_player(game_id, user_id, message)` | Send to a specific player. If not on this worker, publish targeted message to Redis. |

### Redis Pub/Sub Channels

| Channel Pattern | Purpose |
|-----------------|---------|
| `multiplayer:{game_id}` | Game-specific broadcast channel. Each worker subscribes when it has at least one player connected to that game. |

### Single-Worker Simplification

For the initial deployment, a single Uvicorn worker is expected. In this case, Redis pub/sub is still used (to keep the code path consistent), but all messages route locally. The overhead is negligible and avoids a separate code path for single-worker vs. multi-worker.

### Duplicate Connections

If a second WebSocket connection arrives for the same `(game_id, user_id)` pair (e.g., user opens the game in a new tab), the server closes the old connection with code `1000` ("Normal closure") and replaces it with the new one. The new connection receives the current game state via a `game_state` message. No `player_disconnected`/`player_reconnected` is broadcast to other players since the user was never actually absent.

### Heartbeat

The server sends a WebSocket ping frame every 15 seconds to each connection. If no pong is received within 10 seconds, the connection is considered dead and the disconnect flow is triggered (30s reconnect window for gameplay, same for lobby).

This catches silently dropped connections (e.g., mobile network switch, laptop lid close) that TCP keepalive alone would take minutes to detect.

---

## 10. Error Handling

### Connection Phase

| Error | Trigger | Server Response | Client Behavior |
|-------|---------|-----------------|-----------------|
| Invalid token | Bad, expired, or malformed JWT | Close `4001` "Authentication failed" | Show "Session expired", redirect to login |
| Non-Vanderbilt email | Valid JWT, wrong domain | Close `4001` "Unauthorized" | Show error, redirect to login |
| Game not found | Invalid `game_id` | Close `4004` "Game not found" | Show "Game not found", navigate home |
| Not a participant | User not in game's player list | Close `4003` "Not a participant" | Show "You're not in this game" |
| Game not active | Game is completed/cancelled/abandoned | Close `4010` "Game is not active" | Show results if completed, otherwise navigate home |
| Lobby full | 6th player attempts WS connection | Close `4011` "Lobby full" | Show "Game is full" |
| Redis unavailable | pub/sub channel creation fails | Log critical error. Close `1011`. | Show "Connection error", offer retry |

### Lobby Phase

| Error | Trigger | Server Response | Client Behavior |
|-------|---------|-----------------|-----------------|
| Lobby full (REST) | 6th player calls `/join` | HTTP 409 "Game is full" | Show "Game is full" |
| Invalid invite code | Code not found or expired | HTTP 404 "Invalid or expired invite code" | Show "Invalid code, check and try again" |
| Expired lobby | 10-minute TTL exceeded (no extension) | Lazy-set `cancelled` on next access. Return 410. Broadcast `game_cancelled` to connected players. | Show "This game has expired" |
| Host disconnects in lobby | Host WS drops | Start 30s reconnect timer. Broadcast `player_disconnected` to remaining players. If host reconnects within 30s, broadcast `player_reconnected`. If not, set status `cancelled`, broadcast `game_cancelled`. | Players see "Host disconnected (30s to reconnect)". If host doesn't return, navigate home. |
| Non-host disconnects in lobby | Non-host WS drops | Start 30s reconnect timer. If player reconnects within 30s, broadcast `player_reconnected`. If not, remove from players list, broadcast `player_left`. | Others see "Player X disconnected". If they don't return, updated player list. |
| Player leaves lobby | Non-host sends `leave_lobby` message | Remove from players list immediately (no 30s wait). Broadcast `player_left`. Close WS with `1000`. | Others see updated player list. Leaving player navigates home. |
| Lobby TTL exhausted | All 6 extensions used, final 10-minute window expires | Set status `cancelled`. Broadcast `game_cancelled` with reason "Lobby expired". | All players navigate home. |
| Start with < 2 players | Host sends `start_game` alone | Send `error` message: "Need at least 2 players" | Show validation error |
| Non-host starts | Non-host sends `start_game` | Send `error` message: "Only the host can start" | Ignore (button should only render for host) |

### Gameplay Phase

| Error | Trigger | Server Response | Client Behavior |
|-------|---------|-----------------|-----------------|
| Guess after expiry | Timer ran out before guess received | Ignore. Round already resolved with 0 for this player. | Client should auto-submit on timer; resync from `round_result` |
| Duplicate guess | Player submits twice for same round | Ignore second guess. No error sent. | Idempotent, no visible effect |
| Guess for wrong round | Client out of sync | Send `error` with current game state | Client resyncs to correct round |
| Player disconnect | WebSocket drops | Start 30s reconnect timer. Broadcast `player_disconnected`. | Others see "Player X disconnected (30s to reconnect)" |
| Reconnect within 30s | Player re-establishes WS | Cancel timer. Broadcast `player_reconnected`. Send full current game state to reconnecting player. | Player picks up where they left off |
| Reconnect after 30s | Player comes back too late | Player marked `forfeited`. Remaining rounds scored 0. | Show "You were removed from the game" |
| All players disconnect | Everyone drops | Start 60s abandon timer. | If nobody reconnects, game set to `abandoned` |
| Player forfeits | Player explicitly quits | Mark `forfeited`. Remaining rounds scored 0. Broadcast `player_forfeited`. Game continues. | Others see "Player X forfeited" |
| Only 1 player remaining | All others forfeit/disconnect past 30s | That player wins. Game set to `completed`. Broadcast `game_over`. | Show "You win! All opponents left" |
| MongoDB write failure | Can't persist guess | Retry once. Hold result in memory and retry on next write. Send result to players via WS regardless. | Players see results immediately. Persistence is eventually consistent. |
| Redis failure mid-game | pub/sub breaks | Continue with local connections only. Log critical error. Cross-worker players are disconnected. | Players on same worker are unaffected. Others enter reconnect flow. |

### Post-Game

| Error | Trigger | Server Response | Client Behavior |
|-------|---------|-----------------|-----------------|
| Can't load results | MongoDB read fails on GET | HTTP 503 "Service unavailable" | Show "Couldn't load results" with retry button |
| Rematch with offline players | Some players left after game ended | Create new lobby with only connected players | Show who's in the rematch lobby |

---

## 11. Disconnect & Reconnection

### Lobby Disconnection

Disconnections during the lobby phase (`waiting` status) use the same 30-second reconnect window as gameplay, but with different outcomes.

**Host disconnects:**

1. Server marks the host as `disconnected` with `disconnected_at = now()`.
2. Server broadcasts `player_disconnected` with a `reconnectDeadline` (30 seconds from now).
3. If the host reconnects within 30 seconds, server broadcasts `player_reconnected` and the lobby continues normally.
4. If the host does not reconnect within 30 seconds, the lobby is cancelled: status is set to `cancelled`, and `game_cancelled` is broadcast to all remaining players with reason "Host disconnected".

**Non-host disconnects:**

1. Server marks the player as `disconnected` with `disconnected_at = now()`.
2. Server broadcasts `player_disconnected` with a `reconnectDeadline` (30 seconds from now).
3. If the player reconnects within 30 seconds, server broadcasts `player_reconnected`.
4. If the player does not reconnect within 30 seconds, they are removed from the `players` list and `player_left` is broadcast.

The lobby TTL timer continues to tick during disconnections. If the TTL expires while the host is disconnected, the lobby is cancelled regardless of the reconnect window.

### Gameplay Reconnect Window

When a player's WebSocket connection drops during an active game:

1. Server marks the player as `disconnected` with `disconnected_at = now()`.
2. Server broadcasts `player_disconnected` with a `reconnectDeadline` (30 seconds from now).
3. The game continues for remaining players. The disconnected player's rounds are not auto-resolved until the deadline passes.
4. If the player reconnects within 30 seconds:
   - Player authenticates via the same WS handshake flow.
   - Server cancels the forfeit timer.
   - Server broadcasts `player_reconnected`.
   - Server sends the full current game state to the reconnecting player (current round, timer remaining, who has guessed).
5. If the player does not reconnect within 30 seconds:
   - Player is marked `forfeited`.
   - All remaining rounds for this player are scored 0.
   - Server broadcasts `player_forfeited`.

### Forfeit

A player forfeits in two scenarios:

- **Explicit:** The player sends `{"type": "forfeit"}`. Immediate effect.
- **Implicit:** The player disconnects and fails to reconnect within 30 seconds.

In both cases:
- Player's remaining rounds are scored 0.
- Game continues for remaining players.
- If only 1 player remains, they win and the game is completed.

### All-Disconnect Abandon

If every player in the game disconnects simultaneously:

1. Server starts a 60-second abandon timer for the game.
2. If any player reconnects within 60 seconds, the timer is cancelled and the game resumes.
3. If no one reconnects, the game is set to `abandoned`.

### Timer Behavior During Disconnect

The round timer does not pause for disconnected players. If a player is disconnected when the round timer expires, their guess is resolved as 0 (no guess submitted).

---

## 12. Pages & Frontend Components

### Route Changes

| Route | Component | Status | Description |
|-------|-----------|--------|-------------|
| `/` | `Home.svelte` | Modified | Add "Create Game" and "Join Game" UI (gated by feature flag) |
| `/multiplayer/:id/lobby` | `MultiplayerLobby.svelte` | New | Lobby with invite code, player list, host start button |
| `/multiplayer/:id` | `MultiplayerGame.svelte` | New | Gameplay with multiplayer HUD, opponent indicators, N-player results |

### New Frontend Domain

```
apps/web/src/lib/domains/multiplayer/
├── api/
│   └── multiplayer.service.ts       # REST calls (create, join, get)
├── ws/
│   └── multiplayer.ws.ts            # WebSocket client wrapper
├── stores/
│   ├── lobby.store.ts               # Lobby state (players, countdown)
│   └── multiplayer.store.ts         # Game state (rounds, scores, connection)
├── components/
│   ├── LobbyPlayerList.svelte       # Player avatars and names in lobby
│   ├── InviteCodeCard.svelte        # Displays code with copy button
│   ├── MultiplayerHud.svelte        # Round, scores, timer, opponent indicators
│   ├── MultiplayerResultsView.svelte # N-player round results with all pins on map
│   └── MultiplayerSummary.svelte    # Final standings, winner, rematch CTA
└── types.ts                         # MultiplayerGame, Player, Round types
```

### Modified Pages

**Home (`Home.svelte`):** Add a multiplayer section below the existing solo game configuration. Two elements:

- "Create Game" button that calls `POST /v1/multiplayer/create` and navigates to `/multiplayer/:id/lobby`
- "Join Game" input field for entering an invite code, with a "Join" button that calls `POST /v1/multiplayer/join` and navigates to the lobby

Both are conditionally rendered based on `VITE_FEATURE_MULTIPLAYER`.

### New Stores

**`lobby.store.ts`:**

```typescript
interface LobbyState {
  game: MultiplayerGame | null;
  players: Player[];
  countdown: number | null;     // 3-2-1 countdown before game start
  status: "waiting" | "starting" | "cancelled";
}
```

**`multiplayer.store.ts`:**

```typescript
interface MultiplayerState {
  connection: "connecting" | "connected" | "disconnected" | "reconnecting";
  game: MultiplayerGame | null;
  phase: "lobby" | "playing" | "results" | "game_over";
  currentRound: number;
  guessPosition: { lat: number; lng: number } | null;
  playersGuessed: string[];     // user IDs of players who have guessed this round
  roundResult: RoundResult | null;
  standings: Standing[];
  submitting: boolean;
}
```

### WebSocket Client (`multiplayer.ws.ts`)

A thin wrapper around the native `WebSocket` API:

- Acquires the current ID token via `getAccessToken()` and appends it as `?token=` query param
- Exposes `send(message)`, `close()`, and reactive connection state
- Handles automatic reconnection (up to 3 attempts with exponential backoff) on unexpected close
- Dispatches incoming messages to the multiplayer store
- Sends `refresh_token` when prompted by the server

---

## 13. Lobby Design

### Invite Codes

- 6 characters, alphanumeric, uppercase (e.g., `A3X9BK`)
- Generated server-side with collision check (retry on duplicate)
- Stored with a unique index on `multiplayer_games.invite_code`
- Displayed prominently in the lobby with a copy-to-clipboard button

### Player Capacity

- Minimum: 2 players (host + 1)
- Maximum: 5 players
- The join endpoint and WebSocket connection reject players beyond the cap

### Host Privileges

Only the host can:
- Start the game (requires 2+ players)
- Extend the lobby TTL (via `extend_lobby` message)
- The host disconnecting and failing to reconnect within 30s cancels the game for everyone

### Lobby TTL

- Lobbies in `waiting` status expire after 10 minutes
- At 5 minutes remaining, the server sends `lobby_expiring` to the host via WebSocket
- The host can respond with `extend_lobby` to reset the TTL to 10 minutes from now
- Extensions are capped at 6 (maximum total lobby lifetime of ~1 hour). The server tracks the extension count on the game document.
- After the 6th extension, when `lobby_expiring` fires for the final time and the host sends `extend_lobby`, the server responds with an error: `{"type": "error", "code": "INVALID_ACTION", "message": "Maximum lobby extensions reached"}`. If the host does not start the game within the remaining 5 minutes, the lobby is cancelled with `game_cancelled` reason "Lobby expired" and all players are navigated home.
- No visible countdown is shown in the lobby UI; the extension prompt is only surfaced to the host when the server sends `lobby_expiring`
- Expiry is enforced lazily: on `GET /v1/multiplayer/{id}` or `POST /v1/multiplayer/join`, if the TTL has elapsed and status is still `waiting`, the server sets status to `cancelled` and returns an appropriate error
- The Redis key `mp:lobby:{invite_code}` tracks the current TTL and is reset on each extension

### Lobby Flow

```
Host                          Server                        Player B
 |                              |                              |
 |-- POST /create ------------->|                              |
 |<-- game {code: "A3X9BK"} ---|                              |
 |                              |                              |
 |-- WS connect --------------->|                              |
 |                              |                              |
 |   (shares code out-of-band)  |                              |
 |                              |                              |
 |                              |<--------- POST /join {code} -|
 |                              |-- game ---------------------->|
 |                              |                              |
 |                              |<------------ WS connect -----|
 |<-- player_joined ------------|------------ player_joined -->|
 |                              |                              |
 |-- start_game --------------->|                              |
 |<-- game_starting {3} --------|------------ game_starting -->|
 |                              |                              |
 |   ... 3 second countdown ... |                              |
 |                              |                              |
 |<-- round_start --------------|-------------- round_start -->|
```

---

## 14. Scoring & Results

### Scoring Formula

The same formula as solo play:

```
score = 5000 * e ^ (-5 * distance / campus_diagonal)
```

- Building match bonus: if the guess resolves to the same building as the actual location, the player receives a perfect 5000.
- Maximum score per round: 5000. Maximum per game: 25000.
- Players who forfeit or fail to guess within the timer receive 0 for that round.

### Round Results

After each round, all players receive a `round_result` message containing:

- Each player's guess coordinates, distance, and score for the round
- The actual location coordinates and name
- Updated standings (cumulative scores, ranked)

Results are ordered by score descending for that round. The results map shows all players' pins with distinct colors.

### Winner Determination

The player with the highest `total_score` after 5 rounds wins. In case of a tie, the player with the lower total distance wins. If still tied, the player who submitted their guesses faster (sum of `submitted_at - started_at` across rounds) wins.

### Stats Isolation

Multiplayer games are completely excluded from solo player statistics. The following fields on `UserEntity` are unaffected by multiplayer results:

- `gamesPlayed`
- `totalPoints`
- `avgScore`
- `locationsDiscovered`

Multiplayer-specific statistics (wins, losses, win rate, multiplayer games played) are a future consideration and would be tracked as separate fields or in a dedicated collection.

---

## 15. Redis as Hard Dependency

Redis is required for multiplayer. It serves two purposes:

### 1. Pub/Sub for Cross-Worker Message Routing

When running multiple Uvicorn workers, two players in the same game may have WebSocket connections on different workers. Redis pub/sub ensures messages reach all players regardless of which worker they are connected to.

### 2. Ephemeral State

Short-lived data that does not need MongoDB persistence:

| Key Pattern | TTL | Purpose |
|-------------|-----|---------|
| `mp:reconnect:{game_id}:{user_id}` | 30s | Tracks reconnect deadline for disconnected players |
| `mp:abandon:{game_id}` | 60s | Tracks all-disconnect abandon timer |
| `mp:lobby:{invite_code}` | 10m | Fast code-to-game-id lookup (avoids MongoDB query on join) |
| `mp:ready:{game_id}:{round}` | 1h | Distributed round-ready barrier (`ready_next`) |
| `mp:ready-lock:{game_id}:{round}` | 30s | Exactly-once lock for starting the next round |

### Failure Mode

If Redis becomes unavailable:

- **At startup:** The application fails to start if the base Redis connection cannot be established.
- **During operation:** Cross-worker message routing fails. Players on the same worker are unaffected. The `ConnectionManager` falls back to local-only routing and logs a critical error. Reconnect and abandon timers stop working; the server should apply conservative defaults (e.g., immediately forfeit disconnected players rather than waiting).

### Registration in DI Container

Redis must be registered in the lagom container for the multiplayer service to access it:

```python
# container.py
from app.core.db.redis import get_redis

container[redis.Redis] = lambda: get_redis()
```

### MongoDB Index Bootstrap

Required multiplayer indexes are provisioned explicitly rather than during API startup:

```bash
python -m scripts.bootstrap_multiplayer
```

---

## 16. Future Considerations

The following are explicitly out of scope for the initial multiplayer implementation but are natural extensions:

| Feature | Notes |
|---------|-------|
| **Random matchmaking** | Queue system that pairs players automatically. Requires enough concurrent users to keep wait times short. |
| **Spectator mode** | Watch a live game without participating. Could use SSE instead of WebSocket (one-directional). |
| **Multiplayer leaderboard** | Track wins, losses, win rate. Separate from the solo leaderboard. |
| **Rematch** | After a game ends, offer a one-click "Rematch" that creates a new lobby with the same players. |
| **Team mode** | 2v2 or 3v3 with combined team scores. |
| **Variable round count** | Allow the host to configure 3, 5, or 10 rounds. |
| **Async challenges** | A simpler alternative: Player A completes a game, shares a link, Player B plays the same images and scores are compared. No real-time infrastructure required. Could serve as a stepping stone before full multiplayer. |
