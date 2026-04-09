# VandyGuessr Wireframes

## Goal
Rebuild the frontend around low-density, gameplay-first layouts that feel consistent across solo play, multiplayer, contribution, and ranking flows.

## Non-Goals
- Final visual polish, illustration, or motion specs
- New product features or route changes
- Color-only experimentation without layout/system changes

## Core Principles
- One dominant action per screen
- Gameplay pages should feel immersive, not dashboard-like
- Utility pages should feel calm and highly scannable
- Resume always outranks start-new when relevant
- Use fewer surface types, not more
- Keep green as the primary action color, but do not let color compensate for weak hierarchy

## Density Rules
- Avoid three equal-weight columns unless all three are truly primary
- Avoid nested cards inside cards
- Avoid using border, shadow, tint, and heavy padding all at once on every surface
- Keep secondary explanatory copy short
- Push secondary data below the fold or into compact rows/chips

## Spacing Scale
- `8 / 12 / 16 / 24 / 32 / 48 / 64`

## Width Rules
- `narrow`: `560-640px`
- `content`: `880-1040px`
- `wide`: `1160-1280px`
- `immersive`: full bleed

## Surface Rules
- Default container: white or near-white surface with a low-contrast border
- Default elevation: very soft shadow only where separation matters
- Primary CTA: strongest color emphasis on the page
- Overlay HUDs: translucent dark or light pills, never thick framed cards

## Shared States

### Loading
```text
+------------------------------------------------------+
|                                                      |
|                    [ spinner ]                       |
|                    Loading...                        |
|                                                      |
+------------------------------------------------------+
```

### Empty
```text
+------------------------------------------------------+
|                  Nothing here yet                    |
|        Finish a game or add content to get started   |
|                                                      |
|                    [ Go Home ]                       |
+------------------------------------------------------+
```

### Error
```text
+------------------------------------------------------+
|               Something went wrong                   |
|          We couldn't load this right now.            |
|                                                      |
|          [ Retry ]           [ Go Home ]             |
+------------------------------------------------------+
```

### Forbidden
```text
+------------------------------------------------------+
|                 You don't have access                |
|         This page is only available to reviewers.    |
|                                                      |
|                    [ Go Home ]                       |
+------------------------------------------------------+
```

## Shells

### Portal Shell
Used by login and other single-decision entry screens.

### Field Kit Shell
Used by home, leaderboard, upload, review, and history pages.

### Immersive Play Shell
Used by solo and multiplayer gameplay.

### Debrief Shell
Used by round results, summaries, and standings.

## Page Wireframes

### 1. Login
```text
+----------------------------------------------------------------------------------+
|                                                                                  |
|                                  [logo] VandyGuessr                              |
|                                                                                  |
|                        How well do you know campus?                              |
|            Explore real Vanderbilt locations, place your pin, climb the ranks.   |
|                                                                                  |
|                    +------------------------------------------+                  |
|                    | [ Microsoft ] Continue with Vanderbilt   |                  |
|                    +------------------------------------------+                  |
|                                                                                  |
|                    +------------------------------------------+                  |
|                    | [ Google ] Continue with Google          |                  |
|                    +------------------------------------------+                  |
|                                                                                  |
|                         [ auth error / provider status ]                         |
|                                                                                  |
|        See a real place        Drop your pin         Climb the ranks             |
|                                                                                  |
+----------------------------------------------------------------------------------+
```

### 2. Home
```text
+----------------------------------------------------------------------------------+
| Home         Leaderboard         Upload         Review?               [Avatar v] |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------+
| RESUME                                                                           |
|----------------------------------------------------------------------------------|
| [ Solo game in progress ]  Round 2/5  6,820 pts          [ Resume ]             |
| [ Multiplayer lobby ]      4 players  Code ABCD12        [ Open Lobby ]         |
+----------------------------------------------------------------------------------+

+----------------------------------------------------+-----------------------------+
| SOLO PLAY                                          | MULTIPLAYER                 |
|----------------------------------------------------|-----------------------------|
| Daily Challenge                                    | Create Match                |
| Large featured entry point                         | [ Environment ]             |
| [ Play Daily ]                                     | [ Create Match ]            |
|                                                    |                             |
| Random Drop                                        | Join Match                  |
| [ Timed/Untimed ]                                  | [ Invite Code ______ ]      |
| [ Environment ]                                    | [ Join ]                    |
| [ Difficulty ]                                     |                             |
| [ Start Guessing ]                                 |                             |
+----------------------------------------------------+-----------------------------+

+----------------------------------------------------+-----------------------------+
| QUICK STATS                                        | RECENT GAMES                |
|----------------------------------------------------|-----------------------------|
| Rank      Games      Points      Locations         | row                         |
| compact, not oversized                             | row                         |
|                                                    | row                         |
+----------------------------------------------------+-----------------------------+
```

