# VandyGuessr — Product Requirements Document (PRD)

## 1) Summary
VandyGuessr is a GeoGuessr-style game for Vanderbilt students using 360-degree (equirectangular) campus imagery. Players guess locations on a campus map, earn scores based on accuracy, and compete on leaderboards. The product ships in a single, full-scope Phase 1 this semester, with optional extensions if time remains.

## 2) Goals
- Deliver a polished, campus-specific guessing game with 360-degree imagery.
- Support thousands of students with low operating cost.
- Provide competitive elements: stats, scores, and leaderboards.
- Keep content ingestion simple via EXIF-based uploads.

## 3) Non-Goals (Phase 1)
- Global scale or world map coverage
- Advanced social features (friends, clubs)
- Content moderation workflows
- Role-based admin system
- Light/dark mode, reporting, or advanced settings (deferred)

## 4) Target Users
- Vanderbilt students with campus familiarity

## 5) Core User Experience
### 5.1 Welcome/Login
- Centered card: “Welcome back” + “Log in with Vanderbilt”
- Auth0 login
- Vanderbilt-only access: validate `@vanderbilt.edu`
- On success: redirect to Home; on failure: simple error
- User profile loaded (name, email, avatar)

### 5.2 Home (Logged In)
- Centered card, two-column layout:
  - Left: short product description + quick stats (rank, locations discovered, games played, points)
  - Right: mode selection cards (Daily Challenge, Random Drop, Indoor, Outdoor, Timed, Untimed)
- Primary CTA: “Start Guessing”

### 5.3 Game Play
- Full-screen 360-degree viewer (equirectangular)
- Top bar: round number, current score, timer (if timed)
- Bottom controls: settings, mini-map, “Guess”
- Map expands on hover or click
- 5 rounds per game
- Single pin allowed; can be moved before submission

### 5.4 Round Results
- Round number
- Score, max score, optional multiplier (future)
- Map with guessed vs actual location + distance line
- “Next Round” button
- After Round 5, button becomes “See Results”

### 5.5 Game Summary (After Round 5)
- Total score (primary)
- Avg distance or avg score
- Best round / worst round
- Per-round breakdown (round number, score, distance)
- Mode metadata (timed/untimed, indoor/outdoor, daily/random)
- CTAs: Play Again, Home, Leaderboard

### 5.6 Leaderboard
- Filters: game mode + daily / weekly / all-time
- Table: rank, name, avg score, games played, points
- Current user highlighted
- Pagination for larger lists

## 6) Game Modes
- Timed (120 seconds per round)
- Untimed
- Indoor / Outdoor (mutually exclusive)
- Daily Challenge (fixed set of images for that day)
- Random Drop (randomized images)

## 7) Scoring
Primary formula (from PM notes):

```
Score = 5000 * e ^ (-10 * distance / size)
```

- distance: meters from guess to actual
- size: diagonal distance of campus bounding box
- score is rounded
- score clamped at 0 for very large distances

## 8) Maps & Tiles (Free, Campus-Only)
- Map rendering: Leaflet
- Tiles: OpenStreetMap-based raster tiles generated for the campus bounding box
- Hosting: static tiles in DigitalOcean Spaces
- Zoom levels: target z14–19 for campus clarity
- Attribution: include OpenStreetMap attribution in the UI

## 9) 360-Degree Viewer
- Photo Sphere Viewer (Three.js based)
- Equirectangular input
- Svelte integration

## 10) Authentication & Profiles
- Auth0 for sign-in
- Vanderbilt-only access via `@vanderbilt.edu` validation
- User fields stored: `email`, `username`, `name`
- `username`: auto-generated from email local part, normalized, unique
- `name`: editable display name (default from Auth0 first + last)
- Avatar (PFP): pulled from Auth0; shown in top bar with menu (Edit Profile, Logout)

