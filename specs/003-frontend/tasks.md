# Task Breakdown — Frontend (003-frontend)

Ordered strictly by technical dependencies. Each task is sized for 20-30 minutes. Complete tasks in order; do not skip ahead because later tasks depend on earlier contracts.

> **Frontend layout note:** the frontend lives in `frontend/`. All `src/`, `tests/`, and config paths below are relative to `frontend/`, and every command (dev, build, lint, test) must be run from `frontend/`.

Conventions:

- `Covers` = spec business rules and plan sections implemented by the task.
- `Files` = files to create or modify in this task only.
- Progress is tracked with `- [ ]` checkboxes.
- `Done when` is verifiable with a test or command.

---

## T01 — Project scaffold: Vite + React + Tailwind dark base

**Covers:** plan §2 (project layout), BR-15 (dark base), BR-16 (responsive base), plan §6 (Decision 1, 7).

**Files:**

- Create `frontend/package.json`
- Create `frontend/vite.config.js`
- Create `frontend/index.html`
- Create `frontend/.env.example`
- Create `frontend/.gitignore`
- Create `frontend/src/main.jsx`
- Create `frontend/src/App.jsx`
- Create `frontend/src/index.css` (Tailwind v4 CSS-first tokens via `@theme`)

> **Tailwind v4 note:** the design system uses Tailwind CSS v4 (CSS-first). Colors, radii, and animations are declared in `src/index.css` with `@theme`, so no `tailwind.config.js` and no `postcss.config.js` are created; the `@tailwindcss/vite` plugin handles the build.

**Steps:**

- [x] Scaffold a React SPA with Vite using plain JavaScript (no TypeScript).
- [x] Add Tailwind CSS with a single dark palette and no light tokens or theme toggle (BR-15).
- [x] Configure the dev server to proxy `/api` to the backend so `VITE_API_BASE_URL=/api/v1` resolves without CORS.
- [x] Mount `App` from `main.jsx` and import `index.css` with mobile-first base styles (BR-16).

**Done when:**

- `npm run build` completes successfully and `npm run dev` serves the app at the configured port.

---

## T02 — Tooling: ESLint, Prettier and Vitest test infrastructure

**Covers:** `AGENT.md` Definition of Done (linters/tests), plan §7 (test setup).

**Files:**

- Create `frontend/eslint.config.js`
- Create `frontend/.prettierrc`
- Create `frontend/vitest.config.js`
- Create `frontend/tests/setup.js`
- Create `frontend/tests/msw/server.js`
- Create `frontend/tests/unit/smoke.test.js`

**Steps:**

- [ ] Configure ESLint and Prettier with zero-tolerance defaults for the frontend source.
- [ ] Configure Vitest with the `jsdom` environment and React Testing Library, loading `tests/setup.js`.
- [ ] Set up an MSW server factory for shared mock handlers used by later tests.
- [ ] Add npm scripts: `dev`, `build`, `lint`, `format`, `test`.
- [ ] Add a minimal smoke test so the runner is exercised.

**Done when:**

- `npm run lint` exits with zero errors and `npm run test -- --run` exits 0.

---

## T03 — Shared types and model contracts

**Covers:** plan §3.1 (session), §3.2 (view models), §3.3 (form state), plan §4.7 (prop shapes).

**Files:**

- Create `frontend/src/types/models.js`

**Steps:**

- [ ] Define JSDoc typedefs for `User`, `Article`, `AuthSession`, `ApiError`, `RegisterFormState`, `LoginFormState`, `ArticleFormState` (no runtime code).
- [ ] Document the role literal union (`USER` | `ADMIN`) and the `ArticleOutput` fields (`id`, `title`, `text`, `user_id`, `created_at`).
- [ ] Document that the login response exposes only `access_token` and `token_type` (plan §3.6).

**Done when:**

- `node -e "import('./src/types/models.js').then(()=>console.log('ok'))"` prints `ok` (module loads with no syntax errors).

---

## T04 — Utils: token storage wrapper

