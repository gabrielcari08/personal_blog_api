# Frontend — Modern Web Interface

## 1. Objective

Deliver a modern, cohesive web interface that lets anyone read **Personal Blog** and, once authenticated, manage its content entirely from the browser.

Problem solved: the backend already exposes accounts and articles, but with no visual interface nobody can actually use them. This feature gives every visitor a public reading experience, gives registered users a self-service space to publish and manage their own articles, and gives admins a single place to oversee all content and grant admin rights.

Why a single interface: keeps the product coherent — one visual language, one navigation flow, and one continuous session — instead of a set of disconnected screens.

Out of scope: password recovery, email verification, logout, profile editing, comments, likes, categories/tags, search, drafts, pagination, rich text or image uploads, multi-language support, and a light theme. The visual design is **dark-theme only**.

## 2. Use Cases & User Flow

**Primary actors:**

*   Visitor (unauthenticated person, read-only)
*   Registered User (authenticated person with role `USER`)
*   Admin (authenticated person with role `ADMIN`)

**Secondary actor:**

*   System (the backend API plus the client-side session, validation, and feedback logic)

**Happy Path — Public reading:**

1. Visitor opens the blog.
2. System shows the article list, most recent first, with no login required.
3. Visitor opens a single article.
4. System shows title, text, author reference, and creation time.
5. No authentication is requested for any reading action.

Why public reading: maximizes reach; writing stays restricted while reading stays open.

**Happy Path — Register:**

1. Visitor opens the registration form.
2. Visitor provides username, email, and password.
3. System validates presence, format, length, and uniqueness against the backend.
4. On success, system shows a success confirmation and redirects to the login form.
5. No session is started automatically; the user must log in.

Why no auto-login: confirms the user knows their credentials and that the account was created correctly before granting access.

**Happy Path — Login:**

1. User opens the login form.
2. User provides an identifier (email **or** username) plus password.
3. System validates the credentials against the backend.
4. On success, the authenticated session begins and the user is taken to the blog with their role applied (personalized controls become visible).
5. The session persists across page refreshes and across closing/reopening the browser; no logout action is offered.

**Happy Path — Create Article:**

1. Authenticated user opens the creation form.
2. User provides title and text.
3. System validates the lengths and submits to the backend.
4. On success, a toast confirms creation and the new article appears immediately in the public list.

**Happy Path — Edit Own Article:**

1. Authenticated author opens one of their own articles.
2. System shows editing controls because the requester is the owner.
3. Author updates title and/or text.
4. System validates and submits.
5. On success, a toast confirms the update; authorship and creation time remain unchanged.

**Happy Path — Delete Own Article:**

1. Authenticated author selects delete on one of their own articles.
2. System removes the article immediately (no confirmation step) and shows a success toast.
3. The article disappears from the list and its detail page.

**Admin Oversight Flow:**

1. Admin authenticates like any user.
2. For every article, even those owned by others, the system shows editing and deletion controls.
3. Admin edits or deletes under the same validation and permanence rules as a normal author.
4. Authorship and creation time remain unchanged on edit.

Why admin can manage all: allows moderation and maintenance without impersonating the author.

**Admin Dashboard — Promote User:**

1. Admin opens the single admin dashboard.
2. System lists existing users with their current role.
3. Admin selects a `USER` and requests promotion to `ADMIN`.
4. System submits the change and, on success, shows a toast and reflects the new role in the list.

Why a dedicated dashboard: centralizes the only administrative capability of this version (role promotion) in one guarded place.

## 3. Business Rules

**Preconditions:**

*   Reading is open to everyone; no account is required.
*   Creating, editing, or deleting articles requires an authenticated session.
*   Editing or deleting another person's article requires the `ADMIN` role.
*   Accessing the admin dashboard and promoting users requires the `ADMIN` role.
*   No email verification step exists; a newly registered account is usable immediately.

**Required inputs:**

*   Register: username (required, 8-20 characters, no whitespace), email (required, valid standard format), password (required, 8-20 characters). No other fields.
*   Login: identifier (required, accepts email **or** username) + password (required).
*   Article create/edit: title (required, 8-20 characters) and text (required, 10-300 characters).
*   Promote: a target existing user plus the role `ADMIN`. The requester is identified by the active session, never by a field the user types.