### 3. Game History
```text
+----------------------------------------------------------------------------------+
| GAME HISTORY                                                                     |
| Completed and abandoned solo runs                                                |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------+
| Apr 6, 8:42 PM      Completed      Timed Random Drop · Outdoor      18,740 pts  |
|                                                                    [ > ]         |
+----------------------------------------------------------------------------------+
| Apr 5, 3:14 PM      Abandoned      Daily Challenge                   5,200 pts   |
|                                                                    [ > ]         |
+----------------------------------------------------------------------------------+
| Apr 4, 9:30 PM      Completed      Untimed Random Drop · Indoor     21,100 pts  |
|                                                                    [ > ]         |
+----------------------------------------------------------------------------------+
```

### 4. Solo Gameplay
```text
+----------------------------------------------------------------------------------+
| [End Game]                  Round 2 / 5        Score 6,820        Time 01:24     |
+----------------------------------------------------------------------------------+
|                                                                                  |
|                             360 PANORAMA VIEWER                                  |
|                                                                                  |
|                                                               +--------------+   |
|                                                               | mini map     |   |
|                                                               | tap/hover    |   |
|                                                               | to expand    |   |
|                                                               +--------------+   |
+----------------------------------------------------------------------------------+
| Pin status: not placed yet                             [ Guess ]   [ Recenter ]  |
+----------------------------------------------------------------------------------+
```

### 5. End Game Dialog
```text
+----------------------------------------------------------------------------------+
|                           dimmed gameplay background                             |
|                                                                                  |
|                    +------------------------------------------+                  |
|                    | End this game?                           |                  |
|                    | Rounds completed: 2/5                    |                  |
|                    | Current score: 6,820                     |                  |
|                    | Remaining rounds will score 0.           |                  |
|                    | [ Cancel ]          [ End Game ]         |                  |
|                    +------------------------------------------+                  |
|                                                                                  |
+----------------------------------------------------------------------------------+
```

### 6. Solo Round Results
```text
+----------------------------------------------------------------------------------+
| ROUND 2 RESULTS                                                   +4,320 pts     |
| Kirkland Hall                                                        86m away    |
+----------------------------------------------------------------------------------+

+------------------------------------+---------------------------------------------+
| ROUND SNAPSHOT                     | RUN SUMMARY                                 |
|------------------------------------|---------------------------------------------|
| Score       4,320                  | Total so far        6,820                   |
| Distance    86m                    | Avg score           3,410                   |
| Quality     Strong guess           | Round marker        2 / 5                   |
+------------------------------------+---------------------------------------------+

+----------------------------------------------------------------------------------+
|                         MAP: guess vs actual + line                              |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------+-----------------------+
| Round progress: [1] [2 active] [3] [4] [5]              | [ Next Round ]        |
|                                                          | or [ See Results ]    |
+----------------------------------------------------------+-----------------------+
```

### 7. Solo Summary
```text
+----------------------------------------------------------------------------------+
| FINAL SCORE                                                                      |
| [ Timed ] [ Outdoor ] [ Random Drop ] [ Hard ]                    18,740 points |
+----------------------------------------------------------------------------------+

+--------------------------------------+-------------------------------------------+
| TOPLINE                              | PER-ROUND BREAKDOWN                       |
|--------------------------------------|-------------------------------------------|
| Avg score                            | R1   4,820   41m   Kirkland Hall         |
| Avg distance                         | R2   4,320   86m   Alumni Lawn           |
| Best round                           | R3   2,100   410m  Unknown location      |
| Worst round                          | R4   3,700   120m  Wyatt Center          |
|                                      | R5   3,800   95m   Commons               |
+--------------------------------------+-------------------------------------------+

+--------------------------------------+-------------------------------------------+
| MINI VISUALS                         | NEXT                                      |
|--------------------------------------|-------------------------------------------|
| per-round bars                       | [ Play Again ]                            |
| best/worst highlights                | [ Home ]                                  |
| optional share                       | [ Leaderboard ]                           |
| [ Share Results ]                    |                                           |
+--------------------------------------+-------------------------------------------+
```

