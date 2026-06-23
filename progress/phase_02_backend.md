# Phase 2: Database Schemas & Configuration Details

This document covers the core configurations, database models, and migration environments built during Phase 2.

---

## 1. Summary of Files Created

1. **[requirements.txt](file:///Users/jimmycodes/LLMBench/backend/requirements.txt):** Loose requirements allowing Python 3.13 macOS-specific binaries to compile smoothly.
2. **[core/config.py](file:///Users/jimmycodes/LLMBench/backend/app/core/config.py):** Configuration file using Pydantic Settings to aggregate env parameters.
3. **[core/database.py](file:///Users/jimmycodes/LLMBench/backend/app/core/database.py):** Async SQLAlchemy connection engine and dependency session generator (`get_db`).
4. **[models/base.py](file:///Users/jimmycodes/LLMBench/backend/app/models/base.py):** Declarative base configuration mapping custom table pluralization and global creation/modification timestamps.
5. **[models/dataset.py](file:///Users/jimmycodes/LLMBench/backend/app/models/dataset.py):** Schema declarations for datasets and individual evaluation test cases.
6. **[models/prompt.py](file:///Users/jimmycodes/LLMBench/backend/app/models/prompt.py):** Schema mapping Prompt names and specific system/user templates.
7. **[models/evaluation.py](file:///Users/jimmycodes/LLMBench/backend/app/models/evaluation.py):** Schema mapping evaluation runs and granular performance/judge results.
8. **[models/regression.py](file:///Users/jimmycodes/LLMBench/backend/app/models/regression.py):** Comparative analysis storage for baseline and target evaluation runs.
9. **[main.py](file:///Users/jimmycodes/LLMBench/backend/app/main.py):** Initial FastAPI engine setup with CORS allowances and active health endpoints.
10. **[alembic/env.py](file:///Users/jimmycodes/LLMBench/backend/alembic/env.py):** Asynchronous migrations runner mapped dynamically to Pydantic database URI configurations.
11. **[alembic/versions/001_initial_schema.py](file:///Users/jimmycodes/LLMBench/backend/alembic/versions/001_initial_schema.py):** Initial migrations script to establish databases natively when the containers start.

---

## 2. Core Code Section Explanations

### Async DB Dependency (`get_db`)
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```
- **Like I am 5 years old 🧸:** Think of this function like lending a book from the library. We open the library database drawer, hand the librarian the drawer to read or write, and if anything catches fire or drops, we safely close the drawer and undo the page edits.
- **Industry Relevance 🚀:** Prevents database connection leaks. By wrapping operations in a `try...except...finally` block, we guarantee that the database session is closed even when API endpoints throw errors.
- **Interview Relevance 🎤:** *How do you manage database connection lifecycles in FastAPI?* By using a generator function with a yield statement as a FastAPI `Depends` injection parameter. This guarantees that FastAPI manages the session lifecycle context for each incoming HTTP request, closing connections immediately after the request-response cycle completes.

---

### Dynamic Pluralized Table Naming (SQLAlchemy Base Class)
```python
@declared_attr.directive
def __tablename__(cls) -> str:
    import re
    name = cls.__name__
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    name = pattern.sub('_', name).lower()
    
    if name.endswith('y'):
        return name[:-1] + 'ies'
    elif name.endswith('s'):
        return name + 'es'
    else:
        return name + 's'
```
- **Like I am 5 years old 🧸:** Instead of writing the name of each toy chest manually, we wrote a magic rule that reads the chest tag (e.g. `TestCase`) and writes it down in a plural snake shape (e.g. `test_cases`) automatically.
- **Industry Relevance 🚀:** Prevents developer error. Keeping table naming standard and dynamic eliminates manual mismatch bugs when developers forget to specify tables or type them in singular forms.
- **Interview Relevance 🎤:** *What is the advantage of using declarative overrides or directives in SQLAlchemy?* Overrides allow building global standards across all models, like enforcing snake_case naming conventions, automatically injecting audit logging columns (created_at/updated_at), and ensuring clean schema inheritance.

---

### JSONB Formatting (TestCase & Results)
```python
meta_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, nullable=True)
```
- **Like I am 5 years old 🧸:** This is like a blank drawing notebook page. Instead of drawing specific boxes for names or numbers, we can draw whatever we want on this page (like special settings or tags) without needing a new bookcase.
- **Industry Relevance 🚀:** LLM interactions generate unstructured metadata (system configurations, temperature settings, top_p, evaluation dimensions). Postgres' **JSONB** allows storage and indexed queries inside JSON documents without requiring a rigid schema change.
- **Interview Relevance 🎤:** *Why use JSONB over JSON data types in PostgreSQL?* JSON is stored as a plain text string, requiring parsing on every read. JSONB is stored in a decomposed binary format, allowing indexing (using GIN indexes) and faster nested document queries.

---

### Async Alembic Migration Configuration
```python
async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()
```
- **Like I am 5 years old 🧸:** The builder can't build rooms if the power is cut off. We tell Alembic to wait patiently (using `await`) while it opens a line to the database, applies our drawings, and clean-up the connections when finished.
- **Industry Relevance 🚀:** Standard Alembic templates only support synchronous database drivers (like psycopg2). We configure it to run through SQLAlchemy's `asyncio` context to handle asyncpg connections, eliminating sync/async dual-driver setup.
- **Interview Relevance 🎤:** *Explain how Alembic migrations run under an asynchronous driver setup.* We use `async_engine_from_config` to initialize the database connection, then execute standard migrations within a synchronous callback (`do_run_migrations`) wrapped inside the async connection's `run_sync()` method.
