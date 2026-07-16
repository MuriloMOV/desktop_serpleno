# Performance Analysis & 500ms Target Plan

**Date:** 2026-07-15  
**Goal:** Bring all critical user-facing operations below 500ms  
**Scope:** Cold start, login flow, navigation switches, dashboard KPI load, view rendering

---

## Current State Assessment

| Operation | Current (est.) | Target | Status |
|---|---|---|---|
| App cold start | ~300-500ms | < 500ms | Marginal |
| Login flow (click → dashboard) | ~800-1500ms | < 500ms | **Over target** |
| Navigation switch | ~200-400ms | < 500ms | Near target |
| Dashboard KPIs (warm) | ~50-100ms | < 200ms | OK |
| Dashboard KPIs (cold) | ~300-600ms | < 500ms | **Over target** |
| PIL gradient draw | 40-120ms | < 50ms | Over on resize |

---

## Identified Bottlenecks

### 1. Login Frame PIL Gradient (login.py)
- `_desenhar_fundo()` runs pixel-by-pixel gradient generation on main thread during `<Configure>` events
- `_get_or_create_gradient()` creates new `ImageTk.PhotoImage` per size, but generation is still CPU-heavy
- 28 animated bubbles with `after(22ms)` loop = ~45 FPS constant UI updates
- **Impact:** Initial draw can exceed 40ms (logged warning); resize triggers redraw

### 2. View Recreation on Every Navigation (view_factory.py, navigation.py)
- `ViewFactory.create()` instantiates a brand new controller + view on every `show(key)`
- No view caching; old view is destroyed, new one built from scratch
- Each view calls `_load_async(fetch_fn)` which spawns a thread + schedules callback
- **Impact:** Perceived latency of 200-400ms per switch due to widget creation + async data fetch

### 3. Dashboard KPIs: 8+ Queries Cold (dashboard.py)
- `_contar_kpis_consolidado()` runs 8 scalar subqueries + 4 helper queries = ~12 MySQL round-trips
- Each `fetch_one`/`fetch_all` opens/closes a connection from pool
- Warm cache (20s TTL) masks this, but cold/exprired calls hit all queries
- **Impact:** Cold KPI load 300-600ms

### 4. API Client Retry Timeouts Too High (api.py)
- `get()` timeout=6s with 2 retries = worst-case 12s before failure
- `post()` timeout=8s with 2 retries = worst-case 16s
- These timeouts bleed into login (`_try_establish_session`) and sync operations
- **Impact:** Any API-dependent operation can stall for seconds

### 5. Font Object Creation Overhead (typography.py)
- `font()` and `themed_font()` create new `ctk.CTkFont` objects on every widget creation call
- A typical view creates 20-50 widgets, each calling `themed_font()` 1-3 times
- CTkFont wraps Tkinter font objects which incur interpreter overhead
- **Impact:** Cumulative 50-150ms during view construction

### 6. Database Connection Open/Close Per Query (query_helpers.py, db_config.py)
- Each `fetch_all`/`fetch_one` call opens a connection from pool, executes, closes
- Dashboard KPIs cold: 12 connection checkout/return cycles
- Connection pool reduces TCP overhead but still has mutex + handshake cost
- **Impact:** ~10-30ms per connection cycle × 12 queries = 120-360ms overhead

### 7. Login Flow Composition (app.py, login.py)
- `mostrar_login()` builds full LoginFrame synchronously (PIL + 28 bubbles + widgets)
- On success: `iniciar_sistema()` destroys login, builds sidebar + content area + dashboard view
- `BootstrapService.run_post_login_seed()` fires in daemon thread but may compete for DB connections
- **Impact:** Total login flow 800-1500ms

---

## Proposed Improvements

### P1: Cache Views on Navigation (high impact, low risk)
**File:** `presentation/navigation.py`, `presentation/view_factory.py`

- Add `_view_cache: dict[str, ctk.CTkFrame]` to `NavigationManager`
- On `show(key)`: if view exists in cache and is valid, reuse it instead of recreating
- Invalidate cache only on data mutations (write operations) or explicit `refresh(key)`
- Pre-create dashboard view at login instead of first nav switch

**Expected gain:** Navigation switches from ~300ms to ~50ms (reuse + no async reload)

### P2: Consolidate Dashboard KPIs Queries (high impact, low risk)
**File:** `repositories/dashboard.py`

- Replace 8+ scalar subqueries with 1-2 JOIN queries that return all counts in single round-trip
- Example: single query with multiple `COUNT(CASE WHEN ...)` expressions
- Keep local fallback path unchanged