**Covers:** plan §3.5 (persistence keys), BR-8 (persistence), plan §5.1 (bootstrap).

**Files:**

- Create `frontend/src/utils/storage.js`
- Create `frontend/tests/unit/storage.test.js`

**Steps:**

- [ ] Implement `get_token`, `set_token`, `clear_token` over `localStorage` using one namespaced key (e.g. `personal_blog.access_token`).
- [ ] Ensure the module never throws when `localStorage` is unavailable (SSR/test edge) and returns `null` instead.
- [ ] Test: setting then getting returns the same value; clearing returns `null`; only the token string is stored (no password, no user object).

**Done when:**

- `npm run test -- --run tests/unit/storage.test.js` passes.

---

## T05 — Utils: JWT claim decoding

**Covers:** plan §3.1 (claims), §5.1 (bootstrap), plan §6 (Decision 4).

**Files:**

- Create `frontend/src/utils/jwt.js`
- Create `frontend/tests/unit/jwt.test.js`

**Steps:**

- [ ] Implement `decode(token)` returning `{ user_id, username, role, exp }` or `null` for malformed tokens (no signature verification; decoding only).
- [ ] Implement `is_expired(claims)` comparing `exp` against the current time.
- [ ] Test: valid token decodes all four claims; malformed/empty token returns `null`; expired token is detected; future token is not expired.

**Done when:**

- `npm run test -- --run tests/unit/jwt.test.js` passes.

---

## T06 — Utils: client validators mirroring the backend

**Covers:** BR-2, BR-3, plan §3.4 (validation constants), plan §5.5/§5.8.

**Files:**

- Create `frontend/src/utils/validators.js`
- Create `frontend/tests/unit/validators.test.js`

**Steps:**

- [ ] Implement `validate_register` for username 8-20 with no whitespace, valid email shape, password 8-20 (raw, not trimmed).
- [ ] Implement `validate_login` for required identifier and password only.
- [ ] Implement `validate_article` with raw lengths: title 8-20, text required, text 10-300, using the exact strings `title must be 8-20 characters`, `text must be 10-300 characters`, `text is required`.
- [ ] Test boundaries 7/8/20/21 for username, password, and title; whitespace variants (`my user01`, ` user01AB`, `user01AB `); empty text; text 9/10/300/301; emojis and spaces counted as one without trimming.

**Done when:**

- `npm run test -- --run tests/unit/validators.test.js` passes and asserts the exact spec strings.

---

## T07 — Utils: date formatting (UTC to local)

**Covers:** plan §5.11 (`format_created_at`), `AGENT.md` utility-layer rule.

**Files:**

- Create `frontend/src/utils/date.js`
- Create `frontend/tests/unit/date.test.js`

**Steps:**

- [ ] Implement `format_created_at(iso_utc)` converting an ISO-8601 UTC string to a local-timezone display string.
- [ ] Return an empty/safe string for invalid or missing input instead of throwing.
- [ ] Test: a known UTC input renders without error; invalid input degrades gracefully.

**Done when:**

- `npm run test -- --run tests/unit/date.test.js` passes.

---

## T08 — Utils: permission helpers

**Covers:** BR-10, plan §5.7 (`can_manage_article`), plan §5.9 (`is_admin`).

**Files:**

- Create `frontend/src/utils/permissions.js`
- Create `frontend/tests/unit/permissions.test.js`

**Steps:**

- [ ] Implement `is_admin(session)` returning true only when `session.role === "ADMIN"`.
- [ ] Implement `can_manage_article(article, session)` returning true for ADMIN on any article, true for the owner USER, and false for a non-owner USER or no session.
- [ ] Test all four combinations.

**Done when:**

- `npm run test -- --run tests/unit/permissions.test.js` passes.

---

## T09 — Utils: centralized copy (messages)

**Covers:** BR-3, BR-5, BR-9, plan §6 (Decision 13), `[NECESITA ACLARACIÓN]` success/expiry copies.

**Files:**

- Create `frontend/src/utils/messages.js`

