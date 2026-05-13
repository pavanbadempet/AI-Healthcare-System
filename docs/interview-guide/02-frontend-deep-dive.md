# 02 — Frontend Deep Dive

## Q: Explain your frontend architecture.

```
frontend/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── layout.tsx                # Root layout (fonts, providers)
│   │   ├── page.tsx                  # Landing (redirects to dashboard)
│   │   ├── globals.css               # Design tokens (CSS variables)
│   │   ├── login/page.tsx            # Public: login form
│   │   ├── signup/page.tsx           # Public: registration
│   │   └── (protected)/             # Auth-guarded route group
│   │       ├── layout.tsx            # Shared sidebar + topbar
│   │       ├── dashboard/page.tsx    # Stats overview
│   │       ├── predict/
│   │       │   ├── page.tsx          # Disease selection hub
│   │       │   ├── diabetes/         # Diabetes form
│   │       │   ├── heart/            # Heart disease form
│   │       │   ├── liver/            # Liver disease form
│   │       │   ├── kidney/           # Kidney disease form
│   │       │   └── lungs/            # Lung cancer form
│   │       ├── chat/page.tsx         # AI chatbot
│   │       ├── profile/page.tsx      # User profile
│   │       ├── admin/page.tsx        # Admin panel
│   │       ├── patients/page.tsx     # Patient records
│   │       ├── pricing/page.tsx      # Subscription plans
│   │       ├── telemedicine/page.tsx  # Appointments
│   │       ├── capacity/page.tsx     # Hospital capacity
│   │       ├── infrastructure/page.tsx # System monitoring
│   │       └── about/page.tsx        # About page
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx           # Navigation sidebar
│   │   │   └── TopBar.tsx            # Top navigation
│   │   ├── predict/
│   │   │   └── PredictionForm.tsx    # Reusable prediction component
│   │   └── chat/
│   │       └── ChatInterface.tsx     # Streaming chat UI
│   └── lib/
│       ├── api.ts                    # API client (all backend calls)
│       ├── store.ts                  # Zustand auth store
│       └── useTelemetry.ts           # Usage tracking hook
```

---

## Q: Why Next.js 16 instead of plain React?

| Feature | Plain React | Next.js |
|---|---|---|
| Routing | Need React Router | Built-in file-based routing |
| SSR/SEO | Manual setup | Built-in |
| Code splitting | Manual | Automatic per-route |
| Bundler | Webpack/Vite | Turbopack (10x faster) |
| Layouts | Manual nesting | App Router layout system |
| API routes | Need separate backend | Built-in (not used — we have FastAPI) |

**Key reason**: The `(protected)` route group. All 11 authenticated pages share a sidebar layout **without** duplicating code. The parentheses in the folder name mean it doesn't appear in the URL.

---

## Q: Explain the `(protected)` route group pattern.

```
app/
├── login/page.tsx          → /login (no sidebar)
├── signup/page.tsx         → /signup (no sidebar)
└── (protected)/
    ├── layout.tsx          → Wraps ALL children with sidebar + topbar
    ├── dashboard/page.tsx  → /dashboard (has sidebar)
    ├── predict/page.tsx    → /predict (has sidebar)
    └── admin/page.tsx      → /admin (has sidebar)
```

The `(protected)` folder is a **route group** — it organizes code without affecting URLs. The `layout.tsx` inside it wraps every child page with the sidebar and topbar. If a user isn't authenticated, this layout redirects to `/login`.

---

## Q: How does state management work?

I use **Zustand** for global state. The store holds:

```typescript
interface AuthStore {
  token: string | null;
  user: UserProfile | null;
  setToken: (token: string) => void;
  setUser: (user: UserProfile) => void;
  logout: () => void;
}
```

**Why Zustand over Redux?**
- Redux: ~50 lines for store + slice + reducers + selectors + provider
- Zustand: ~10 lines, no provider needed, built-in persistence

**How auth token injection works:**
```typescript
// In api.ts
let getToken: (() => string | null) | null = null;
export function setTokenGetter(fn: () => string | null) { getToken = fn; }

// In root layout, on mount:
setTokenGetter(() => useAuthStore.getState().token);

// Every API call auto-injects:
function authHeaders() {
  const token = getToken?.();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
```

---

## Q: Explain the PredictionForm component in detail.

It's a **single reusable component** used by all 5 disease pages. Props:

```typescript
interface PredictionFormProps {
  title: string;              // "Diabetes Risk Assessment"
  description: string;        // "Enter patient metrics..."
  fields: Field[];            // Array of form field configs
  onSubmit: (data) => Promise<PredictionResult>;  // API call
}

interface Field {
  name: string;       // "bmi"
  label: string;      // "Body Mass Index"
  type: "number" | "select";
  options?: { label: string; value: number }[];
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
  tooltip?: string;
}
```

