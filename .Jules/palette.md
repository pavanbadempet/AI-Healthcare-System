## 2026-06-11 - Command Input Labeling
**Learning:** Search inputs in custom command palettes often rely solely on placeholders, which can be skipped by some screen readers or disappear on input, degrading accessibility.
**Action:** Always provide explicit `aria-label` attributes to search inputs that lack a visible `<label>`.
## 2026-06-11 - Fixing Asynchronous React Testing Library Tests
**Learning:** Using `expect(screen.getByText(...)).toBeInTheDocument()` after asynchronous events (like form submissions that update state later via promises) can cause flaky or failing tests because the element isn't present *immediately*.
**Action:** Use `await waitFor(() => expect(screen.getByText(...)).toBeInTheDocument())` when asserting that an element appears as a result of an async operation.