**Steps:**

- [ ] Define literal copy constants: `REGISTER_SUCCESS`, `SESSION_EXPIRED`, `ARTICLE_CREATED`, `ARTICLE_UPDATED`, `ARTICLE_DELETED`, `USER_PROMOTED`, `GENERIC_ERROR`, `FORBIDDEN`, `ARTICLE_NOT_FOUND`, `INVALID_CREDENTIALS`.
- [ ] Use plain strings only (no i18n framework), keeping `SESSION_EXPIRED` and the success copies explicit.
- [ ] Keep `INVALID_CREDENTIALS` free of any hint about which credential failed (BR-6).

**Done when:**

- `grep -n "SESSION_EXPIRED\|INVALID_CREDENTIALS\|ARTICLE_CREATED" src/utils/messages.js` shows the constants defined.

---

## T10 — Utils: API error normalization

**Covers:** BR-3, BR-4, BR-6, BR-18, plan §5.10 (normalize), plan §3.2 (`ApiError`).

**Files:**

- Create `frontend/src/utils/api_errors.js`
- Create `frontend/tests/unit/api_errors.test.js`

**Steps:**

- [ ] Implement `normalize(status, code, detail)` returning `{ status, code, globalMessage, fieldErrors }`.
- [ ] Map `duplicate_username` -> `username` field and `duplicate_email` -> `email` field.
- [ ] Map `validation_error` detail to best-effort field errors; map `invalid_credentials` to a single generic global message.
- [ ] Map missing response (network/timeout) to `code: network_error` and 5xx to a non-technical generic message.
- [ ] Test each mapping from plan §5.10.

**Done when:**

- `npm run test -- --run tests/unit/api_errors.test.js` passes.

---

## T11 — HTTP client with interceptors

**Covers:** BR-9, BR-18, plan §4.3, plan §5.2, plan §6 (Decision 2, 3).

**Files:**

- Create `frontend/src/api/client.js`

**Steps:**

- [ ] Create a single Axios instance with `baseURL` from `VITE_API_BASE_URL` (default `/api/v1`) and JSON headers.
- [ ] Request interceptor: attach `Authorization: Bearer <token>` only when a non-expired token exists.
- [ ] Response interceptor: pass through successes; normalize errors via `utils/api_errors`.
- [ ] On `401` (excluding the login call) clear the token and emit a `session-expired` event; expose an `onSessionExpired` subscription used by `AuthContext`.

**Done when:**

- `npm run lint` passes and `node -e "import('./src/api/client.js').then(()=>console.log('ok')).catch(e=>{console.error(e);process.exit(1)})"` prints `ok`.

---

## T12 — Service: auth

**Covers:** plan §4.1 (register/login), §4.2, BR-6, BR-7.

**Files:**

- Create `frontend/src/services/auth_service.js`
- Create `frontend/tests/unit/auth_service.test.js`

**Steps:**

- [ ] Implement `register(payload)` calling `POST /users/register` and returning the created user (no token).
- [ ] Implement `login(payload)` calling `POST /users/login` and returning `{ access_token }`.
- [ ] Ensure both throw the normalized `ApiError` from the client and never touch React state.
- [ ] Test with MSW: register success returns a user with `role: USER`; login success returns a token; login 401 throws an `invalid_credentials` error.

**Done when:**

- `npm run test -- --run tests/unit/auth_service.test.js` passes.

---

## T13 — Service: articles

**Covers:** plan §4.1 (articles), §4.2, BR-1, BR-13.

**Files:**

- Create `frontend/src/services/article_service.js`
- Create `frontend/tests/unit/article_service.test.js`

**Steps:**

- [ ] Implement `getAll()` and `getById(id)` for public reads.
- [ ] Implement `create(payload)`, `update(id, payload)` and `remove(id)` (expects 204 for delete).
- [ ] Ensure payloads contain only `title` and `text` (never author or time) and errors propagate as `ApiError`.
- [ ] Test with MSW: list returns an array; getById returns one article; create/update return the article; remove resolves on 204; a 404 on getById throws `article_not_found`.

