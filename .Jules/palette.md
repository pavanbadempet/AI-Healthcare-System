## 2026-06-24 - Fixing Asynchronous React Testing Library Tests
**Learning:** Using `expect(screen.getByText(...)).toBeInTheDocument()` after asynchronous events (like form submissions that update state later via promises) can cause flaky or failing tests because the element isn't present *immediately*.
**Action:** Use `await waitFor(() => expect(screen.getByText(...)).toBeInTheDocument())` when asserting that an element appears as a result of an async operation.
