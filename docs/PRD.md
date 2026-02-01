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

### Authentication & Profile
- As a Vanderbilt student, I can log in using my Vanderbilt email.
- As a user, I see an error if my login fails or my email is not Vanderbilt.
- As a user, I can view my profile avatar and name.
- As a user, I can edit my display name.

### Home & Mode Selection
- As a user, I can see my stats (rank, games played, points, locations discovered).
- As a user, I can choose a game mode (daily, random, indoor, outdoor, timed, untimed).
- As a user, I can start a game from the home screen.

### Gameplay
- As a user, I can view a 360-degree image for the current round.
- As a user, I can place a single pin on the map to make a guess.
- As a user, I can adjust my pin before submitting.
- As a user, I can submit my guess only after placing a pin.
- As a user, I can see the timer if I chose timed mode.

### Results & Summary
- As a user, I can see the correct location and my guess after a round.
- As a user, I can see my round score and distance.
- As a user, I can progress to the next round.
- As a user, I can see a final game summary after 5 rounds.
- As a user, I can view total score and per-round performance.

### Leaderboard
- As a user, I can view a campus leaderboard.
- As a user, I can filter the leaderboard by mode and timeframe.
- As a user, I can see my rank highlighted.

### Content Ingestion
- As an uploader, I can submit a 360 image with GPS EXIF.
- As the system, I reject images without GPS EXIF.
- As the system, I store the image in Spaces and save its location.

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