**Done when:**

- `npm run test -- --run tests/unit/article_service.test.js` passes.

---

## T14 — Service: users (list + promote)

**Covers:** BR-14, plan §4.1 (`GET /users`, `PATCH /users/{id}/role`), §4.2, plan §6 (Decision 11).

**Files:**

- Create `frontend/src/services/user_service.js`
- Create `frontend/tests/unit/user_service.test.js`

**Steps:**

- [ ] Implement `list()` calling `GET /users` returning the user array (documented backend dependency).
- [ ] Implement `promote(id)` calling `PATCH /users/{id}/role` with body `{ role: "ADMIN" }` and returning the updated user.
- [ ] Test with MSW: list returns users; promote returns the updated role; a 403 throws `forbidden`.

**Done when:**

- `npm run test -- --run tests/unit/user_service.test.js` passes.

---

## T15 — Toast context and toast UI

**Covers:** BR-5, plan §4.4 (`ToastContext`), plan §6 (Decision 9).

**Files:**

- Create `frontend/src/components/ui/Toast.jsx`
- Create `frontend/src/context/ToastContext.jsx`
- Create `frontend/tests/component/Toast.test.jsx`

**Steps:**

- [ ] Implement `ToastContext` exposing `showToast({ type, message })` and rendering a stacked toast region.
- [ ] Implement auto-dismiss with a visible countdown-independent timeout.
- [ ] Test: calling `showToast` renders the message; the toast disappears after the timeout; multiple toasts stack.

**Done when:**

- `npm run test -- --run tests/component/Toast.test.jsx` passes.

---

## T16 — Auth context: session lifecycle (no logout)

**Covers:** BR-8, BR-9, plan §4.4, plan §5.1/§5.3, plan §6 (Decision 3, 4, 12).

**Files:**

- Create `frontend/src/context/AuthContext.jsx`
- Create `frontend/tests/component/AuthContext.test.jsx`

**Steps:**

- [ ] Implement the `AuthContext` provider exposing `{ session, user, isAuthenticated, isAdmin, login, register, handleSessionExpired }` (no `logout`).
- [ ] Bootstrap the session from `storage` + `jwt` on mount; treat invalid/expired tokens as no session.
- [ ] On `login`, store the token and set the session from decoded claims; on `register`, call the service without storing a token.
- [ ] Subscribe to the client `session-expired` event and clear the session in `handleSessionExpired`.
- [ ] Test: valid stored token yields an authenticated session; expired token yields no session; a session-expired event clears the session; no logout member is exposed.

**Done when:**

- `npm run test -- --run tests/component/AuthContext.test.jsx` passes.

---

## T17 — Hook: use_auth

**Covers:** plan §4.5 (`use_auth`), BR-6, BR-7.

**Files:**

- Create `frontend/src/hooks/use_auth.js`
- Create `frontend/tests/unit/use_auth.test.jsx`

**Steps:**

- [ ] Expose `{ session, user, isAuthenticated, isAdmin, login, register, loginError, isSubmitting }` from `AuthContext`.
- [ ] `login` returns `{ global }` on invalid credentials (single generic message) and `{ fieldErrors }` on 400.
- [ ] `register` returns `{ fieldErrors }` for 400/409 and a success signal for navigation to login.
- [ ] Test each return branch with MSW-backed services.

**Done when:**

- `npm run test -- --run tests/unit/use_auth.test.jsx` passes.

---

## T18 — UI primitives: Button, Input, Textarea, FieldError

**Covers:** BR-4, BR-15, plan §4.7 (component props), `AGENT.md` UI-layer rule.

**Files:**

- Create `frontend/src/components/ui/Button.jsx`
- Create `frontend/src/components/ui/Input.jsx`
- Create `frontend/src/components/ui/Textarea.jsx`
- Create `frontend/src/components/ui/FieldError.jsx`
- Create `frontend/tests/component/UiPrimitives.test.jsx`

**Steps:**