**Expected gain:** Cold KPI load from ~500ms to ~150ms

### P3: Reduce API Timeouts (medium impact, low risk)
**File:** `infrastructure/api/api.py`

- `get()`: timeout=3s, retries=1 (worst-case 6s → 3s)
- `post()`: timeout=4s, retries=1 (worst-case 8s → 4s)
- Keep retry for `ConnectionError`/`Timeout` but reduce to 1 retry
- Add `_request_timeout` env var override for debugging

**Expected gain:** API failure paths from 6-16s to 3-4s; successful calls unaffected

### P4: Offload PIL Gradient to Background Thread (medium impact, medium risk)
**File:** `presentation/views/login.py`

- Create gradient image in daemon thread via `AsyncRunner.run()`
- Show placeholder solid color immediately, swap gradient when ready
- Cache gradient by size (already partially implemented with `_gradient_cache`)
- Pre-generate gradient for common window sizes (800x600, 1024x768, 1280x720) at startup in background

**Expected gain:** Initial login frame visible in <100ms; gradient appears within 200ms

### P5: Font Object Pool (low impact, low risk)
**File:** `ui/theme/typography.py`

- Add module-level `_FONT_CACHE: dict[tuple[str, int, str], ctk.CTkFont]`
- `font()` and `themed_font()` check cache before creating new object
- Cache key: `(family, size, weight)`

**Expected gain:** View construction 50-100ms faster

### P6: Batch MySQL Queries with Connection Reuse (medium impact, low risk)
**File:** `infrastructure/db/query_helpers.py`, `repositories/dashboard.py`

- Add `fetch_all_batch(queries: list[tuple[str, tuple]])` that reuses a single connection
- For dashboard KPIs: pass all 8 count queries in one batch
- Alternative: add `with connection() as conn:` context in `_contar_kpis_consolidado` and reuse cursor

**Expected gain:** Connection overhead reduced from ~200ms to ~30ms for dashboard cold load

### P7: Lazy-Load Sidebar + Content Area (low impact, low risk)
**File:** `app.py`, `presentation/navigation.py`

- Currently `iniciar_sistema()` builds sidebar + content + dashboard synchronously
- Build sidebar first (fast), show dashboard placeholder, then load dashboard data async
- Use `after_idle` to defer non-critical UI construction

**Expected gain:** Perceived login flow from ~800ms to ~400ms

### P8: Reduce Bubble Animation Load (low impact, low risk)
**File:** `presentation/views/login.py`

- Reduce bubble count from 28 to 16
- Increase animation interval from 22ms to 33ms (~30 FPS instead of 45)
- Use `canvas.move()` instead of `canvas.coords()` for bubble position updates (less overhead)

**Expected gain:** 10-20ms per animation frame, lower CPU usage

---

## Implementation Order

1. **P3** (timeouts) — 1 file, immediate safety improvement
2. **P5** (font cache) — 1 file, no behavior change
3. **P6** (batch queries) — 2 files, core performance win
4. **P1** (view cache) — 2 files, major UX improvement
5. **P2** (consolidate KPIs) — 1 file, complements P6
6. **P4** (async gradient) — 1 file, login experience
7. **P7** (lazy sidebar) — 2 files, perceived performance
8. **P8** (bubbles) — 1 file, polish

---

## Validation Plan

1. **Instrument existing PERF logs:**
   - Add `PERF nav_switch_<key>_ms` already exists — verify after P1
   - Add `PERF dashboard_kpis_ms` for cold/warm distinction
   - Add `PERF login_flow_total_ms` from button click to dashboard rendered

2. **Run existing benchmark:**
   - `python scripts/benchmarks/perf_bench.py`
   - Target: dashboard cold < 200ms, warm < 100ms

3. **Run test suite:**
   - `pytest -v --tb=short`
   - Ensure no regressions

4. **Manual timing with stopwatch / PERF logs:**
   - Cold start: app launch to login visible
   - Login flow: click "Entrar" to dashboard fully rendered
   - Navigation: click sidebar items, measure 3 switches

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| View caching causes stale data after mutations | Add `invalidate_view(key)` call in all write operations |
| Gradient thread race condition | Use `after_idle` to safely swap image on main thread |
| Font cache key collisions | Use `(family, size, weight)` tuple; clear on theme toggle |
| Batch queries break local fallback | Only use batch in MySQL path; local fallback unchanged |

---

## Out of Scope

- MySQL connection pool sizing optimization (requires load testing)
- SQLite WAL vs DELETE journal mode comparison
- asyncio migration (too large for this cycle)
- Memoization of widget property lookups (micro-optimization)
