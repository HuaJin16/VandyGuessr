# VandyGuessr — Design System & Visual Direction

## 1. Vision: "Vandy Safari"
**Theme:** A modern, tactile field expedition. "The Sims meets Google Maps."
**Vibe:** Adventurous, playful, crisp, and digital-native.
**Metaphor:** The UI is a "Field Kit". Cards are clean paper, buttons are physical tools/plastic, the map is the terrain.

---

## 2. Color Palette (The Expedition v2)
Use these exact hex codes to maintain the theme.

| Token | Hex | Usage |
| :--- | :--- | :--- |
| **Primary (Jungle)** | `#2E933C` | Main buttons (Start, Guess), Map Pin, Active states. Vibrant and fresh. |
| **Secondary (Gold)** | `#F4C430` | Highlights, Score counters, Medals, "Winner" states. |
| **Background (Terrain)** | `#F5F2E9` | The main app background. A warm, clean parchment/beige. |
| **Surface (Paper)** | `#FFFFFF` | Cards, Modals, Panels. Pure white to pop off the terrain. |
| **Text (Charcoal)** | `#18181B` | Primary text. Sharp, deep gray (not muddy). |
| **Error (Clay)** | `#D95D39` | Errors, Destructive actions, Timer < 10s. |

---

## 3. Typography
**Headings: Rubik** (Google Font)
*   **Weights:** Bold (700) or Medium (500).
*   **Feel:** Chunky, geometric, tactile. "Game UI" style.

**Body: Inter** (Google Font)
*   **Weights:** Regular (400), Medium (500).
*   **Feel:** Standard, neutral, highly legible, professional.

---

## 4. UI Physics & Shapes
*   **Borders:** Solid `1px` borders in muted gray or dark beige to define edges.
*   **Radius:**
    *   **Cards:** `16px` (Friendly).
    *   **Buttons:** `8px` or `12px` (Chunky).
*   **Shadows:** **Hard Shadows** (No blur). This creates the "Sims" / "Sticker" look.
    *   *CSS:* `box-shadow: 4px 4px 0px 0px rgba(0,0,0,0.1);`

---

## 5. Generator Prompts (High Fidelity)

