# Google Stitch UI Design Tokens & System

This document outlines the design token schema, typography rules, color palettes, and component specifications for the **AI Healthcare System** to achieve a premium, high-readability developer console and clinical dashboard.

---

## 1. Typography System

We use premium modern Google Fonts to replace all browser defaults.

*   **Display & Headings (Outfit)**: Used for headers, dashboard numbers, and large labels to create a friendly, modern, and high-tech feel.
    *   `font-family: 'Outfit', sans-serif;`
*   **Body & UI Text (Inter)**: Highly readable sans-serif font designed for application interfaces.
    *   `font-family: 'Inter', sans-serif;`
*   **Code & Telemetry (JetBrains Mono)**: Used for data tables, status bars, and log displays to emphasize precision.
    *   `font-family: 'JetBrains Mono', monospace;`

---

## 2. Color Palette & Theming (Modern Dark Mode)

We implement a cohesive dark theme built with high-contrast, harmonious HSL values for comfort during extended clinical monitoring sessions.

| Token | HSL / Hex Value | Description |
|---|---|---|
| `--bg-primary` | `hsl(240, 10%, 3.9%)` / `#09090b` | Base background |
| `--bg-secondary` | `hsl(240, 10%, 6.5%)` / `#0f0f11` | Containers and lists |
| `--bg-card` | `hsl(240, 5.9%, 10%)` / `#18181b` | Default card surfaces |
| `--bg-card-hover` | `hsl(240, 5.9%, 14%)` / `#222227` | Active hover state |
| `--text-primary` | `hsl(240, 5.9%, 96.1%)` / `#f4f4f5` | Main text headers |
| `--text-secondary` | `hsl(240, 5%, 64.9%)` / `#a1a1aa` | Labels and body text |
| `--text-dim` | `hsl(240, 3.8%, 46.1%)` / `#71717a` | Inactive captions |
| `--accent` | `hsl(243, 75.4%, 58.6%)` / `#4f46e5` | Primary Indigo brand accent |
| `--accent-purple` | `hsl(258, 90%, 66%)` / `#8b5cf6` | AI features highlight |
| `--accent-blue` | `hsl(188, 86%, 53%)` / `#06b6d4` | Live stream telemetry accent |
| `--border` | `rgba(255, 255, 255, 0.06)` | Thin divider lines |
| `--border-focus` | `rgba(255, 255, 255, 0.18)` | Active borders |

---

## 3. Geometric Rules & Spacings

*   **Borders**: Strictly `1px` solid `rgba(255, 255, 255, 0.06)`. No heavy solid borders.
*   **Corners**:
    *   Small buttons / inputs: `6px` (`--radius-sm`)
    *   Cards / Panels: `10px` (`--radius`)
    *   Outer wrapper panels: `16px` (`--radius-lg`)
*   **Atmosphere (Atmospheric Glow)**:
    *   Behind the body, we place a multi-point radial gradient background to create depth:
        ```css
        background:
          radial-gradient(800px 600px at 10% 15%, rgba(99, 102, 241, 0.05), transparent 50%),
          radial-gradient(900px 700px at 85% 20%, rgba(139, 92, 246, 0.04), transparent 50%),
          radial-gradient(700px 500px at 50% 80%, rgba(6, 182, 212, 0.03), transparent 50%);
        ```

---

## 4. UI Components Specification

### A. Buttons (`.btn`)
*   **Primary (`.btn-primary`)**: High-contrast brand background, small dropshadow, scale click response.
*   **Secondary (`.btn-secondary`)**: Translucent background, border outline, subtle hover highlight.
*   **Ghost (`.btn-ghost`)**: Fully transparent background, text color transition on hover.

### B. Glass Cards (`.glass-card`)
*   Translucent cards with `backdrop-filter: blur(16px)` and subtle scale/border-color transitions on hover.

### C. Clinical Inputs (`.input-clinical`)
*   Lightly shaded backgrounds with clean focus indicators (indigo outline + glow) for high visibility.
