## 2026-06-13 - Added ARIA Label to Mobile Drawer Quick Search
**Learning:** Found an accessibility issue where the Quick Search button in the mobile drawer lacked an explicit aria-label, which is important for screen readers.
**Action:** Added `aria-label="Open quick search"` to the button to improve accessibility.
