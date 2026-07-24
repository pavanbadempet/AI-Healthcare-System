# SOTA Server-Driven View Layer Specification

This document specifies the Server-Driven UI (SDUI) schema compilation and Virtual View Tree Patching standards.

```
┌─────────────────────────────────────────────────────────────┐
│          Server-Driven UI (SDUI) Schema Compiler            │
│  - Emits JSON UIComponentNode trees dynamically from API     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Virtual View Tree Reconciliation & Diffing         │
│  - Calculates minimal prop update patches for client UI     │
└─────────────────────────────────────────────────────────────┘
```

---

## 👁️ Key View Layer Standards

1. **Server-Driven UI (SDUI) Schema Protocol (`render_clinical_dashboard_view`)**:
   - Generates structured JSON UI tree nodes (`UIComponentNode`) to drive client app rendering dynamically.
2. **Virtual View Tree Patch Reconciler (`diff_view_trees`)**:
   - Computes minimal prop update patches (`UPDATE_PROPS`) between view iterations to eliminate wasteful UI re-renders.
3. **Sub-10ms UI Component Shell Generator**:
   - Assembles static UI shells server-side for immediate progressive hydration.
