# Technical Documentation: `documentor/web/main.py`

## Overview

The `documentor/web/main.py` file serves as the web server entry point for the **Documentor** application. Built using **FastAPI**, it exposes RESTful API endpoints for generating codebase documentation, querying the generated vector store via an AI chat interface, listing generated documentation files, and reading document contents. Additionally, it mounts static web frontend files for user interaction.

---

## Dependencies & Imports

### Internal Engine & Utility Imports
* `documentor.cli.main.load_config`: Loads CLI and environment configuration settings globally upon server initialization.
* `documentor.engine.parser.ASTParser`: Parses target source code into Abstract Syntax Trees (ASTs).
* `documentor.engine.vectorizer.VectorStore`: Manages chunking, storing, and retrieving semantic vector embeddings (Chroma DB).
* `documentor.engine.mapper.DependencyMapper`: Maps dependencies across the parsed codebase.
* `documentor.engine.generator.LLMGenerator`: Runs the documentation generation pipeline using Large Language Models (LLMs).

### External Imports
* `fastapi`: Framework for building APIs (`FastAPI`, `HTTPException`, `StaticFiles`, `CORSMiddleware`).
* `pydantic`: Schema validation using `BaseModel`.
* `litellm`: Multi-provider LLM completion library.
* `pathlib.Path`: Cross-platform filesystem path manipulations.
* `os`: Used for reading environment variables (`MODEL_NAME`).

---

## Initial Server Configuration

Upon importing the module, the configuration is initialized globally:

```python
from documentor.cli.main import load_config
load_config()

app = FastAPI(title="Documentor API")
```

### CORS Middleware
To permit cross-origin requests, `CORSMiddleware` is configured with open permissions:
* **Allowed Origins:** `["*"]`
* **Allow Credentials:** `True`
* **Allowed Methods:** `["*"]`
* **Allowed Headers:** `["*"]`

---

## Data Models (Pydantic Schemas)

### `GenerateRequest`
Defines the payload required to trigger documentation generation.
* **`path`** (`str`): Absolute or relative filesystem path to the target codebase directory.
* **`model`** (`str`, optional): Specific LLM model to use. Defaults to `""`.

### `ChatMessage`
Represents an individual message in a chat history context.
* **`role`** (`str`): Author role (e.g., `"user"`, `"assistant"`, `"system"`).
* **`content`** (`str`): Message body content.

### `ChatRequest`
Defines the payload for sending a chat query regarding the codebase.
* **`query`** (`str`): User's query or prompt.
* **`path`** (`str`): Target codebase path containing the vector database.
* **`model`** (`str`, optional): Specific LLM model to use. Defaults to `""`.
* **`history`** (`list[ChatMessage]`, optional): List of preceding chat messages for multi-turn conversations. Defaults to `[]`.

---

## API Endpoints

### 1. `POST /api/generate`
Executes the full AST parsing, vector embedding, dependency mapping, and LLM documentation generation workflow for a specified repository directory.

* **Request Body:** `GenerateRequest`
* **Path Validation:** Validates if `path` points to an existing directory. Returns `400 Bad Request` if invalid.
* **Process Flow:**
  1. Instantiates `ASTParser` on `target_path` and runs `.parse()`.
  2. Initializes `VectorStore` located at `target_path / ".documentor" / "chroma"` and calls `chunk_and_store(parsed_data)`.
  3. Instantiates `DependencyMapper()`.
  4. Resolves the model: Uses `req.model` if provided, otherwise checks the `MODEL_NAME` environment variable, defaulting to `"gemini/gemini-3.6-flash"`.
  5. Initializes `LLMGenerator` with `temperature=0.0`.
  6. Inspects `target_path / "documentor_docs"` for existing `.md` files to construct a `skip_files` set (enables process resuming).
  7. Calls `generator.run_full_pipeline(...)` passing a file-writing callback function `write_file`.
* **Responses:**
  * `200 OK`: `{"status": "success", "message": "Documentation generated successfully!"}`
  * `400 Bad Request`: Directory path is invalid.
  * `500 Internal Server Error`: Execution or generation failure.

---

### 2. `POST /api/chat`
Provides an interactive chat interface over the generated codebase vector database.

* **Request Body:** `ChatRequest`
* **Path Check:** Verifies that `target_path / ".documentor" / "chroma"` exists. Returns `400 Bad Request` if missing.
* **Process Flow:**
  1. Retrieves top 5 matching document chunks from `VectorStore` using `vector_store.retrieve(req.query, n_results=5)`.
  2. Constructs a system prompt incorporating the retrieved context and 4 rigid operational rules:
     * **Rule 1:** Act as a helpful AI assistant.
     * **Rule 2:** Do not perform direct file edits (politely refuse and suggest changes in chat).
     * **Rule 3:** Avoid hallucinating codebase specifics.
     * **Rule 4:** Format suggested code changes clearly in markdown.
  3. Resolves the model (`req.model` or `MODEL_NAME` env var, fallback `"gemini/gemini-3.6-flash"`).
  4. Constructs message list (`system` prompt, followed by `history` items, ending with the user's `query`).
  5. Calls `litellm.completion(...)` with `temperature=0.0`.
* **Responses:**
  * `200 OK`: `{"answer": "<LLM response text>"}`
  * `400 Bad Request`: Missing vector store (documentation must be generated first).
  * `500 Internal Server Error`: Error during vector search or LLM completion.

---

### 3. `GET /api/docs`
Retrieves a list of generated Markdown documentation files available for a given repository.

* **Query Parameter:** `path` (`str`)
* **Process Flow:**
  1. Validates that `path` exists and is a directory (`400 Bad Request` if invalid).
  2. Scans for top-level legacy documentation files (`ARCHITECTURE.md`, `QUICKSTART.md`).
  3. Recursively scans `target_path / "documentor_docs"` for all `*.md` files.
  4. Converts relative paths to forward-slash URL format (`/`).
* **Response:**
  * `200 OK`: `{"docs": ["documentor_docs/index.md", ...]}` (sorted array of string paths).

---

### 4. `GET /api/docs/content`
Fetches the text content of a specific documentation Markdown file.

* **Query Parameters:**
  * `path` (`str`): Target project directory path.
  * `doc` (`str`): Relative path to the target Markdown file.
* **Security Check:** Ensures resolved `doc_path` resides strictly within `target_path` to prevent path traversal attacks (`403 Forbidden` if outside).
* **Existence Check:** Raises `404 Not Found` if the document does not exist.
* **Response:**
  * `200 OK`: `{"content": "<raw markdown text contents>"}`

---

## Static Files Serving

At the bottom of the file, static assets for the UI frontend are mounted:

```python
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
```

* **Location:** `documentor/web/static`
* **Route:** `/`
* **HTML Mode:** Enabled (`html=True`), automatically serving `index.html` for root visits.
* **Order Significance:** Mounted after all `/api` routes so that API routes take priority over static file matching.

---

## Error Handling & Security Summary

| Category | Implementation Detail | Status Code |
| :--- | :--- | :--- |
| **Path Traversal Protection** | Evaluates `str(doc_path).startswith(str(target_path))` in `/api/docs/content` | `403 Forbidden` |
| **Directory Validation** | Checks `.exists()` and `.is_dir()` on target repository paths | `400 Bad Request` |
| **Vector DB Presence** | Verifies existence of `.documentor/chroma` before running queries | `400 Bad Request` |
| **Missing Resource** | File existence check before reading document content | `404 Not Found` |
| **Runtime Exceptions** | Wraps pipeline operations and LLM calls in `try...except` blocks | `500 Internal Server Error` |