- [ ] Implement `Button` with `variant` (`primary|secondary|danger|ghost`), `loading`, `disabled`, and `type`.
- [ ] Implement `Input` and `Textarea` forwarding `label`, `value`, `onChange`, `error`, `maxLength`.
- [ ] Implement `FieldError` rendering a message under a field (inline error surface, BR-4).
- [ ] Test: disabled state when `loading`; error prop renders `FieldError`; variants apply distinct classes.

**Done when:**

- `npm run test -- --run tests/component/UiPrimitives.test.jsx` passes.

---

## T19 — UI states: Spinner, EmptyState, ErrorState, Modal

**Covers:** BR-17, BR-18, plan §4.7.

**Files:**

- Create `frontend/src/components/ui/Spinner.jsx`
- Create `frontend/src/components/ui/EmptyState.jsx`
- Create `frontend/src/components/ui/ErrorState.jsx`
- Create `frontend/src/components/ui/Modal.jsx`
- Create `frontend/tests/component/UiStates.test.jsx`

**Steps:**

- [ ] Implement `Spinner` for loading states.
- [ ] Implement `EmptyState` (`title`, `message`, optional action) and `ErrorState` (`title`, `message`, optional retry).
- [ ] Implement a generic `Modal` component (available for future use; not used for delete, per BR-11).
- [ ] Test: each state renders its text; `ErrorState` retry triggers the callback.

**Done when:**

- `npm run test -- --run tests/component/UiStates.test.jsx` passes.

---

## T20 — Layout: Navbar and PageContainer

**Covers:** BR-14 (hidden admin entry), BR-15, BR-16, plan §2, plan §4.6.

**Files:**

- Create `frontend/src/components/layout/Navbar.jsx`
- Create `frontend/src/components/layout/PageContainer.jsx`
- Create `frontend/tests/component/Navbar.test.jsx`

**Steps:**

- [ ] Implement `Navbar` with public links (Home) and auth-aware links; show the New Article link only when authenticated and the Admin link only for ADMIN (BR-14).
- [ ] Render no logout control anywhere, even when authenticated (BR-8).
- [ ] Implement `PageContainer` providing the responsive dark shell used by all pages.
- [ ] Test: guest sees no New Article/Admin links; USER sees New Article but not Admin; ADMIN sees both; no logout button in any state.

**Done when:**

- `npm run test -- --run tests/component/Navbar.test.jsx` passes.

---

## T21 — Route guards: ProtectedRoute, GuestRoute, RequireAdmin

**Covers:** BR-9, BR-14, plan §4.6, plan §6 (Decision 6).

**Files:**

- Create `frontend/src/routes/ProtectedRoute.jsx`
- Create `frontend/src/routes/GuestRoute.jsx`
- Create `frontend/src/components/features/admin/RequireAdmin.jsx`
- Create `frontend/tests/component/RouteGuards.test.jsx`

**Steps:**

- [ ] `ProtectedRoute`: redirect to `/login` with the intended route and `reason=session_expired` when there is no valid session.
- [ ] `GuestRoute`: redirect authenticated users to `/`.
- [ ] `RequireAdmin`: redirect a valid non-admin session to `/` without rendering children.
- [ ] Test: each guard renders children or redirects as specified.

**Done when:**

- `npm run test -- --run tests/component/RouteGuards.test.jsx` passes.

---

## T22 — Feature: LoginForm

**Covers:** BR-4, BR-6, plan §4.7, plan §5.4.

**Files:**

- Create `frontend/src/components/features/auth/LoginForm.jsx`
- Create `frontend/tests/component/LoginForm.test.jsx`

**Steps:**

- [ ] Render identifier and password fields with inline errors; block submit when required fields are empty.
- [ ] On submit call `use_auth().login`; show a single generic inline message on 401 (BR-6); show field errors on 400.
- [ ] Render the session-expired notice when arrived with `reason=session_expired` (BR-9).
- [ ] Test: empty submit shows required errors; wrong credentials show the generic message; success calls login once.

