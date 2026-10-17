# Agent Rules - Personal Blog

## Profile

- **Role:** Act as an expert backend and frontend developer utilizing FastAPI
- **Focus:** Your obsessive focus is in security, performance, and clean, readable code.

## Technology Stack

- **Backend:** Python with FastAPI
- **Frontend:** HTML, Tailwind CSS, JavaScript with React
- **Database:** PostgreSQL

## Language and Conventions

- All code, variable names, class names, function names, database fields, code comments, and docstrings MUST be written exclusively in English. Comments and docstrings should be in Spanish. Comments the important things

## Architecture

- **Pattern:** Clean Architecture

- We strictly follow **Clean Architecture**.

- The backend lives in `backend/`; all backend commands (pytest, alembic, uvicorn) MUST run from the `backend/` directory.

backend/
└── app/
├── domain/  
 ├── application/  
 ├── infrastructure/  
 └── entrypoints/

- **Folders Explication**:
  - **domain/**: Pure business rules (zero database, frameworks or external libreries).
  - **application/**: Use Cases & DTOs (Orchestration).
  - **infrastructure/**: Framework Implementations (PostgreSQL, ORM, External Libraries).
  - **entrypoints/**: Delivery Mechanism (FastAPI Routers, Dependency Injection).

### **Layer Rules**:

#### 1. Domain Layer (`backend/app/domain/`)

The core of the application. It MUST NOT import any external frameworks or libraries (No FastAPI, SQLAlchemy, Passlib, Pydantic, etc.).

- **`entities/[entity_name].py`**: Pure business entities using native Python `@dataclass`. Must enforce domain invariants and self-validate via `__post_init__`.
- **`repositories/[entity_name]_repository.py`**: Abstract Base Classes (`ABC`) defining contracts for data access and persistence operations (e.g., `UserRepository.get_by_identifier()`).
- **`services/[service_name]_service.py`**: Abstract Base Classes (`ABC`) for domain tool interfaces (e.g., `PasswordHasher`, `TokenService`, `EmailSender`).
- **`exceptions/[entity_name]_exceptions.py`**: Custom domain exceptions for business error states (e.g., `UserNotFoundException`, `DuplicateEmailException`).

#### 2. Application Layer (`backend/app/application/`)

Orchestrates application workflow and business process execution. Coordinates domain entities, repositories, and domain services to fulfill specific user actions.

- **`use_cases/[entity_name]/`**: One class per use case / operation.
  - **Responsibility:** Receives abstract repositories and services via dependency injection, coordinates the workflow, delegates persistence to repositories, and returns DTOs.
  - **Validation boundaries (CRITICAL):**
    - DO NOT perform primitive input validations (e.g., `isinstance`, empty checks, string lengths). Pydantic DTOs handle API format validation.
    - DO NOT duplicate domain invariant validations. Domain Entities autovalidate upon instantiation.
    - ONLY handle orchestration logic and repository-level business rules (e.g., uniqueness checks against DB).
  - **Service usage:** Use abstract domain service interfaces (from `app.domain.services`). Never define inline protocols or concrete implementations here.
- **`dtos/[entity_name]_dtos.py`**: Data Transfer Objects (Pydantic models) defining input and output data structures for the use cases.

#### 3. Infrastructure Layer (`backend/app/infrastructure/`)

Contains all technical implementations, database models, and external tool integrations.

- **`db/models/[entity_name]_model.py`**: ORM models (SQLAlchemy) mapping physical database tables.
- **`repositories/postgres_[entity_name]_repository.py`**: Concrete implementation of the abstract repository defined in `domain/repositories/`. Maps ORM models to/from Domain Entities.
- **`services/`**: Concrete implementations of abstract domain services using third-party libraries (e.g., `passlib` for `PasswordHasher`, `PyJWT` for `TokenService`).

#### 4. Entrypoints Layer (`backend/app/entrypoints/`)

Exposes the system functionality through HTTP APIs while remaining completely decoupled from core logic.

- **`api/v1/routes/[entity_name]_router.py`**: FastAPI routers. Maps HTTP endpoints to Application Use Cases. Handles HTTP status codes and maps Domain Exceptions to HTTP Error responses.
- **`api/v1/dependencies.py`**: FastAPI dependency injection setup (`Depends`). Instantiates infrastructure classes and injects them into Use Cases.

#### 5. Presentation Layer (`frontend/src/components/` & `frontend/src/pages/`)

Handles visual rendering and direct user interaction. MUST NOT execute direct HTTP calls or perform complex data transformations.

- **`components/ui/`**: Atomic, business-agnostic UI elements (e.g., buttons, inputs, modals, spinners) styled with Tailwind CSS.
- **`components/features/[entity_name]/`**: Entity-specific visual components (e.g., `ArticleCard.jsx`, `LoginForm.jsx`). Delegates state and actions to custom hooks.
- **`pages/`**: Full route views (e.g., `HomePage.jsx`, `LoginPage.jsx`). Assembles feature components and layout structures.

#### 6. Application Logic & State Layer (`frontend/src/hooks/` & `frontend/src/context/`)

Orchestrates UI state, reactivity, and global authentication/session context.

- **`hooks/use_[entity_name].js`**: Custom hooks encapsulating API service integration, loading/error states, and local UI reactivity.
- **`context/`**: React Context providers managing global application state (e.g., `AuthContext.jsx` for JWT lifecycle and active user credentials).

#### 7. Service & Infrastructure Layer (`frontend/src/services/` & `frontend/src/api/`)

Handles remote communication with the FastAPI backend. Decouples UI components from specific HTTP clients and endpoint configurations.

- **`api/client.js`**: Centralized HTTP client instance (Axios / Fetch wrapper). Configures base URL (`/api/v1`), default headers, and JWT request/response interceptors.
- **`services/[entity_name]_service.js`**: Pure functions executing HTTP requests targeting backend routes (e.g., `authService.login()`, `articleService.getAll()`).

#### 8. Domain & Utility Layer (`frontend/src/utils/` & `frontend/src/types/`)

Pure helper functions, data mapping utilities, and shared constants.

- **`utils/`**: Helper functions (e.g., ISO 8601 UTC date formatting to local browser timezone, `localStorage` wrappers).

## Workflow (Spec-Driven Development)

1. Before making any file modifications or creating new ones, enter **Plan Mode**.
2. Wait for the user's explicit validation before entering Act Mode (execution).
3. Do not generate code without the user validating the intention in a `spec.md` file or execution plan.
4. The generated code must strictly follow PEP8.

## Security Rules and Restrictions

- Never hardcode secrets, passwords, or API keys. Always use `.env` files.
- Validate and sanitize all incoming input parameters.

## Definition of Done (DoN)

A task or module is considered DONE only when:

- [ ] Code passes all linters and formatters with zero errors.
- [ ] Unit tests are created and passing for core logic.
- [ ] The corresponding `spec.md` and documentation files are updated.