**How each disease page uses it:**
```tsx
// diabetes/page.tsx
<PredictionForm
  title="Diabetes Risk Assessment"
  fields={[
    { name: "bmi", label: "BMI", type: "number", min: 10, max: 60 },
    { name: "gender", label: "Gender", type: "select", 
      options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] },
    // ... 7 more fields
  ]}
  onSubmit={predictDiabetes}
/>
```

**Features inside PredictionForm:**
1. **CustomSelect** — Styled dropdown that replaces ugly native OS selects
2. **Validation** — Checks all fields before submit
3. **Loading animation** — Spinning icon + progress bar
4. **Confidence bar** — Animated fill with color coding:
   - Green (<40%) = Low risk
   - Amber (40-75%) = Moderate risk
   - Red (>75%) = High risk
5. **Risk level badge** — "LOW" / "MODERATE" / "HIGH" with color
6. **Medical disclaimer** — Always shown below results

---

## Q: How does the streaming chat work?

```
User types message
    ↓
Frontend sends POST /chat/stream
    ↓
Backend returns text/event-stream
    ↓
Frontend reads with ReadableStream
    ↓
Each chunk: data: {"token":"word","status":"streaming"}
    ↓
Append token to UI in real-time
    ↓
Final chunk: {"status":"complete"}
    ↓
Stop reading
```

**Frontend code pattern:**
```typescript
export function streamChat(message, history, onChunk, onDone, onError) {
  const controller = new AbortController();  // Cancel support
  
  fetch('/chat/stream', {
    method: 'POST',
    headers: { ...authHeaders() },
    body: JSON.stringify({ message, history }),
    signal: controller.signal,
  })
  .then(async (res) => {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const text = decoder.decode(value);
      for (const line of text.split('\n')) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          onChunk(data);  // Append token to UI
        }
      }
    }
    onDone();
  });
  
  return () => controller.abort();  // Cancel function
}
```

**Why SSE over WebSockets?**
- Chat streaming is **unidirectional** (server → client only during response)
- SSE uses standard HTTP — no upgrade handshake needed
- Works through proxies and load balancers without special config
- Browser has built-in reconnection
- Simpler error handling

---

## Q: Explain your CSS design system.

I use **CSS custom properties** (variables) for a consistent medical dark theme:

```css
:root {
  /* Surface Hierarchy (5 levels) */
  --bg-primary: #000000;        /* Page backgrounds */
  --bg-secondary: #0a0a0a;      /* Panels, sidebars */
  --bg-card: #111111;           /* Cards, inputs */
  --bg-card-hover: #171717;     /* Hover states */
  --bg-elevated: #1a1a1a;       /* Modals, overlays */

  /* Status Colors (3 states × 3 variants each) */
  --danger: #ef4444;            /* High risk */
  --danger-muted: rgba(239, 68, 68, 0.1);
  --danger-border: rgba(239, 68, 68, 0.3);
  --warning: #f59e0b;           /* Moderate risk */
  --warning-muted: rgba(245, 158, 11, 0.1);
  --warning-border: rgba(245, 158, 11, 0.3);
  --success: #10b981;           /* Low risk */
  --success-muted: rgba(16, 185, 129, 0.1);
  --success-border: rgba(16, 185, 129, 0.2);
}
```

**Why CSS variables over Tailwind config?**
- Full runtime control — can change theme without rebuild
- Works with Framer Motion animations
- Component-level overrides possible
- No Tailwind class name bloat for complex color schemes

---

## Q: How do you handle responsive design?

1. **Grid system**: `grid-cols-1 lg:grid-cols-12` — single column on mobile, 12-column on desktop
2. **Sidebar**: Collapses to hamburger menu on mobile
3. **Prediction form**: 2-column grid → 1-column on small screens
4. **Results panel**: Stacks below form on mobile with `scrollIntoView()`:
   ```typescript
   useEffect(() => {
     if (result && window.innerWidth < 1024) {
       resultRef.current?.scrollIntoView({ behavior: "smooth" });
     }
   }, [result]);
   ```

---

## Q: What animations do you use?

| Animation | Library | Where |
|---|---|---|
| Page transitions | Framer Motion | `AnimatePresence` on route changes |
| Form field entrance | Framer Motion | `initial={{ opacity: 0, y: 10 }}` |
| Confidence bar fill | Framer Motion | `animate={{ width: "94.2%" }}` |
| Loading spinner | Framer Motion | `animate={{ rotate: 360 }}` infinite |
| Button progress | Framer Motion | `animate={{ width: "100%" }}` linear |
| Dropdown open/close | Framer Motion | `AnimatePresence` with y-offset |
| Error messages | Framer Motion | Height animation (0 → auto) |

---

## Q: How does the API client work?

`api.ts` provides a typed wrapper around `fetch`:

```typescript
async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),          // Auto-inject JWT
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    // Parse error detail (string or array of validation errors)
    throw new Error(errorMessage);
  }

  return res.json();
}
```

**Key design decisions:**
- **Auto-injects auth** — No need to pass token manually
- **Type-safe** — Generic `<T>` return type
- **Error parsing** — Handles both string errors and Pydantic validation arrays
- **Centralized** — Change base URL in one place for deployment
