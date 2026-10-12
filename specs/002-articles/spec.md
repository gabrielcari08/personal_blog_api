# Articles — Create, View, Edit and Delete

## 1. Objective

Enable authenticated users of **Personal Blog** to publish and manage short text articles, while keeping public reading open to everyone.

Problem solved: without this functionality the blog has users but no content. This feature gives `USER` authors full ownership over their own articles (create, read, update, delete) and gives `ADMIN` oversight over all articles to moderate or maintain content quality, without restricting read access.

Out of scope: drafts, publishing states, comments, likes, categories/tags, rich text or images, version history, and recovery of deleted articles.

## 2. Use Cases & User Flow

**Primary actors:**

*   Visitor (unauthenticated person, read-only)
*   Registered User (authenticated person with role `USER`)
*   Admin (authenticated person with role `ADMIN`)

**Secondary actor:**

*   System (validates inputs, enforces ownership, enforces role rules, assigns authorship and creation time)

**Happy Path — Create:**

1. Authenticated user opens creation form.
2. User provides title and text.
3. System validates presence and length limits.
4. System assigns authorship to the current user and records creation time.
5. System stores the article and confirms successful creation.
6. Article becomes immediately visible in public reading.

Why immediate visibility: articles are simple public posts with no review workflow in this version, so publishing is instant.

Why system-assigned authorship: prevents impersonation and guarantees that ownership always reflects the real creator.

**Happy Path — View:**

1. Any person (visitor, user, or admin) opens the article list or a single article.
2. System displays title, text, author reference, and creation time.
3. No authentication is required to read.

Why public reading: maximizes reach of the blog; writing is restricted but knowledge sharing is open.

**Happy Path — Edit own article:**

1. Authenticated author opens their own article.
2. System shows editing options because the requester is the owner (or admin).
3. Author updates title and/or text.
4. System validates new values against the same creation rules.
5. System stores the changes, keeping original authorship and creation time unchanged.
6. System confirms successful update.

Why only title and text are editable: authorship and creation time are historical facts and must remain immutable to preserve trust.

**Happy Path — Delete own article:**

1. Authenticated author selects delete on their own article.
2. System verifies ownership (or admin role).
3. System permanently removes the article.
4. System confirms successful deletion; article no longer appears in public reading.

Why permanent direct deletion: keeps behavior simple in this version with no trash, recovery, or confirmation step.

**Admin Oversight Flow:**

1. Admin authenticates.
2. Admin views any article (same public view).
3. For any article, even ones owned by others, system shows editing and deletion options to the admin.
4. Admin edits title/text or deletes the article under the same validation and permanence rules as a normal author.
5. Authorship and creation time remain unchanged on edit.

Why admin can manage all: allows moderation and maintenance without needing to impersonate the author.

## 3. Business Rules

**Preconditions:**

*   To create, edit, or delete, the person must be authenticated. Visitors cannot create, edit, or delete.
*   To edit or delete a specific article, the article must exist.
*   To edit or delete another person's article, the requester must have role `ADMIN`.

**Required inputs:**

*   Create: title (required), text (required). Author and creation time are never requested; they are assigned by the system.
*   Edit: title (required), text (required). Author and creation time are never editable.
*   Delete: no additional inputs; only the target article identity and the requester identity/role.

**Operation rules:**

*   BR-1 Public read: any person, including unauthenticated visitors, can list and read all articles.
*   BR-2 Authenticated creation: only authenticated users with role `USER` or `ADMIN` can create articles. An article created by an `ADMIN` is owned by that admin like any other author.
*   BR-3 Ownership on creation: the author of a new article is always the currently authenticated user; client-supplied author values are ignored.
*   BR-4 Creation time on creation: creation time is assigned by the system at creation and never changes afterwards. It follows the same handling as user creation time: system-assigned, timezone-aware, and audit-only (never requested nor editable).
*   BR-5 Owner-only mutation: a user with role `USER` can edit or delete only articles where they are the author.
*   BR-6 Admin override: a user with role `ADMIN` can edit or delete any article regardless of authorship, under the same validation rules.
*   BR-7 Hidden actions plus direct enforcement: editing and deletion options for an article must not be displayed to a `USER` who is not its author. `ADMIN` always sees these options. In addition, the system must directly reject any edit or delete attempt by a non-owner `USER` on another person's article as forbidden, even if the request bypasses the interface.
*   BR-8 Editable fields: only title and text can change on edit. Author and creation time are immutable, even for `ADMIN`.
*   BR-9 Title length: title must be 8-20 characters inclusive. Any violation, including empty, is rejected with exact error message: `title must be 8-20 characters`.
*   BR-10 Text length: text must be 10-300 characters inclusive. Empty text is rejected with exact error message: `text is required`. Any non-empty text shorter than 10 or longer than 300 characters is rejected with exact error message: `text must be 10-300 characters`.
*   BR-11 Character counting: length is counted on the raw value with no trimming. Spaces, line breaks, and emojis each count as one character.
*   BR-12 Listing order: the public article list is ordered most recent first by creation time. No pagination applies in this version.
*   BR-13 No modification timestamp: the model stores only creation time; no last-modified time is recorded or displayed in this version.
*   BR-14 Permanent deletion: successful deletion removes the article definitively with no recovery path and no confirmation step in this version.