### 8. Leaderboard
```text
+----------------------------------------------------------------------------------+
| LEADERBOARD                                                  [Env] [Timeframe]   |
+----------------------------------------------------------------------------------+

+----------------------------------------------------------------------------------+
| Rank | Player                  | Avg Score | Games | Rounds | Points            |
|------|-------------------------|-----------|-------|--------|-------------------|
| 1    | Ava Carter              | 4,380     | 32    | 160    | 140,200           |
| 2    | You                     | 4,210     | 18    | 90     | 75,820            |
| 3    | Marcus Lee              | 4,130     | 25    | 125    | 103,400           |
| ...                                                                          ... |
+----------------------------------------------------------------------------------+

+--------------------------------------+-------------------------------------------+
| Your rank / percentile               | [ Prev ]                     [ Next ]      |
+--------------------------------------+-------------------------------------------+
```

### 9. Upload
```text
+----------------------------------------------------------------------------------+
| UPLOAD A CAMPUS PHOTO                                                            |
| Photos are reviewed before they appear in rounds.                                |
+----------------------------------------------------------------------------------+

+----------------------------------------------------+-----------------------------+
| SUBMISSION                                         | GUIDELINES                  |
|----------------------------------------------------|-----------------------------|
| [ Indoor / Outdoor ]                               | Needs GPS EXIF              |
| [ Choose files ]                                   | JPEG / PNG / HEIC           |
| 6 ready                                            | No screenshots              |
| 2 failed pre-check                                 | Queued for processing       |
| file.jpg            ready                          |                             |
| photo.heic          missing GPS                    |                             |
| pano.png            unsupported                    |                             |
| [ Submit for Review ]                              |                             |
+----------------------------------------------------+-----------------------------+

+----------------------------------------------------------------------------------+
| QUEUE RESULT                                                                     |
| 6 queued, 2 failed                                                               |
| [ failure reasons if needed ]                                                    |
+----------------------------------------------------------------------------------+
```

### 10. Review Submissions
```text
+----------------------------------------------------------------------------------+
| REVIEW SUBMISSIONS                                                               |
| Approve photos to add them to the playable pool.                                 |
+----------------------------------------------------------------------------------+

+-------------------+--------------------------------------------------------------+
| thumbnail         | Outdoor                                                      |
| [ preview ]       | Kirkland Hall                                                 |
|                   | Submitted by Jane Doe · jane@vanderbilt.edu                  |
|                   | Apr 6, 8:42 PM                                                |
|                   | [ Preview as Round ]   [ Approve ]   [ Reject ]              |
+-------------------+--------------------------------------------------------------+

+-------------------+--------------------------------------------------------------+
| thumbnail         | Indoor                                                       |
| [ preview ]       | Unknown location                                              |
|                   | Submitted by Ryan                                             |
|                   | Apr 6, 7:14 PM                                                |
|                   | [ Preview as Round ]   [ Approve ]   [ Reject ]              |
+-------------------+--------------------------------------------------------------+
```

### 11. Profile Sheet
```text
+----------------------------------------------+
| [ avatar ] Ryan McCauley                     |
| ryan@vanderbilt.edu                          |
|----------------------------------------------|
| Display name                                 |
| [ Ryan McCauley________________________ ]    |
| [ Save ]                                     |
|----------------------------------------------|
| Logout                                       |
+----------------------------------------------+
```

### 12. Multiplayer Join by Link
```text
+------------------------------------------------------+
|                                                      |
|                    [ spinner ]                       |
|                  Joining match...                    |
|                                                      |
+------------------------------------------------------+
```

