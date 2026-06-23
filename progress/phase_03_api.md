# Phase 3: Dataset, Prompt, & API Router Implementations

This document logs the development, structure, and design rationale behind our schemas, CRUD layers, security configurations, and REST routers.

---

## 1. Summary of Files Created / Modified

1. **[schemas/dataset.py](file:///Users/jimmycodes/LLMBench/backend/app/schemas/dataset.py):** Pydantic validation models for Dataset and TestCase request payloads.
2. **[schemas/prompt.py](file:///Users/jimmycodes/LLMBench/backend/app/schemas/prompt.py):** Prompt Arena input/output templates validation.
3. **[schemas/evaluation.py](file:///Users/jimmycodes/LLMBench/backend/app/schemas/evaluation.py):** Data schemas to represent runs, detailed judge metrics, and trigger request definitions.
4. **[schemas/regression.py](file:///Users/jimmycodes/LLMBench/backend/app/schemas/regression.py):** Structured data mapping baseline-to-target comparisons.
5. **[crud/base.py](file:///Users/jimmycodes/LLMBench/backend/app/crud/base.py):** Standard CRUD database transaction executor subclassing SQLAlchemy.
6. **[crud/dataset.py](file:///Users/jimmycodes/LLMBench/backend/app/crud/dataset.py):** Core dataset and test cases database transaction handlers.
7. **[crud/prompt.py](file:///Users/jimmycodes/LLMBench/backend/app/crud/prompt.py):** Prompt template duplicate checks and version listing.
8. **[crud/evaluation.py](file:///Users/jimmycodes/LLMBench/backend/app/crud/evaluation.py):** Evaluation run and result updates handlers.
9. **[crud/regression.py](file:///Users/jimmycodes/LLMBench/backend/app/crud/regression.py):** Regression reports fetcher.
10. **[core/security.py](file:///Users/jimmycodes/LLMBench/backend/app/core/security.py):** Access control middleware verifying standard API Token header headers.
11. **[api/v1/datasets.py](file:///Users/jimmycodes/LLMBench/backend/app/api/v1/datasets.py):** REST endpoints for datasets, singular test cases, and batch JSON imports.
12. **[api/v1/prompts.py](file:///Users/jimmycodes/LLMBench/backend/app/api/v1/prompts.py):** REST endpoints for prompt management and version comparisons.
13. **[api/v1/evaluations.py](file:///Users/jimmycodes/LLMBench/backend/app/api/v1/evaluations.py):** REST endpoints for run scheduling and regression calculation comparisons.
14. **[api/v1/router.py](file:///Users/jimmycodes/LLMBench/backend/app/api/v1/router.py):** Aggregated API v1 route aggregator.
15. **[main.py](file:///Users/jimmycodes/LLMBench/backend/app/main.py) (Modified):** Integrated v1 API router mounted under `/api/v1`.

---

## 2. Core Code Section Explanations

### Pydantic ORM Serialization Configuration (`from_attributes`)
```python
class Config:
    from_attributes = True
```
- **Like I am 5 years old 🧸:** Database items are stored inside complicated folders (SQLAlchemy models). Pydantic is a package checker who reads our templates and prints a clean report. The `from_attributes` key is a magic lens that lets Pydantic read directly from these database folders without crashing.
- **Industry Relevance 🚀:** SQLAlchemy uses lazy-loading and proxy objects for relations. In Pydantic v1, this was called `orm_mode = True`. In Pydantic v2, it is `from_attributes = True`. It enables direct parsing of database model records into JSON serializable API models.
- **Interview Relevance 🎤:** *How do you serialize database objects to JSON in FastAPI?* By configuring Pydantic schemas with `from_attributes = True`. This allows Pydantic to read properties from database objects (instead of raw dictionaries), automating serialization and nesting relations.

---

### Batch Test Case Import Router
```python
@router.post("/{dataset_id}/testcases/batch", status_code=status.HTTP_201_CREATED)
async def create_test_cases_batch(
    dataset_id: int,
    test_cases_in: List[schema_dataset.TestCaseCreate],
    db: AsyncSession = Depends(get_db),
):
    ...
```
- **Like I am 5 years old 🧸:** Instead of carrying toys up to the room one-by-one, we put a whole list of questions into a big box, check that they are all valid questions, and store them in the scrapbook at the same time.
- **Industry Relevance 🚀:** Standard APIs can choke when uploading 1,000 test cases individually. Batch import endpoints streamline inputs by validation filtering a list of schemas in a single API roundtrip.
- **Interview Relevance 🎤:** *What is the difference between single insert and batch insert API endpoints?* Single inserts generate an API roundtrip and DB query per record. Batch inserts validate lists using Pydantic arrays and write records in bulk, reducing connection pool and HTTP request overhead.

---

### Security Header Interception (`APIKeyHeader`)
```python
api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    ...
```
- **Like I am 5 years old 🧸:** Before opening the door, we ask for a password. If you don't write down the password, or write a bad one, we say "Go Away" (403 or 401 error) and don't let you see the toys.
- **Industry Relevance 🚀:** Automated pipelines (e.g. GitHub Actions running prompt evaluations) need a secure, non-interactive way to access endpoints. Header-based API keys are standard practice for machine-to-machine APIs.
- **Interview Relevance 🎤:** *Explain how header authentication is implemented in FastAPI.* We define an `APIKeyHeader` security scheme. We inject it as a route dependency using FastAPI's `Depends(verify_api_key)`. If validation fails, we raise an `HTTPException` with a 401 or 403 status code, immediately stopping execution.
