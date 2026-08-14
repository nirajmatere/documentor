# Technical Documentation Guide: `tests/test_web.py`

## Overview

The `tests/test_web.py` file contains integration and unit tests for the web interface endpoints of the `documentor` application. Using `pytest` and FastAPI's `TestClient`, this test suite validates HTTP responses, status codes, and error messages for specific routes defined in `documentor.web.main.app`.

Specifically, it tests:
- Error handling for nonexistent directory paths across multiple endpoints (`/api/docs`, `/api/generate`).
- Error handling when attempting to query the chat endpoint (`/api/chat`) before a vector store database has been generated.
- Root path (`/`) behavior for serving static HTML content.

---

## Dependencies & Setup

### Modules and Imports

```python
import pytest
from fastapi.testclient import TestClient
from documentor.web.main import app
```

- **`pytest`**: The test framework used for running tests and managing fixtures (e.g., `tmp_path`).
- **`fastapi.testclient.TestClient`**: A test client that wraps the FastAPI application to allow synchronous testing of HTTP endpoints without launching a full web server.
- **`documentor.web.main.app`**: The FastAPI application instance under test.

### Client Initialization

```python
client = TestClient(app)
```

A module-level `TestClient` instance is instantiated using the imported FastAPI `app`. This client is reused across all test functions in the file to issue simulated HTTP requests.

---

## Key Test Functions

### 1. `test_api_docs_invalid_path()`

Tests error handling for the `/api/docs` endpoint when provided with a directory path that does not exist.

* **HTTP Method**: `GET`
* **Target Endpoint**: `/api/docs`
* **Query Parameters**: `path=/path/that/does/not/exist`
* **Assertions**:
  * **Status Code**: Asserts that the response status code is `400 Bad Request`.
  * **Response Body**: Asserts that the JSON response `detail` field contains the error message `"Provided path is not a valid directory."`.

---

### 2. `test_api_generate_invalid_path()`

Tests error handling for the `/api/generate` endpoint when supplied with an invalid filesystem directory path in the request body.

* **HTTP Method**: `POST`
* **Target Endpoint**: `/api/generate`
* **JSON Payload**:
  ```json
  {
    "path": "/path/that/does/not/exist",
    "model": "gemini/gemini-3.6-flash"
  }
  ```
* **Assertions**:
  * **Status Code**: Asserts that the response status code is `400 Bad Request`.
  * **Response Body**: Asserts that the JSON response `detail` field contains the error message `"Provided path is not a valid directory."`.

---

### 3. `test_api_chat_no_vector_db(tmp_path)`

Tests the behavior of the `/api/chat` endpoint when a valid directory exists but does not contain a pre-existing vector store database.

* **Parameters**: Uses Pytest's built-in `tmp_path` fixture to provide a temporary, valid directory path.
* **HTTP Method**: `POST`
* **Target Endpoint**: `/api/chat`
* **JSON Payload**:
  ```json
  {
    "path": "<str(tmp_path)>",
    "query": "Hello",
    "model": "gemini/gemini-3.6-flash"
  }
  ```
* **Assertions**:
  * **Status Code**: Asserts that the response status code is `400 Bad Request`.
  * **Response Body**: Asserts that the JSON response `detail` field contains the error message `"Vector store not found. Generate documentation first."`.

---

### 4. `test_static_files()`

Validates that the root endpoint correctly serves the main static HTML file (`index.html`).

* **HTTP Method**: `GET`
* **Target Endpoint**: `/`
* **Assertions**:
  * **Status Code**: Asserts that the response status code is `200 OK`.
  * **Headers**: Asserts that the `content-type` header includes `"text/html"`.

---

## Execution Summary Table

| Test Function | Endpoint Tested | Request Details | Expected Status Code | Key Assertion / Detail Message |
| :--- | :--- | :--- | :--- | :--- |
| `test_api_docs_invalid_path` | `GET /api/docs` | `path=/path/that/does/not/exist` | `400` | `"Provided path is not a valid directory."` |
| `test_api_generate_invalid_path` | `POST /api/generate` | JSON payload with invalid `path` | `400` | `"Provided path is not a valid directory."` |
| `test_api_chat_no_vector_db` | `POST /api/chat` | JSON payload with valid `tmp_path`, missing vector DB | `400` | `"Vector store not found. Generate documentation first."` |
| `test_static_files` | `GET /` | None | `200` | Header `content-type` contains `"text/html"` |