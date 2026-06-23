# Phase 7: Testing Framework

This document logs the design, implementation, and relevance of our test suite architecture and mocks setup built during Phase 7.

---

## 1. Summary of Files Created

1. **[tests/conftest.py](file:///Users/jimmycodes/LLMBench/tests/conftest.py):** Houses Pytest shared fixtures including the asynchronous HTTPX test client and override mocks for SQLAlchemy database sessions.
2. **[tests/test_api/test_datasets.py](file:///Users/jimmycodes/LLMBench/tests/test_api/test_datasets.py):** Verifies the dataset creation, retrieval, and API Key authorization routes.
3. **[tests/test_evaluation/test_judge.py](file:///Users/jimmycodes/LLMBench/tests/test_evaluation/test_judge.py):** Verifies the Claude-as-a-Judge parser, testing JSON schema cleaning and fallbacks.

---

## 2. Core Code Section Explanations

### Async API Overrides (`dependency_overrides`)
```python
@pytest.fixture
def client(mock_db: AsyncMock) -> Generator[AsyncClient, None, None]:
    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    ...
```
- **Like I am 5 years old 🧸:** When the tester comes to check the shop, we don't let them play with the real cash register because they might lose real money. We swap out the real register (`get_db`) with a toy register (`mock_db`) so the tester can push buttons safely without messing up the shop records.
- **Industry Relevance 🚀:** Unit testing endpoints shouldn't rely on live database connections. FastAPI's `dependency_overrides` dictionary allows swapping out database sessions, authentication callbacks, or third-party client drivers dynamically.
- **Interview Relevance 🎤:** *How do you override database dependencies in FastAPI when running tests?* We inject a mock database session using FastAPI's `dependency_overrides` map. We set the key as the original generator function (`get_db`) and map it to a mock generator (`override_get_db`) that yields our mock session. We clear this map after each test using `app.dependency_overrides.clear()` to prevent side effects.

---

### Clean Markdown JSON Parsing Tests
```python
mock_markdown_response = """```json
{
  "accuracy": 4.0,
  ...
}
```"""
# Asserts evaluate_with_judge strips markdown and parses correctly.
```
- **Like I am 5 years old 🧸:** Sometimes the robot replies with extra labels (like drawing a box around the answer). The tester makes sure that our code is smart enough to throw away the box packaging and read the score numbers inside correctly without getting confused.
- **Industry Relevance 🚀:** Large Language Models often wrap their JSON outputs inside markdown backticks (e.g. ````json ... ````). Testing parsing heuristics ensures the application doesn't crash when encountering these common LLM output variants.
- **Interview Relevance 🎤:** *How do you ensure robustness when parsing structured JSON outputs from LLMs?* We write unit tests that supply malformed or markdown-wrapped JSON strings (e.g., enclosing code blocks) and assert that our cleaning regex filters strip the wrapping and parse the inner JSON successfully, returning standard objects.