**Done when:**

- `npm run test -- --run tests/component/LoginForm.test.jsx` passes.

---

## T23 — Feature: RegisterForm

**Covers:** BR-2, BR-3, BR-4, BR-7, plan §4.7, plan §5.5.

**Files:**

- Create `frontend/src/components/features/auth/RegisterForm.jsx`
- Create `frontend/tests/component/RegisterForm.test.jsx`

**Steps:**

- [ ] Render username, email, password fields with client validation from `utils/validators` and inline errors.
- [ ] On submit call `use_auth().register`; map 409 duplicate errors to the matching field and 400 to field errors.
- [ ] On success navigate to login with the `REGISTER_SUCCESS` confirmation and store no token (BR-7).
- [ ] Test: invalid lengths/whitespace show inline errors; duplicate username/email map to fields; success navigates to login.

**Done when:**

- `npm run test -- --run tests/component/RegisterForm.test.jsx` passes.

---

## T24 — Pages: LoginPage and RegisterPage

**Covers:** BR-7, BR-9, plan §4.6.

**Files:**

- Create `frontend/src/pages/LoginPage.jsx`
- Create `frontend/src/pages/RegisterPage.jsx`

**Steps:**

- [ ] `LoginPage` renders `LoginForm` inside `GuestRoute`, reading the `reason` query param and the register confirmation from navigation state.
- [ ] `RegisterPage` renders `RegisterForm` inside `GuestRoute`.
- [ ] After a successful login follow the intended route when provided, otherwise go to `/` (plan §5.4).
- [ ] Keep both pages presentational, delegating all logic to the feature components and hooks.

**Done when:**

- `npm run lint` passes and the pages render without console errors when mounted in the route guard test suite (`npm run test -- --run tests/component/RouteGuards.test.jsx`).

---

## T25 — Hook use_articles + ArticleCard + ArticleList

**Covers:** BR-1, BR-10, BR-17, plan §4.5, plan §5.6/§5.7.

**Files:**

- Create `frontend/src/hooks/use_articles.js`
- Create `frontend/src/components/features/article/ArticleCard.jsx`
- Create `frontend/src/components/features/article/ArticleList.jsx`
- Create `frontend/tests/component/ArticleCard.test.jsx`

**Steps:**

- [ ] Implement `use_articles` exposing `{ articles, loading, error, refetch }` calling the public list.
- [ ] `ArticleCard` receives `{ article, canManage, onDelete }` and renders title, author label (`You`/`Author #id` via helper), and formatted creation time.
- [ ] Hide edit/delete controls unless `canManage` is true; `ArticleList` renders `Spinner`, `EmptyState`, or the cards (BR-17).
- [ ] Test: non-owner USER sees no controls; owner and ADMIN see both controls; empty list renders the empty state.

**Done when:**

- `npm run test -- --run tests/component/ArticleCard.test.jsx` passes.

---

## T26 — Page: HomePage

**Covers:** BR-1, BR-13, BR-17, plan §4.6, plan §5.6.

**Files:**

- Create `frontend/src/pages/HomePage.jsx`

**Steps:**

- [ ] Render the public article list via `use_articles`, with loading, empty, and error states.
- [ ] Compute `canManage` per card using `permissions.can_manage_article` with the current session.
- [ ] Show a New Article entry point only to authenticated users.
- [ ] Keep the list order exactly as returned by the backend (most recent first, no client sorting, no pagination).

**Done when:**

- `npm run lint` passes and `npm run build` succeeds with `HomePage` wired to `use_articles`.

---

## T27 — Hook use_article + ArticleForm + ArticleDetail

**Covers:** BR-5, BR-11, BR-12, plan §4.5, plan §4.7, plan §5.8.

**Files:**

- Create `frontend/src/hooks/use_article.js`
- Create `frontend/src/components/features/article/ArticleForm.jsx`
- Create `frontend/src/components/features/article/ArticleDetail.jsx`
- Create `frontend/tests/component/ArticleForm.test.jsx`

**Steps:**

