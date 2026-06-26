## 2025-02-18 - Missing ARIA Labels on Status Controls
**Learning:** Found an icon-only button inside the PatientDetail view (Refresh Lab Kits) lacking an ARIA label, which is critical for screen reader users to understand its action.
**Action:** Always verify icon-only interactive elements contain accessible labels or `aria-label` attributes.