**Operation rules:**

*   BR-1 Public reading: any visitor can see the article list and any single article with no session; the list is ordered most recent first with no pagination.
*   BR-2 Client validation mirrors the backend: the interface prevents submitting invalid lengths, missing fields, or malformed email before the request, but the backend remains the authority and its errors are always surfaced.
*   BR-3 Exact messages: when the backend rejects a field, the interface shows the message exactly as returned, including `title must be 8-20 characters`, `text must be 10-300 characters`, and `text is required`.
*   BR-4 Inline errors in forms: validation, duplicate, and login errors are displayed next to the corresponding form or field, not as toasts.
*   BR-5 Toasts for action results: the outcome of create, edit, delete, and promote actions is communicated as a temporary notification (toast).
*   BR-6 Generic login failure: an unknown identifier and a wrong password must produce the same generic message; the interface never reveals which part failed.
*   BR-7 No auto-login after register: successful registration leads to the login form, never directly into an authenticated area.
*   BR-8 Persistent session, no logout: once logged in, the session survives refresh and browser restart, and no logout control is offered anywhere in the interface.
*   BR-9 Session expiry handling: when the session is missing, expired, or the backend responds with an authentication failure, the interface clears the session and redirects to the login form with a notice that the session expired and the user must log in again.
*   BR-10 Ownership-aware controls: for a `USER`, editing and deletion controls are shown only on their own articles. For an `ADMIN`, these controls are shown on every article.
*   BR-11 Direct deletion, no confirmation: deleting an article removes it right away with no confirmation dialog.
*   BR-12 Author and time are read-only: the interface never offers fields to change authorship or creation time, and never sends them.
*   BR-13 Immediate visibility: a newly created article appears in the public list without any publish or review step.
*   BR-14 Admin-only dashboard: the dashboard and its promotion action are reachable and usable only with the `ADMIN` role; non-admins never see the entry point and are redirected away if they reach it.
*   BR-15 Dark theme only: the entire interface uses a single modern dark visual theme; no light theme or theme toggle exists.
*   BR-16 Responsive layout: the interface adapts to both desktop and mobile viewports, keeping reading and form actions usable at small widths.
*   BR-17 Loading and empty states: while data is being fetched, a loading indicator is shown; when the article list is empty, an explanatory empty state is shown instead of a blank area.
*   BR-18 Network/backend failure: when a request fails unexpectedly (server or network error), the interface shows a clear, non-technical error message and never leaves the user stuck on a silent blank screen.

**System limits:**

*   Article fields are limited to title, text, author reference, and creation time.
*   Title under 8 or over 20 characters is invalid. Text under 10 or over 300 characters, or empty text, is invalid.
*   Roles are limited to `USER` and `ADMIN`; promotion in this version always means granting `ADMIN`.
*   The article list has no pagination; the full list is shown ordered most recent first.
*   The interface exposes no password recovery, email verification, profile editing, or logout.

## 4. Scenarios

**Well — Successful paths:**

*   Context: visitor without a session -> When: opens the blog -> Then: article list displayed most recent first with no login required.
*   Context: visitor without a session -> When: opens a single article -> Then: title, text, author reference, and creation time displayed with no login required.
*   Context: visitor on the registration form -> When: submits valid unique username, valid email, and valid password -> Then: success confirmation shown and redirected to the login form with no session started.
*   Context: visitor after registering -> When: submits the registered identifier and correct password -> Then: authenticated, controls for their role become visible, and the session persists across refresh and browser restart.
*   Context: authenticated user on the creation form -> When: submits a valid title and text -> Then: success toast shown and the article appears immediately in the public list.
*   Context: authenticated author viewing their own article -> When: opens it -> Then: editing and deletion controls displayed.
*   Context: authenticated author on the edit form for their own article -> When: submits a new valid title and text -> Then: success toast shown, article updated, authorship and creation time unchanged.
*   Context: authenticated author selecting delete on their own article -> When: confirms the action (no confirmation dialog) -> Then: success toast shown and the article disappears from list and detail.
*   Context: authenticated admin viewing an article owned by another user -> When: opens it -> Then: editing and deletion controls displayed.
*   Context: authenticated admin on the dashboard -> When: promotes an existing `USER` to `ADMIN` -> Then: success toast shown and the user's role reflects `ADMIN` in the list.