- [ ] Implement `use_article(id?)` exposing `{ article, loading, error, create, update, remove, isSubmitting }`.
- [ ] `ArticleForm` receives `{ initialValues, onSubmit, submitting, fieldErrors }` and renders only title and text (no author/time fields, BR-12); show exact backend messages inline (BR-3).
- [ ] `ArticleDetail` renders title, text, author label, and time; delete fires immediately with no confirmation dialog (BR-11) and shows a success toast (BR-5).
- [ ] Test: form shows exact `title`/`text` messages; no author/time inputs exist; delete calls `remove` without any confirm step.

**Done when:**

- `npm run test -- --run tests/component/ArticleForm.test.jsx` passes.

---

## T28 — Pages: ArticleDetailPage, ArticleCreatePage, ArticleEditPage

**Covers:** BR-5, BR-10, BR-11, BR-13, plan §4.6, plan §5.8.

**Files:**

- Create `frontend/src/pages/ArticleDetailPage.jsx`
- Create `frontend/src/pages/ArticleCreatePage.jsx`
- Create `frontend/src/pages/ArticleEditPage.jsx`

**Steps:**

- [ ] `ArticleDetailPage` loads a single article publicly, shows controls only when `can_manage_article`, and handles 404 with `ARTICLE_NOT_FOUND`.
- [ ] `ArticleCreatePage` (protected) submits via `use_article().create`, shows `ARTICLE_CREATED`, and returns to the list.
- [ ] `ArticleEditPage` (protected) loads the article, submits via `update`, shows `ARTICLE_UPDATED`, and preserves history (never sends author/time).
- [ ] Guard direct edit access by ownership in the UI while relying on the backend 403 as the authority.

**Done when:**

- `npm run lint` passes and `npm run build` succeeds with all three pages wired to `use_article`.

---

## T29 — Hook use_admin_users + UserTable

**Covers:** BR-14, plan §4.5, plan §4.7, plan §5.9, plan §6 (Decision 11).

**Files:**

- Create `frontend/src/hooks/use_admin_users.js`
- Create `frontend/src/components/features/admin/UserTable.jsx`
- Create `frontend/tests/component/UserTable.test.jsx`

**Steps:**

- [ ] Implement `use_admin_users` exposing `{ users, loading, error, refetch, promote, promotingId }` backed by `user_service`.
- [ ] `UserTable` receives `{ users, onPromote, promotingId }` and lists username, email, and role.
- [ ] Offer promote only for rows with role `USER`; show loading/empty/error states.
- [ ] Test: promote hidden/last-disabled for ADMIN rows; calling promote invokes the handler with the target id; empty/error states render.

**Done when:**

- `npm run test -- --run tests/component/UserTable.test.jsx` passes.

---

## T30 — Pages: AdminDashboardPage and NotFoundPage

**Covers:** BR-14, BR-5, BR-18, plan §4.6, plan §5.9.

**Files:**

- Create `frontend/src/pages/AdminDashboardPage.jsx`
- Create `frontend/src/pages/NotFoundPage.jsx`

**Steps:**

- [ ] `AdminDashboardPage` renders `UserTable` and promotes users via `use_admin_users`, showing `USER_PROMOTED` on success and a clear message on 403.
- [ ] Keep the page reachable only through `RequireAdmin` (wired in T31).
- [ ] `NotFoundPage` renders a simple dark not-found screen for unknown routes.
- [ ] Do not render any admin entry point for non-admins (BR-14).

**Done when:**

- `npm run lint` passes and `npm run build` succeeds with both pages present.

---

## T31 — App router wiring and provider composition

**Covers:** BR-8, BR-9, BR-14, plan §4.6, plan §2.

**Files:**

- Modify `frontend/src/App.jsx`
- Modify `frontend/src/main.jsx`
- Create `frontend/tests/integration/routing.test.jsx`

**Steps:**