### A. Logo Prompt (for Nano Banana Pro)
> **Prompt:** A minimalist vector logo for a location guessing game. A "Map Pin" icon stylized to look like a game piece or a jewel. The body of the pin is vibrant Jungle Green (#2E933C). The head/top of the pin has a highlight of Bright Gold (#F4C430). The pin is slightly tilted to the right. It casts a small, sharp, hard shadow beneath it. White background. Flat design, thick lines, playful, "Sims" aesthetic.

---

### B. UI Mockup Prompts (for Google Stitch)

#### 1. Login Screen (The Portal)
**Role:** Expert UI/UX Designer specializing in "Tactile" and "Gamified" interfaces.
**Subject:** High-fidelity login screen mockup for "VandyGuessr".

**ASCII Structure:**
```text
+-------------------------------------------------------+
|  (Background: Blurred Peabody Lawn Summer Photo)      |
|                                                       |
|          +---------------------------------+          |
|          | [ GLASS CARD CONTAINER ]        |          |
|          |                                 |          |
|          |  Welcome Back!                  |          |
|          |  (Heavy, Charcoal, Rubik Font)  |          |
|          |                                 |          |
|          |  +---------------------------+  |          |
|          |  | [ICON] Log in with School |  |          |
|          |  +---------------------------+  |          |
|          |  (Button: Green Plastic, 3D)    |          |
|          |                                 |          |
|          +---------------------------------+          |
+-------------------------------------------------------+
```

**Visual Description:**
The background is a vibrant, sunny photograph of the "Peabody Lawn" at Vanderbilt University during summer. Lush green grass and historic buildings are visible but treated with a strong "Gaussian Blur" (approx 20px radius) and a "Warm Parchment Beige" (#F5F2E9) overlay at 80% opacity. This creates a soft, nostalgic, and textured backdrop.

Floating in the dead center is a "Glassmorphism" login modal. Translucent white, frosted glass effect, 24px rounded corners. It casts a "Hard Shadow" (no blur, dark grey) to the bottom-right, looking like a sticker or cutout.

Inside: a Vanderbilt-first sign-in card with the Microsoft CTA always present. When Vanderbilt restriction is disabled, a second Google CTA appears beneath it with matching weight and spacing. Supporting copy explains the campus-competition premise and keeps the entry flow focused on a single decision: which provider to use.

#### 2. Home / Start Game Menu (The Field Kit)
**Role:** Expert Game UI Designer.
**Subject:** High-fidelity home screen mockup.

**ASCII Structure:**
```text
+-------------------------------------------------------+
|  VandyGuessr              [Avatar] Player One     v   |
+-------------------------------------------------------+
|  (Background: Solid Warm Beige #F5F2E9)               |
|                                                       |
|  +----------------+   +---------------------------+   |
|  | LEFT PANEL     |   | RIGHT PANEL (Menu)        |   |
|  | (Passport)     |   |                           |   |
|  | [Avatar]       |   |  DAILY CHALLENGE [Gold]   |   |
|  | Player One     |   |  (Large Action Row)       |   |
|  | Rank: #42      |   |                           |   |
|  | Score: 15k     |   |  Random Drop              |   |
|  | (Clean White)  |   |  (Standard Row)           |   |
|  +----------------+   |                           |   |
|                       |  Indoor Mode              |   |
|                       |  (Standard Row)           |   |
|                       |                           |   |
|                       |  Timed Mode               |   |
|                       |  (Standard Row)           |   |
|                       +---------------------------+   |
+-------------------------------------------------------+
```

**Visual Description:**
Set against a solid "Warm Beige" (#F5F2E9) background.

**Left Panel:** A vertical white "Identity Card" or passport. Contains User Avatar, Name "Player One", quick rank/stats, and active game resume cards for solo or multiplayer.

**Center Panel:** Solo game setup with a strong Daily Challenge hero action, then configurable Random Drop controls for timing, environment, and difficulty.

**Right Panel:** Multiplayer tools. One card creates a lobby, another joins by invite code, and both visually feel like sturdy expedition equipment rather than admin forms. Recent completed games can sit below the setup panels as compact logbook entries.

#### 3. Gameplay (The Explorer's View)
**Role:** Expert UI Designer for immersive web games.
**Subject:** First-person gameplay screen mockup.

**ASCII Structure:**
```text
+-------------------------------------------------------+
|   [ PILL:  Round 3/5  |  Score 4500  |  01:23  ]      |
+-------------------------------------------------------+
|                                                       |
|           ( FULL SCREEN 360 CAMPUS PHOTO )            |
|                                                       |
|                                     +---------------+ |
|                                     |  MINI MAP     | |
|                                     | [ Sepia Map ] | |
|                                     |      |        | |
|                                     |    (Pin)      | |
|                                     |               | |
|                                     +---------------+ |
|                                     | [ GUESS ]     | |
|                                     +---------------+ |
+-------------------------------------------------------+
```

**Visual Description:**
Immersive 360-degree street view of campus.
**Top:** Floating white "Status Pill" with Round, Score, Timer (Orange text).
**Bottom Right:** "Map Assembly". A rectangular map container with rounded corners. The map is "Sepia / Paper" toned (not blue). A "Jungle Green" pin is sticking out of it. Attached to the bottom of the map is a wide, thick "GUESS" button in Green (#2E933C) with a hard 3D shadow.

#### 4. Round Results (The Debrief)
**Role:** Expert UI Designer.
**Subject:** Round Results screen mockup.

**ASCII Structure:**
```text
+-------------------------------------------------------+
|                                                       |
|     ( LARGE MAP VIEW - SEPIA TONED - TOP 70% )        |
|                                                       |
|         (User Guess)          (Actual Location)       |
|          [Green Pin] - - - - - - [Gold Flag]          |
|                 \                   /                 |
|                  \___ "125m" ____/                    |
|                                                       |
|  +-------------------------------------------------+  |
|  |  [ BOTTOM SHEET / RESULT CARD ]                 |  |
|  |                                                 |  |
|  |  ROUND SCORE              [ Gold Medal Icon ]   |  |
|  |  4,850 pts                                      |  |
|  |                                                 |  |
|  |          [ BUTTON: NEXT ROUND > ]               |  |
|  +-------------------------------------------------+  |
+-------------------------------------------------------+
```

**Visual Description:**
**Top 70%:** Large Sepia Map. Dashed line connects User Pin (Green) to Actual Location (Gold Flag). Label "125m".
**Bottom 30%:** Sliding White Sheet. Huge text "4,850 pts" in Rubik Bold (Green). Gold Medal icon. Large "Next Round" button at the bottom.

#### 5. Leaderboard (The Hall of Fame)
**Role:** Expert UI Designer.
**Subject:** Leaderboard table mockup.

**ASCII Structure:**
```text
+-------------------------------------------------------+
| < Back                  LEADERBOARD                   |
+-------------------------------------------------------+
|  (Background: Warm Beige #F5F2E9)                     |
|                                                       |
|  [Daily | All Time]     [Indoor | Outdoor]            |
|   (Green Toggle)         (Gray Toggle)                |
|                                                       |
|  +-------------------------------------------+        |
|  |  #   PLAYER           SCORE     GAMES     |        |
|  |  ---------------------------------------  |        |
|  |  1   Player One [Gold] 24,950    142      |        |
|  |  2   Player Two [Slvr] 23,100    88       |        |
|  |  3   Player Three [Brz] 21,000   12       |        |
|  |  ...                                      |        |
|  |  ---------------------------------------  |        |
|  |  42  YOU (Highlight)  15,200    12        |        |
|  +-------------------------------------------+        |
|   (Card: White with Hard Shadow)                      |
+-------------------------------------------------------+
```

**Visual Description:**
Vertical White Card on Beige background. Hard shadow.
**Header:** Pill toggles for filters.
**Table:** Clean, uppercase headers.
**Rows 1-3:** Gold/Silver/Bronze icons.
**Row 42 (YOU):** Highlighted with "Pale Gold" (#F4C430 @ 20%) background. Bold text.

---

## 6. Responsive Design (Mobile-First)

VandyGuessr is designed mobile-first. Students will primarily use it on their phones between classes.

### Breakpoints
| Breakpoint | Width | Tailwind Prefix | Usage |
| :--- | :--- | :--- | :--- |
| **Mobile** | < 640px | (default) | Primary target, single column layouts |
| **Tablet** | 640px - 1023px | `sm:` | Slightly larger touch targets, show secondary info |
| **Desktop** | 1024px+ | `lg:` | Full layouts, hover interactions enabled |

### Mobile-First Principles
1. **Touch Targets:** Minimum 44x44px for all interactive elements (buttons, links, cards)
2. **Typography:** Body text minimum 14px (`text-sm`), never smaller for readability
3. **Spacing:** Generous padding (16px minimum) to prevent mis-taps
4. **Content Priority:** Show essential info first, progressive disclosure for details
5. **Bottom Sheets:** Use slide-up panels for results/modals (thumb-friendly)

### Component Adaptations

#### Navbar
- **Mobile:** Logo only (no text), icon-only buttons
- **Desktop:** Logo + "VandyGuessr" text, full button labels

#### HUD Pill (Gameplay)
- **Mobile:** Compact spacing, smaller text (`text-[10px]`)
- **Desktop:** Standard spacing, normal text

#### Map Assembly (Gameplay)
- **Mobile:** Full-width, collapsed by default so the panorama stays dominant; tap to expand the map, place or adjust the pin, then collapse it again
- **Desktop:** Anchored bottom-right with a roomy collapsed state and a larger expanded state for fine pin placement

#### Leaderboard Table
- **Mobile:** Hide "Class of" secondary text, compact avatar (32px)
- **Desktop:** Show all columns, larger avatars (40px)

---

## 7. Component Library

### A. Navbar (Standard)
Used on: Start Game, Leaderboard
```
Background: #FFFFFF (white)
Height: 56px mobile, 64px desktop
Border: 1px solid rgba(0,0,0,0.05) bottom
Shadow: none

Left:   Logo (32-40px) + "VandyGuessr" (Rubik Bold, hidden on mobile)
Right:  Nav links + Logout button (icon + text, text hidden on mobile)
```

### B. Glass Card
Used on: Login, Start Game (main card)
```css
.glass-card {
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.5);
    box-shadow: 6px 6px 0px 0px rgba(0,0,0,0.12);
}
```

### C. HUD Pill
Used on: Gameplay, Round Results
```css
.hud-pill {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(12px);
    border-radius: 9999px;
    padding: 8px;
    border: 1px solid rgba(255, 255, 255, 0.5);
    box-shadow: 4px 4px 0px 0px rgba(0,0,0,0.1);
}
```
**Contents:** Round counter | Score | Timer (separated by 1px dividers)

### D. Map Assembly (Gameplay)
```css
.map-assembly {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    transform-origin: bottom right;
}

/* Mobile: Full width */
@media (max-width: 639px) {
    .map-assembly { width: 100%; }
    .map-container { width: 100%; height: 0; }
    .map-assembly.expanded .map-container { height: min(42dvh, 320px); }
}

/* Desktop: Expandable */
@media (min-width: 1024px) {
    .map-assembly { width: 340px; }
    .map-container { width: 340px; height: 220px; }

    .map-assembly.expanded { width: 480px; }
    .map-assembly.expanded .map-container { width: 480px; height: 320px; }
}
```

### E. 3D Button
Used on: Primary actions (Login, Guess, Next Round)
```css
.btn-3d {
    background: #2E933C;
    color: white;
    font-family: "Rubik", sans-serif;
    font-weight: 700;
    padding: 16px 24px;
    border-radius: 12px;
    box-shadow: 0 6px 0 #236E2D;
    transition: transform 0.1s, box-shadow 0.1s;
}

.btn-3d:hover {
    background: #236E2D;
}

.btn-3d:active {
    transform: translateY(6px);
    box-shadow: 0 0px 0 #236E2D;
}
```

### F. Mode Row (Start Game)
```css
.mode-row {
    background: white;
    border-radius: 16px;
    padding: 16-20px;
    border: 1px solid rgba(0,0,0,0.05);
    transition: all 0.15s;
}

.mode-row:hover {
    transform: translateX(4px);
    background: rgba(46, 147, 60, 0.05);
}

/* Daily Challenge variant */
.mode-row.hero {
    border: 2px solid #F4C430;
    background: linear-gradient(to right, rgba(244,196,48,0.15), transparent);
}
```

### G. Initials Avatar
```css
.avatar-initials {
    background: linear-gradient(135deg, #2E933C 0%, #236E2D 100%);
    border-radius: 50%;
    color: white;
    font-family: "Rubik", sans-serif;
    font-weight: 700;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Sizes */
.avatar-sm { width: 32px; height: 32px; font-size: 12px; }
.avatar-md { width: 40px; height: 40px; font-size: 14px; }
.avatar-lg { width: 56px; height: 56px; font-size: 18px; }
```

### H. Toggle Pills (Filters)
```css
.toggle-group {
    background: white;
    border-radius: 9999px;
    padding: 4px;
    box-shadow: 4px 4px 0px 0px rgba(0,0,0,0.1);
}

.toggle-active {
    background: #2E933C;
    color: white;
    border-radius: 9999px;
    padding: 6-8px 12-16px;
    font-weight: 600;
}

.toggle-inactive {
    background: transparent;
    color: #18181B;
    border-radius: 9999px;
    padding: 6-8px 12-16px;
}

.toggle-inactive:hover {
    background: rgba(46, 147, 60, 0.1);
}
```

### I. Confirmation Dialog
Used on: End Game, Delete Account, other destructive/important actions

**Structure:**
```
Backdrop (click to dismiss)
└── Dialog Card
    ├── Icon (optional, in colored circle)
    ├── Title (Rubik Bold)
    ├── Description (optional)
    ├── Stats Block (optional, for context)
    ├── Warning Notice (optional)
    └── Action Buttons (Cancel + Confirm)
```

**Backdrop:**
```css
.dialog-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    z-index: 50;
}
```

**Dialog Card:**
```css
.dialog-card {
    width: 100%;
    max-width: 448px; /* max-w-md */
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(24px);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.5);
    box-shadow: 6px 6px 0px 0px rgba(0,0,0,0.15);
    padding: 24px; /* mobile */
    padding: 32px; /* desktop (sm:) */
}
```

**Icon Container:**
```css
.dialog-icon {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Variants */
.dialog-icon.warning { background: rgba(217, 93, 57, 0.1); } /* clay/10 */
.dialog-icon.success { background: rgba(46, 147, 60, 0.1); } /* jungle/10 */
.dialog-icon.info { background: rgba(244, 196, 48, 0.1); }    /* gold/10 */
```

**Typography:**
- **Title:** `font-heading font-bold text-2xl text-charcoal text-center`
- **Description:** `text-charcoal/60 text-center`

**Stats Block (optional context):**
```css
.dialog-stats {
    background: #F5F2E9; /* terrain */
    border-radius: 12px;
    padding: 16px;
}
/* Use grid-cols-2 gap-4 for two-column layout */
/* Label: text-[10px] uppercase tracking-wider text-charcoal/50 */
/* Value: font-mono font-bold text-2xl */
```

**Warning Notice (optional):**
```css
.dialog-notice {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 16px;
    border-radius: 12px;
}

.dialog-notice.warning {
    background: rgba(217, 93, 57, 0.05);
    border: 1px solid rgba(217, 93, 57, 0.2);
}
/* Icon: text-clay text-lg */
/* Text: text-sm text-charcoal/70 */
```

**Action Buttons:**
```css
/* Container */
.dialog-actions {
    display: flex;
    gap: 12px;
}

/* Cancel (Ghost) */
.btn-ghost {
    flex: 1;
    padding: 12px 24px;
    border-radius: 12px;
    border: 2px solid rgba(24, 24, 27, 0.2);
    color: #18181B;
    font-weight: 600;
    transition: background 0.15s;
}
.btn-ghost:hover {
    background: rgba(24, 24, 27, 0.05);
}

/* Destructive */
.btn-destructive {
    flex: 1;
    padding: 12px 24px;
    border-radius: 12px;
    background: #D95D39;
    color: white;
    font-weight: 600;
    box-shadow: 4px 4px 0px 0px rgba(0,0,0,0.1);
    transition: background 0.15s;
}
.btn-destructive:hover {
    background: rgba(217, 93, 57, 0.9);
}
```

### J. Ghost Button (Secondary Actions)
Used on: End Game trigger, Cancel actions, subtle controls
```css
.btn-ghost-subtle {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255, 255, 255, 0.5);
    box-shadow: 4px 4px 0px 0px rgba(0,0,0,0.1);
    color: rgba(24, 24, 27, 0.7);
    font-size: 14px;
    font-weight: 500;
    transition: all 0.15s;
}

.btn-ghost-subtle:hover {
    color: #D95D39; /* clay - for destructive hint */
    background: rgba(255, 255, 255, 0.95);
}
```

---

## 8. Screen-Specific Notes

### Login (01-login.html)
- **No navbar** - branding is inside the centered card
- Card contains: Logo → App name → Divider → Welcome text → Login button
- Footer text below card

### Start Game (02-start-game.html)
- **White navbar** with logo, Leaderboard link, Logout button
- Centered glass card with user stats header + game mode rows
- Mobile: Stats row moves below user info

### Gameplay (03-gameplay.html)
- **No navbar** - immersive full-screen
- **End Game button** top-left corner (ghost style, shows "X" icon on mobile, "End Game" text on desktop)
- HUD pill at top center
- Side controls (zoom, compass) on right (desktop only)
- Map assembly stays collapsible on mobile and expands via toggle on desktop
- End Game button hidden on round 5 (game about to end anyway)

### End Game Dialog (06-end-game-dialog.html)
- **Triggered from:** End Game button on gameplay screen
- **Backdrop:** Semi-transparent black with blur, click to dismiss
- **Dialog:** Warning icon, title "End Game Early?", description
- **Stats block:** Shows rounds completed (X/5) and current score
- **Warning notice:** Explains remaining rounds will score 0
- **Buttons:** Cancel (ghost) + End Game (destructive clay color)

### Round Results (04-round-results.html)
- **No navbar** - seamless from gameplay
- HUD pill at top (shows completed round)
- Sepia map with pins + dashed line + distance label
- Bottom sheet slides up with score, stats, Next Round button
- No exit button

### Leaderboard (05-leaderboard.html)
- **White navbar** with Back, Logo, Logout
- Filter toggles below navbar
- Table card with ranks, avatars, scores
- User row highlighted with gold accent
- Stats summary cards at bottom