**Bad — Failure paths:**

*   Context: registration form -> When: submits a username shorter than 8 or longer than 20 characters, or containing whitespace -> Then: a length/whitespace error shown inline, no account created.
*   Context: registration form -> When: submits an email already registered (any casing) -> Then: a duplicate-email error shown inline, no account created.
*   Context: registration form -> When: submits a username already registered (exact case) -> Then: a duplicate-username error shown inline, no account created.
*   Context: registration form -> When: submits an invalid email format, an invalid password length, or any required field empty -> Then: the corresponding error shown inline, no account created.
*   Context: login form -> When: submits a correct identifier with a wrong password -> Then: generic invalid-credentials message shown inline, no session started.
*   Context: login form -> When: submits an unknown identifier with any password -> Then: the same generic invalid-credentials message shown inline, no session started.
*   Context: authenticated user viewing an article owned by another user -> When: opens it -> Then: editing and deletion controls are not displayed.
*   Context: any session -> When: a request is rejected as forbidden -> Then: a clear permission error is shown and nothing changes in the interface.
*   Context: create/edit form -> When: submits a title outside 8-20 characters, empty text, or text outside 10-300 characters -> Then: the exact backend message shown inline, no change persisted.
*   Context: authenticated session -> When: an action is attempted on an article that no longer exists -> Then: a not-found message is shown and the list refreshes to reflect reality.
*   Context: any authenticated area -> When: the session is missing, expired, or rejected by the backend -> Then: the session is cleared and the user is redirected to the login form with a session-expired notice.
*   Context: non-admin session -> When: attempts to open the admin dashboard or promote a user -> Then: access is denied and the admin entry point is not shown.
*   Context: any page -> When: a request fails due to a server or network error -> Then: a clear non-technical error message is shown, with no blank screen or silent failure.

## [NECESITA ACLARACIÓN]

*   **Identidad del autor en la interfaz:** la respuesta de un artículo del backend solo incluye `user_id`, sin nombre de usuario ni email. Por lo tanto la interfaz no puede mostrar el nombre del autor, únicamente su referencia interna. Falta decidir si se muestra algo (por ejemplo un identificador recortado), si no se muestra autor, o si el backend debe ampliar su respuesta para incluir un nombre visible.
*   **Obtención de la identidad del usuario actual:** para ocultar/mostrar controles según propiedad y rol, el frontend necesita conocer el `id` y el `role` del usuario en sesión. El token incluye esos datos, pero no existe un endpoint de "perfil actual" ni se definió si el frontend puede/debe leer ese contenido localmente o si el backend debe exponerlo. Requiere confirmación.
*   **Destino tras login exitoso:** no se especificó a qué pantalla se entra al iniciar sesión (lista pública, pantalla de inicio, o página previa de origen). Se asumió la lista de artículos como pantalla principal, pero debe confirmarse.
*   **Alcance del dashboard de ADMIN:** se definió un dashboard único orientado a promover usuarios. Falta confirmar si ese mismo dashboard debe listar todos los usuarios con paginación/búsqueda (el backend no expone endpoints de listado de usuarios ni paginación en las specs actuales) o si basta con un flujo mínimo de promoción por identificador. El backend tampoco documenta un endpoint para **listar usuarios** existentes, lo que bloquea la promoción si se requiere seleccionar de una lista.
*   **Comportamiento del usuario promovido en su propia sesión:** si un usuario es promovido mientras tiene una sesión activa, no se definió si sus controles de admin aparecen sin volver a iniciar sesión (depende de si el rol se relee del backend o queda fijado en el token).
*   **Copys exactos de mensajes de éxito y del aviso de sesión expirada:** se definió el comportamiento, pero no los textos literales que se mostrarán al usuario (por ejemplo el mensaje exacto del toast de creación o del aviso de expiración).