- [ ] Compose providers in order: `ToastContext` -> `AuthContext` -> router.
- [ ] Declare routes exactly as in plan §4.6: `/`, `/articles/:id`, `/articles/new` (protected), `/articles/:id/edit` (protected), `/login` (guest), `/register` (guest), `/admin` (protected + admin), `*` -> `NotFoundPage`.
- [ ] Wire the `session-expired` event to a redirect to `/login?reason=session_expired`.
- [ ] Test: `/admin` redirects a guest and a USER to `/` or `/login`; an ADMIN reaches the dashboard; unknown route renders `NotFoundPage`.

**Done when:**

- `npm run test -- --run tests/integration/routing.test.jsx` passes and `npm run build` succeeds.

---

## T32 — Integration test: authentication flow

**Covers:** BR-7, BR-8, BR-9, plan §7 (auth_flow), full spec Scenarios for auth.

**Files:**

- Modify `frontend/tests/msw/handlers.js`
- Create `frontend/tests/integration/auth_flow.test.jsx`

**Steps:**

- [ ] Add MSW handlers for register, login, and the 401 session case.
- [ ] Test the flow: register -> redirected to login with `REGISTER_SUCCESS` -> login succeeds -> session persisted in `localStorage`.
- [ ] Simulate a reload and assert the session survives; then simulate a 401 and assert the session clears and redirects to login with `SESSION_EXPIRED`.
- [ ] Assert no logout control exists at any step.

**Done when:**

- `npm run test -- --run tests/integration/auth_flow.test.jsx` passes.

---

## T33 — Integration test: article CRUD and permissions

**Covers:** BR-1, BR-3, BR-5, BR-10, BR-11, BR-13, plan §7 (article_crud).

**Files:**

- Modify `frontend/tests/msw/handlers.js`
- Create `frontend/tests/integration/article_crud.test.jsx`

**Steps:**

- [ ] Add MSW handlers for public list/single and authenticated create/update/delete.
- [ ] Test: public list renders without a token in backend order; create shows `ARTICLE_CREATED` and the item appears; edit shows `ARTICLE_UPDATED` with history unchanged; delete removes with no confirmation dialog and shows `ARTICLE_DELETED`.
- [ ] Test: a non-owner USER sees no controls and a direct edit gets a 403 permission error; an ADMIN manages another user's article.

**Done when:**

- `npm run test -- --run tests/integration/article_crud.test.jsx` passes.

---

## T34 — Integration test: admin promotion

**Covers:** BR-5, BR-14, plan §7 (admin_promote), plan §6 (Decision 11, 12).

**Files:**

- Modify `frontend/tests/msw/handlers.js`
- Create `frontend/tests/integration/admin_promote.test.jsx`

**Steps:**

- [ ] Add MSW handlers for `GET /users` and `PATCH /users/{id}/role`.
- [ ] Test: a non-admin is redirected away from `/admin` and sees no entry point; an admin lists users and promotes a `USER`, seeing the role update and `USER_PROMOTED`.
- [ ] Test: a 403 from promote shows a clear permission error and leaves the row unchanged.

**Done when:**

- `npm run test -- --run tests/integration/admin_promote.test.jsx` passes.

---

## T35 — Final verification and Definition of Done

**Covers:** `AGENT.md` Definition of Done, full spec scenarios regression.

**Files:**

- Touch no source files; update `specs/003-frontend/tasks.md` checkboxes only.

**Steps:**

- [ ] Run `npm run lint` and `npm run format -- --check` with zero errors.
- [ ] Run the full suite: `npm run test -- --run` passes (unit + component + integration).
- [ ] Run `npm run build` successfully.
- [ ] Manually verify: public list needs no session and is most-recent-first with no pagination; author/time are never sent; a non-owner USER gets a 403 on direct edit/delete; an ADMIN manages any article and promotes users; a deleted article disappears; no logout control exists; the theme is dark-only and responsive.
- [ ] Confirm `spec.md`, `plan.md`, and `tasks.md` are consistent with delivered behavior.

**Done when:**

- `npm run lint` and `npm run test -- --run` pass with zero errors and `npm run build` succeeds.
