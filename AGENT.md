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

app/
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

#### 1. Domain Layer (`app/domain/`)

The core of the application. It MUST NOT import any external frameworks or libraries (No FastAPI, SQLAlchemy, Passlib, Pydantic, etc.).

- **`entities/[entity_name].py`**: Pure business entity using native Python `@dataclass`. Represents domain concepts (e.g., `Patient`, `Appointment`, `User`).
- **`repositories/[entity_name]_repository.py`**: Abstract Base Class (`ABC`) defining contracts/interfaces for persistence (e.g., `PatientRepository.get_by_id()`, `PatientRepository.save()`). Apply the dependency inversion concept.
- **`services/[service_name]_service.py`**: Domain service interfaces (`ABC`) for business operations that don't belong to a single entity.
- **`exceptions/[entity_name]_exceptions.py`**: Custom domain exceptions (e.g., `PatientNotFoundException`, `DuplicatePatientException`).

#### 2. Application Layer (`app/application/`)

Orchestrates application workflow. Coordinates domain entities and repositories to fulfill specific user actions.
It does not query the database (that's the infrastructure's job).

- **`use_cases/[entity_name]/`**: One class per use case / operation.
  - _Examples for CRUD:_ `create_[entity].py`, `get_[entity]_by_id.py`, `list_[entities].py`, `update_[entity].py`, `delete_[entity].py`.
  - _Responsibility:_ Receives abstract repositories via dependency injection, executes the workflow, and returns domain entities or DTOs.
- **`dtos/[entity_name]_dtos.py`**: Data Transfer Objects (Pydantic models or dataclasses) defining input and output data structures for the use cases.

#### 3. Infrastructure Layer (`app/infrastructure/`)

Contains all technical implementations, database models, and external tool integrations.

- **`db/models/[entity_name]_model.py`**: ORM models (SQLAlchemy) mapping physical PostgreSQL tables.
- **`repositories/postgres_[entity_name]_repository.py`**: Concrete implementation of the abstract repository defined in `domain/repositories/`. Maps ORM models to/from Domain Entities.
- **`services/`**: Concrete implementations of external domain services (e.g., cryptography, email providers, PDF generators).

#### 4. Entrypoints Layer (`app/entrypoints/`)

Exposes the system functionality through HTTP APIs while remaining completely decoupled from core logic.

- **`api/v1/routes/[entity_name]_router.py`**: FastAPI routers. Maps HTTP endpoints (`POST`, `GET`, `PUT`, `DELETE`) to Application Use Cases. Handles HTTP status codes and maps Domain Exceptions to HTTP Error responses.
- **`api/v1/dependencies.py`**: FastAPI dependency injection setup (`Depends`). Instantiates infrastructure classes and injects them into Use Cases.

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