**System limits:**

*   Article data is limited to title, author reference, text, and creation time. No other fields exist in this version.
*   Title under 8 or over 20 characters is invalid. Text under 10 or over 300 characters is invalid; empty text is invalid.
*   One article has exactly one author; authorship cannot be transferred.
*   Public list has no pagination; full list is shown ordered most recent first.

## 4. Scenarios

**Well — Successful paths:**

*   Context: authenticated user with role `USER` on creation form -> When: submits title 8-20 chars and text 10-300 chars -> Then: article created with requester as author and system creation time, immediately publicly visible.
*   Context: authenticated admin on creation form -> When: submits valid title and text -> Then: article created owned by that admin and publicly visible.
*   Context: any visitor without login viewing blog -> When: requests article list -> Then: all articles displayed ordered most recent first with no pagination and no login required.
*   Context: any visitor without login viewing blog -> When: requests single article -> Then: title, text, author reference, and creation time displayed with no login required.
*   Context: authenticated author viewing their own article -> When: opens article -> Then: editing and deletion options displayed.
*   Context: authenticated author on edit form for own article -> When: submits new valid title and text -> Then: article updated, author and creation time unchanged.
*   Context: authenticated admin viewing article owned by another user -> When: opens article -> Then: editing and deletion options displayed.
*   Context: authenticated admin on edit form for another user's article -> When: submits valid title and text -> Then: article updated, original author and creation time unchanged.
*   Context: authenticated author selecting delete on own article -> When: requests deletion -> Then: article permanently removed and no longer publicly visible.
*   Context: authenticated admin selecting delete on another user's article -> When: requests deletion -> Then: article permanently removed and no longer publicly visible.

**Bad — Failure paths:**

*   Context: unauthenticated visitor -> When: attempts to create an article -> Then: rejected as unauthorized, no article created.
*   Context: unauthenticated visitor -> When: attempts to edit or delete any article -> Then: rejected as unauthorized, nothing changes.
*   Context: creation form with title shorter than 8 or longer than 20 chars -> When: submits -> Then: rejected with exact error `title must be 8-20 characters`, no article created.
*   Context: creation form with text longer than 300 or shorter than 10 chars (non-empty) -> When: submits -> Then: rejected with exact error `text must be 10-300 characters`, no article created.
*   Context: creation form with empty text -> When: submits -> Then: rejected with exact error `text is required`, no article created.
*   Context: creation form with title containing spaces, line breaks, or emojis -> When: submits -> Then: each counts as one character toward the 8-20 limit.
*   Context: creation form with text containing spaces, line breaks, or emojis -> When: submits -> Then: each counts as one character toward the 10-300 limit, with no trimming applied.
*   Context: authenticated user with role `USER` viewing article owned by another user -> When: opens article -> Then: editing and deletion options not displayed.
*   Context: authenticated user with role `USER` attempting edit on another user's article -> When: submits edit directly -> Then: rejected as forbidden, article unchanged.
*   Context: authenticated user with role `USER` attempting delete on another user's article -> When: requests deletion directly -> Then: rejected as forbidden, article not removed.
*   Context: edit form for existing article -> When: submits title or text violating length limits -> Then: rejected with corresponding length error, original values preserved.
*   Context: edit or delete request for non-existent article -> When: submitted by any authenticated user -> Then: rejected as not-found, nothing changes.

## [NECESITA ACLARACIÓN]

*   Sin puntos pendientes. Todas las dudas fueron resueltas: mensajes exactos (`title must be 8-20 characters`, `text must be 10-300 characters`, `text is required` para vacío), conteo sin recorte (espacios, saltos y emojis valen 1), ocultamiento más bloqueo directo con prohibido, listado con más recientes primero sin paginación, y `created_at` igual que en users (asignado por el sistema, con zona horaria, solo auditoría).