## 11) Daily Challenge (No CRON)
### Deterministic Hash + Cache
- Inputs: date (CST), salt, eligible image IDs
- Seeded RNG picks 5 images
- First request each day writes the set to DB; subsequent requests reuse it
- Prevents daily set from changing if images are added mid-day

### Timezone
- Daily challenge rotates at CST midnight

### Tag Handling
- Daily challenge uses random images regardless of tags
- Tag system remains extensible for future filters

## 12) Data Model (MongoDB)

### users
```
{
  _id,
  auth0Id,
  email,
  username,
  name,
  avatarUrl,
  createdAt,
  stats: { gamesPlayed, totalPoints, avgScore, locationsDiscovered }
}
```

### images
```
{
  _id,
  url,
  exif: { lat, lng, altitude, timestamp, width, height, format },
  environment: "indoor" | "outdoor",
  createdAt
}
```

### games
```
{
  _id,
  userId,
  mode: { timed: boolean, environment: "indoor" | "outdoor" | "any", daily: boolean },
  rounds: [
    { roundId, imageId, guess: { lat, lng }, distanceMeters, score }
  ],
  totalScore,
  createdAt
}
```

### daily_challenges
```
{
  _id,
  date,        // YYYY-MM-DD in CST
  imageIds: [id1, id2, id3, id4, id5],
  createdAt
}
```

### leaderboards (optional materialized cache)
```
{
  _id,
  modeKey,
  timeframe,  // daily | weekly | alltime
  rankings: [{ userId, name, avgScore, gamesPlayed, totalPoints }],
  updatedAt
}
```