### 13. Multiplayer Lobby
```text
+----------------------------------------------------------------------------------+
|                                  MATCH LOBBY                                     |
|                                 Code: ABCD12                                     |
+----------------------------------------------------------------------------------+

+--------------------------------------+-------------------------------------------+
| MATCH STATUS                         | PLAYERS                                   |
|--------------------------------------|-------------------------------------------|
| Environment: Outdoor                 | Host  Ava        connected   ready        |
| Connection: Connected                | You   Ryan       connected   ready        |
| Lobby expiry / extension notice      | Sam   Sam        disconnected             |
| [ Copy Code ] [ Share Link ]         | Jules Jules      connected   ready        |
+--------------------------------------+-------------------------------------------+

+----------------------------------------------------------------------------------+
| [ Ready Up ]   [ Start Match ]   [ Extend Lobby ]   [ Leave Lobby ]             |
+----------------------------------------------------------------------------------+
```

### 14. Multiplayer Countdown
```text
+----------------------------------------------------------------------------------+
|                           dimmed lobby / pano background                         |
|                                                                                  |
|                                   MATCH STARTING                                 |
|                                         3                                        |
|                              Get ready to place your pin                         |
|                                                                                  |
+----------------------------------------------------------------------------------+
```

### 15. Multiplayer Gameplay
```text
+----------------------------------------------------------------------------------+
| Round 3 / 5    Ava 12.3k   You 11.9k   Jules 10.7k                 Time 00:42    |
| guessed: Ava, Jules                 reconnecting: Sam (22s)                      |
+----------------------------------------------------------------------------------+
|                                                                                  |
|                             360 PANORAMA VIEWER                                  |
|                                                                                  |
|                                                               +--------------+   |
|                                                               | mini map     |   |
|                                                               | expandable   |   |
|                                                               +--------------+   |
+----------------------------------------------------------------------------------+
| Pin status / connection status                [ Guess ]       [ Forfeit ]        |
+----------------------------------------------------------------------------------+
```

### 16. Multiplayer Round Results
```text
+----------------------------------------------------------------------------------+
| ROUND 3 RESULTS                                                                  |
| Correct location: Alumni Lawn                                                    |
+----------------------------------------------------------------------------------+

+--------------------------------------+-------------------------------------------+
| ROUND STANDINGS                      | TOTAL STANDINGS                           |
|--------------------------------------|-------------------------------------------|
| 1. Ava        4,980   8m             | 1. Ava        12,320                      |
| 2. You        4,710   36m            | 2. You        11,940                      |
| 3. Jules      4,100   98m            | 3. Jules      10,780                      |
| 4. Sam        0       no guess       | 4. Sam         6,200                      |
+--------------------------------------+-------------------------------------------+

+----------------------------------------------------------------------------------+
|                           MAP: all guesses vs actual                             |
+----------------------------------------------------------------------------------+

+------------------------------------------------------+---------------------------+
| Ready for next round: 3 / 4                          | [ Ready ]                 |
+------------------------------------------------------+---------------------------+
```

### 17. Multiplayer Final Standings
```text
+----------------------------------------------------------------------------------+
|                               MATCH COMPLETE                                     |
|                                  Ava Wins                                        |
+----------------------------------------------------------------------------------+

+--------------------------------------+-------------------------------------------+
| FINAL STANDINGS                      | MATCH STORY                               |
|--------------------------------------|-------------------------------------------|
| 1. Ava         18,420                | R1 Ava                                    |
| 2. You         17,980                | R2 You                                    |
| 3. Jules       15,200                | R3 Ava                                    |
| 4. Sam          9,400                | R4 Jules                                  |
|                                      | R5 Ava                                    |
+--------------------------------------+-------------------------------------------+

+----------------------------------------------------------------------------------+
| [ Rematch ]                             [ Home ]                 [ Leaderboard ] |
+----------------------------------------------------------------------------------+
```

## Do / Don't

### Do
- Let panorama and maps dominate gameplay pages
- Use one strong CTA per screen
- Keep stats compact and contextual
- Reuse the same shells and row patterns across utility pages
- Keep reviewer and upload flows operationally clear, not decorative

### Don't
- Build a multi-column dashboard for every route
- Put every block into a raised card
- Use strong shadows everywhere
- Let home, gameplay, and summary share the same density level
- Add more chrome to gameplay to make it feel “complete”
