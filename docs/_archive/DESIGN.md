# Design System Document: Kinetic Cyber-Editorial

## 1. Overview & Creative North Star: "The Neon Brutalist"
This design system rejects the "flat and friendly" aesthetics of corporate SaaS in favor of a high-octane, editorial experience tailored for the elite esports tier. Our Creative North Star is **"The Neon Brutalist."** 

We achieve this by blending the raw, unapologetic structure of architectural brutalism—sharp 0px corners and heavy type—with a futuristic "cyber-glitch" layer. We break the template look through **intentional asymmetry**, where bracket lines might feel like high-voltage conduits and content bleeds off-canvas to suggest a world larger than the viewport. This is not just a dashboard; it is a digital arena.

---

## 2. Colors & Surface Philosophy
The palette is rooted in deep space blacks (`#0b0e14`) to allow our high-frequency neons (`primary: #aaffdc` and `secondary: #00e3fd`) to vibrate.

### The "No-Line" Rule
Traditional 1px solid borders are strictly prohibited for sectioning. They create visual "stutter." Instead, define boundaries through:
- **Tonal Shifts:** Place a `surface_container_high` card against a `surface_container` background.
- **Luminous Edge Lighting:** Use a 1px inner-shadow or a "Ghost Border" (described in Section 4) rather than a stroke.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of semi-transparent polymer sheets.
- **Base Layer:** `surface` (#0b0e14).
- **Secondary Sections:** `surface_container_low` for non-interactive background areas.
- **Active Cards:** `surface_container_highest` (#22262f) to bring content "forward" toward the user.

### The "Glass & Gradient" Rule
To elevate the "out-of-the-box" feel, all bracket cards and floating overlays must utilize **Glassmorphism**.
- **Recipe:** Background: `surface_variant` at 40% opacity + `backdrop-blur: 12px`.
- **Signature Texture:** Primary CTAs should never be flat. Apply a linear gradient from `primary` (#aaffdc) to `primary_container` (#00fdc1) at a 135-degree angle to simulate glowing light.

---

## 3. Typography: Sharp & Authoritative
We use a high-contrast typographic pairing to balance technical precision with extreme legibility.

*   **Display & Headlines (Space Grotesk):** This is our "mechanical" voice. Used for tournament titles, match scores, and large bracket headers. The wide tracking and geometric forms command authority.
    *   *Direction:* Use `display-lg` for hero match titles. For a custom touch, set `headline-lg` to uppercase with 0.1rem letter-spacing.
*   **Body & Titles (Manrope):** Our "human" voice. Manrope provides the necessary clarity for player bios, rulebooks, and settings.
    *   *Direction:* Keep `body-md` for long-form text, ensuring a line-height of 1.5 to contrast against the dense, tight headlines.

---

## 4. Elevation & Depth
In a world of 0px border radii, depth is our only tool for soft hierarchy.

*   **The Layering Principle:** Avoid shadows on static elements. Instead, nest `surface_container_lowest` elements inside `surface_container_high` regions to create a "recessed" or "carved" look.
*   **Ambient Shadows:** For floating modals, use an extra-diffused shadow: `box-shadow: 0 20px 50px rgba(0, 227, 253, 0.08)`. Note the use of the `secondary` color tint in the shadow—this makes the glow feel like it's emitting from the UI itself.
*   **The "Ghost Border" Fallback:** If a divider is mandatory for accessibility, use the `outline_variant` token at 15% opacity. It should be felt, not seen.
*   **Bracket Connections:** Use `primary_dim` or `secondary_dim` lines at 1px thickness to connect bracket cards, but apply a `mask-image` linear gradient so the lines fade out as they move away from the active match.

---

## 5. Components

### Buttons
*   **Primary:** Sharp 0px corners. Gradient fill (`primary` to `primary_container`). Text in `on_primary_fixed`. On hover: add a `0 0 15px` outer glow using the `primary` color.
*   **Secondary:** Ghost style. `outline` color border at 20% opacity. On hover: fill with `secondary_container` at 30% opacity.

### Bracket Cards (Signature Component)
*   **Construction:** Use `surface_container_highest` with 60% opacity. 
*   **Header:** Use `label-md` in `secondary` for the "Live" or "Upcoming" status.
*   **Separation:** **No Dividers.** Use a `2.5` (0.5rem) spacing gap between player rows. Use a subtle background shift (`surface_bright` at 5% opacity) for the winning player's row.

### Chips & Tags
*   **Style:** Small, high-contrast labels. Use `tertiary_container` for the background and `on_tertiary_container` for text. 
*   **Shape:** Strictly rectangular.

### Input Fields
*   **State:** Default state is `surface_container_low`. On focus, the bottom border "activates" with a 2px `primary` line, while the rest of the container remains borderless.

---

## 6. Do's and Don'ts

### Do:
*   **Do** use the spacing scale religiously. Large gaps (e.g., `16` or `20`) create the "Editorial" breathability required for high-end design.
*   **Do** lean into asymmetry. Align a headline to the far left and the supporting body text to a column on the right.
*   **Do** use `primary` and `secondary` sparingly. They are "high-voltage" accents; if everything glows, nothing is important.

### Don't:
*   **Don't** use rounded corners (`0px` is the mandate). Even 2px breaks the Brutalist soul of this system.
*   **Don't** use pure white (#FFFFFF). Use `on_surface` (#ecedf6) to maintain the dark-room atmosphere and reduce eye strain during long gaming sessions.
*   **Don't** use standard "drop shadows" on cards. Use tonal layering or subtle ambient glows.