## 13) API Surface (Phase 1)
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me` (update display name)
- `POST /api/v1/games/start` (returns game + rounds)
- `POST /api/v1/games/{id}/round/{n}/guess`
- `GET /api/v1/leaderboard?mode=...&timeframe=...`
- `POST /api/v1/images/upload?code=...&environment=indoor|outdoor`

## 14) User Stories

### Authentication & Access
**A1 - Vanderbilt-only login**
- Acceptance Criteria:
  - Only `@vanderbilt.edu` emails can complete login.
  - Non-Vanderbilt emails are blocked with a clear error.
- Constraints:
  - Email domain validation is case-insensitive.
- Dependencies:
  - Auth0 tenant configuration and rules.
- Edge Cases:
  - Uppercase domains; missing email claim.
- Data Contracts:
  - `UserProfile`
- Telemetry (optional):
  - `auth_login_success`, `auth_login_denied`

**A2 - Auth failure handling**
- Acceptance Criteria:
  - Failed login shows an error and allows retry.
  - Users are not created on failed auth.
- Constraints:
  - Error is generic (no sensitive details).
- Dependencies:
  - Auth0 SDK error handling.
- Edge Cases:
  - Timeouts, canceled login, expired auth code.
- Data Contracts:
  - None

**A3 - Persistent session**
- Acceptance Criteria:
  - Users remain signed in between sessions when the token is valid.
  - Expired sessions return to login.
- Constraints:
  - Token refresh handled by Auth0 SDK.
- Dependencies:
  - Auth0 session/token storage.
- Edge Cases:
  - Clock skew; revoked tokens.
- Data Contracts:
  - `UserProfile`

### Profile & Identity
**B1 - Initialize profile from Auth0**
- Acceptance Criteria:
  - `name` defaults to Auth0 first + last on first login.
  - `email`, `username`, and `avatarUrl` are stored.
- Constraints:
  - `name` is editable after creation.
- Dependencies:
  - Auth0 profile claims.
- Edge Cases:
  - Missing first/last name; fallback to email local part.
- Data Contracts:
  - `UserProfile`

**B2 - Auto-generate username**
- Acceptance Criteria:
  - Username derived from email local part and normalized.
  - Collisions resolved with suffix.
- Constraints:
  - Usernames are unique.
- Dependencies:
  - User creation logic.
- Edge Cases:
  - Duplicate local parts; special characters.
- Data Contracts:
  - `UserProfile.username`

**B3 - Edit display name**
- Acceptance Criteria:
  - User can update their display name.
  - New name appears on leaderboard and profile.
- Constraints:
  - Non-empty string; length limit enforced.
- Dependencies:
  - `PATCH /api/v1/users/me`.
- Edge Cases:
  - Whitespace-only input.
- Data Contracts:
  - `UserProfile.name`

**B4 - Avatar menu and logout**
- Acceptance Criteria:
  - Avatar opens menu with Edit Profile and Logout.
  - Logout clears the session and returns to login.
- Constraints:
  - Avatar fallback when missing.
- Dependencies:
  - Auth0 logout flow.
- Edge Cases:
  - Missing avatar claim.
- Data Contracts:
  - `UserProfile.avatarUrl`

### Home & Mode Selection
**C1 - Display quick stats**
- Acceptance Criteria:
  - Rank, games played, points, and locations discovered are visible.
  - New users see zeros without errors.
- Constraints:
  - Stats calculated from completed games.
- Dependencies:
  - Stats service or aggregation.
- Edge Cases:
  - Missing stats data; show defaults.
- Data Contracts:
  - `UserProfile.stats`

**C2 - Select game mode**
- Acceptance Criteria:
  - User can choose Daily/Random and Timed/Untimed.
  - Indoor and Outdoor are mutually exclusive.
- Constraints:
  - Mode selection persists until Start Guessing.
- Dependencies:
  - Mode config schema.
- Edge Cases:
  - No images for a selected mode; show error.
- Data Contracts:
  - `GameSession.mode`

**C3 - Start game**
- Acceptance Criteria:
  - Creates a game session with 5 rounds.
  - Routes user to the gameplay view.
- Constraints:
  - Game creation is idempotent for double-clicks.
- Dependencies:
  - `POST /api/v1/games/start`.
- Edge Cases:
  - Insufficient images; return error.
- Data Contracts:
  - `GameSession`, `Round[]`

### Gameplay
**D1 - Load 360 image**
- Acceptance Criteria:
  - Round loads an equirectangular image successfully.
  - Viewer supports pan interaction.
- Constraints:
  - Image must be accessible via a public URL.
- Dependencies:
  - Photo Sphere Viewer, Spaces URL.
- Edge Cases:
  - Image load error; show retry.
- Data Contracts:
  - `Image.url`

**D2 - Place single pin**
- Acceptance Criteria:
  - User can place a single pin on the map.
  - Only one active pin exists at any time.
- Constraints:
  - Pin can be repositioned before submit.
- Dependencies:
  - Leaflet map and marker state.
- Edge Cases:
  - Multiple clicks; only latest pin remains.
- Data Contracts:
  - `Round.guessLatLng`

**D3 - Submit guess**
- Acceptance Criteria:
  - Guess button enabled only after a pin is placed.
  - After submit, input is locked for the round.
- Constraints:
  - One submission per round.
- Dependencies:
  - `POST /api/v1/games/{id}/round/{n}/guess`.
- Edge Cases:
  - Double submit; server handles idempotently.
- Data Contracts:
  - `RoundResult`

**D4 - Timed mode countdown**
- Acceptance Criteria:
  - Timer starts at 120 seconds when the image is ready.
  - Timer decrements once per second.
  - At 0 seconds: if pin exists, auto-submit; if not, submit with 0 score.
  - Timer stops after submission.
- Constraints:
  - Timer does not start before the image loads.
- Dependencies:
  - Viewer load event, guess submission endpoint.
- Edge Cases:
  - Tab switch; timer continues.
- Data Contracts:
  - `RoundResult`

### Results & Summary
**E1 - Distance calculation**
- Acceptance Criteria:
  - Distance between guess and true location is computed in meters.
  - Distance is included in the round results.
- Constraints:
  - Use geodesic distance (not pixel distance).
- Dependencies:
  - Distance utility.
- Edge Cases:
  - Guess outside campus bounds.
- Data Contracts:
  - `RoundResult.distanceMeters`

**E2 - Score calculation**
- Acceptance Criteria:
  - Score uses `5000 * e ^ (-10 * distance / size)`.
  - Score is rounded and not negative.
- Constraints:
  - `size` derived from campus bounding box.
- Dependencies:
  - Campus bounds config.
- Edge Cases:
  - Very large distances -> score = 0.
- Data Contracts:
  - `RoundResult.score`

**E3 - Round results display**
- Acceptance Criteria:
  - Round results show guess, actual, distance, and score.
  - Map shows a line between guess and actual.
- Constraints:
  - Data must render even if map tiles are slow to load.
- Dependencies:
  - `RoundResult` response.
- Edge Cases:
  - Missing location data; show error.
- Data Contracts:
  - `RoundResult`

**E4 - Next round flow**
- Acceptance Criteria:
  - “Next Round” advances to the next round.
  - After round 5, button changes to “See Results.”
- Constraints:
  - Navigation is idempotent.
- Dependencies:
  - Game state progression.
- Edge Cases:
  - Back navigation; guard against skipping rounds.
- Data Contracts:
  - `GameSession`

### Game Summary
**F1 - Summary totals**
- Acceptance Criteria:
  - Total score is displayed prominently.
  - Avg distance or avg score is shown.
- Constraints:
  - Summary uses final round data.
- Dependencies:
  - Game aggregation.
- Edge Cases:
  - Missing round data; show fallback.
- Data Contracts:
  - `GameSession.totalScore`

**F2 - Best and worst rounds**
- Acceptance Criteria:
  - Highest and lowest round scores are identified.
- Constraints:
  - If tie, show the earliest round.
- Dependencies:
  - Round results data.
- Edge Cases:
  - All rounds equal.
- Data Contracts:
  - `RoundResult[]`

**F3 - Per-round breakdown**
- Acceptance Criteria:
  - List of rounds with score and distance.
- Constraints:
  - Order matches round sequence.
- Dependencies:
  - Round results data.
- Edge Cases:
  - Missing distances; display “N/A.”
- Data Contracts:
  - `RoundResult[]`

**F4 - Summary actions**
- Acceptance Criteria:
  - “Play Again” starts a new game.
  - “Home” returns to mode selection.
  - “Leaderboard” opens leaderboard view.
- Constraints:
  - Actions available after full game completion.
- Dependencies:
  - Routing and game start.
- Edge Cases:
  - Rapid clicks; enforce idempotency.
- Data Contracts:
  - None

### Leaderboard
**G1 - View leaderboard**
- Acceptance Criteria:
  - Leaderboard renders a ranked list.
  - Default sort is avg score descending.
- Constraints:
  - Results are paginated.
- Dependencies:
  - Leaderboard query.
- Edge Cases:
  - No entries; show empty state.
- Data Contracts:
  - `LeaderboardEntry[]`

**G2 - Filter by mode and timeframe**
- Acceptance Criteria:
  - Mode and timeframe filters update the list.
  - Daily uses CST window.
- Constraints:
  - Filters are combinable.
- Dependencies:
  - Filterable leaderboard endpoint.
- Edge Cases:
  - No data for a filter; show empty state.
- Data Contracts:
  - `LeaderboardEntry[]`

**G3 - Highlight current user**
- Acceptance Criteria:
  - Current user row is visually distinct.
- Constraints:
  - Highlight applies even if user is off-page (optional).
- Dependencies:
  - User id in leaderboard data.
- Edge Cases:
  - User not ranked yet.
- Data Contracts:
  - `LeaderboardEntry`

**G4 - Pagination**
- Acceptance Criteria:
  - Next/previous pages load correctly.
  - Page size is consistent.
- Constraints:
  - Page size is configurable.
- Dependencies:
  - Leaderboard pagination API.
- Edge Cases:
  - Last page has fewer entries.
- Data Contracts:
  - `LeaderboardEntry[]`

### Daily Challenge
**H1 - Fixed daily set**
- Acceptance Criteria:
  - All users receive the same 5 images for the day.
  - Daily set is deterministic and cached.
- Constraints:
  - Daily set created once per day.
- Dependencies:
  - Daily challenge generator.
- Edge Cases:
  - Fewer than 5 images available.
- Data Contracts:
  - `DailyChallenge`

**H2 - CST reset**
- Acceptance Criteria:
  - Daily set rotates at CST midnight.
- Constraints:
  - Uses server time in CST.
- Dependencies:
  - Timezone handling.
- Edge Cases:
  - DST transitions.
- Data Contracts:
  - `DailyChallenge.date`

**H3 - Stable despite new uploads**
- Acceptance Criteria:
  - Daily set does not change after creation.
- Constraints:
  - Cached record reused for the day.
- Dependencies:
  - Daily challenge persistence.
- Edge Cases:
  - Uploads mid-day.
- Data Contracts:
  - `DailyChallenge.imageIds`

### Content Ingestion
**I1 - Upload image with EXIF**
- Acceptance Criteria:
  - Accepts 360 image with GPS EXIF.
  - Upload returns URL and metadata.
- Constraints:
  - File size limit enforced.
- Dependencies:
  - EXIF extraction and Spaces upload.
- Edge Cases:
  - Unsupported file types.
- Data Contracts:
  - `Image`, upload response

**I2 - Reject missing GPS**
- Acceptance Criteria:
  - Images missing GPS EXIF return 400.
- Constraints:
  - Error message is clear and actionable.
- Dependencies:
  - EXIF extraction.
- Edge Cases:
  - Corrupt EXIF data.
- Data Contracts:
  - Error response

**I3 - Require environment tag**
- Acceptance Criteria:
  - Upload requires `environment=indoor|outdoor`.
  - Mutually exclusive enforcement.
- Constraints:
  - Invalid values rejected.
- Dependencies:
  - Upload validation.
- Edge Cases:
  - Missing environment value.
- Data Contracts:
  - `Image.environment`

**I4 - Upload secret**
- Acceptance Criteria:
  - Upload requires a valid secret code.
  - Invalid or missing code returns 401.
- Constraints:
  - Secret is configured server-side.
- Dependencies:
  - Settings validation.
- Edge Cases:
  - Secret not configured -> 500.
- Data Contracts:
  - Error response

### Reliability
**J1 - Image load failure handling**
- Acceptance Criteria:
  - If the image fails to load, show retry.
  - Timer does not start until image is loaded.
- Constraints:
  - Retry is limited to avoid loops.
- Dependencies:
  - Viewer error hooks.
- Edge Cases:
  - Intermittent connectivity.
- Data Contracts:
  - None

**J2 - Map tile load failure handling**
- Acceptance Criteria:
  - If tiles fail, show a friendly error.
  - Guessing is disabled if map is unavailable.
- Constraints:
  - Provide a retry option.
- Dependencies:
  - Tile host availability.
- Edge Cases:
  - Partial tile failure.
- Data Contracts:
  - None

## 15) Non-Functional Requirements
- Smooth 360-degree interaction and fast map rendering
- Low operating cost with static tiles
- Minimal latency for leaderboard queries (Redis caching)

## 16) Risks & Mitigations
- Scope creep -> lock Phase 1 and defer extras
- Inaccurate metadata -> require EXIF GPS; reject otherwise
- Tile load performance -> static tiles + caching
- OSM data gaps -> adjust map styling and consider manual edits if needed
- Image size -> compress and limit max upload size

## 17) Future Features (Out of Scope)
- Multiplayer or AI mode
- User-uploaded images
- Gamemode variants beyond Phase 1
- Virtual tour mode
- Round multipliers and trivia facts
