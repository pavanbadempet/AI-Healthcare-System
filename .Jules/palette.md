## 2024-05-18 - Interactive Dropdowns Screen Reader Support
**Learning:** Found a reusable UX pattern for interactive layout dropdowns (Profile, Language, Telemetry). Screen readers need `aria-expanded` tied to the state and `aria-haspopup` to properly navigate and understand these complex interactive elements.
**Action:** Always add `aria-expanded={isOpen}` and `aria-haspopup="true"` to custom dropdown toggle buttons across the design system.
