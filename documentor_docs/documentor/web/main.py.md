# Technical Documentation: `documentor/web/main.py`

## Overview

The `documentor/web/main.py` module defines the backend Web API server for the **Documentor** application using **FastAPI**. It exposes HTTP endpoints that interface with the application's engine components (`ASTParser`, `VectorStore`, `DependencyMapper`, and `LLMGenerator`) to perform documentation generation, context-aware RAG (Retrieval-Augmented Generation) chat queries, and document retrieval. Additionally, it mounts and serves static files for the web user interface.

---

## Configuration and Initialization

Upon loading the module, the following initialization steps occur:

1. **Configuration Loading:** Calls `load_config()` from `documentor.cli.main` globally to populate application settings.
2. **FastAPI App Creation:** Instantiates the application `app = FastAPI(title="Documentor API")`.
3. **CORS Middleware Setup:** Adds `CORSMiddleware` to allow cross-origin requests from any origin (`"*"`) with standard headers and methods.
4. **Static File Directory Resolution:** Sets `STATIC_DIR` relative to `documentor/web/main.py` at `./static`.

---

## Data Models (Pydantic Schemas)

### `GenerateRequest`
Defines the request body for triggering documentation generation.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `path` | `str` | Required | Target directory path containing the codebase to document. |
| `model` | `str` | `""` | Optional LLM model identifier. If empty, falls back to `MODEL_NAME` env var or `"gemini/gemini-3.6-flash"`. |

### `ChatRequest`
Defines the request body for RAG-based chat interactions.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `query` | `str` | Required | User's search query or prompt regarding the codebase. |
| `path` | `str` | Required | Target directory path where the vector store resides. |
| `model` | `str` | `""` | Optional LLM model identifier. If empty, falls back to `MODEL_NAME` env var or `"gemini/gemini-3.6-flash"`. |

---

## API Endpoints

### 1. `POST /api/generate`
Triggers the full documentation generation pipeline for a target directory.

* **Function:** `api_generate(req: GenerateRequest)`
* **Workflow:**
  1. Resolves `req.path` to an absolute path (`target_path`).
  2. Validates that `target_path` exists and is a valid directory (raises HTTP `400` if invalid).
  3. Parses the target directory AST using `ASTParser(str(target_path)).parse()`.
  4. Vectorizes the parsed data into Chroma DB located at `target_path / ".documentor" / "chroma"` using `VectorStore`.
  5. Instantiates `DependencyMapper`.
  6. Configures `LLMGenerator` with `temperature=0.0` and the selected model (uses `req.model`, `MODEL_NAME` environment variable, or defaults to `"gemini/gemini-3.6-flash"`).
  7. Defines an internal callback `write_file(doc_path: str, content: str)` to create directories and save generated markdown files to `target_path / doc_path`.
  8. Checks for existing markdown files in `target_path / "documentor_docs"` to build a `skip_files` set, supporting process resumption.
  9. Executes `generator.run_full_pipeline(...)`.
* **Response:**
  * **Success (200):** `{"status": "success", "message": "Documentation generated successfully!"}`
  * **Errors:**
    * HTTP `400`: Path is not a valid directory.
    * HTTP `500`: Pipeline failure or unhandled exception.

---

### 2. `POST /api/chat`
Provides RAG-based Q&A capabilities against the stored vector embeddings of the codebase.

* **Function:** `api_chat(req: ChatRequest)`
* **Workflow:**
  1. Checks for the vector database directory at `target_path / ".documentor" / "chroma"`. Raises HTTP `400` if absent.
  2. Queries `VectorStore` for the top 5 relative context snippets (`n_results=5`).
  3. Joins retrieved snippets with `"\n---\n"`.
  4. Formulates a strict prompt specifying:
     * Restrict responses strictly to the provided codebase context.
     * Do not answer general or out-of-scope questions.
     * Do not hallucinate; acknowledge missing information.
     * Explicitly cite code filenames in the answer.
  5. Calls `litellm.completion` with `temperature=0.0`.
* **Response:**
  * **Success (200):** `{"answer": "<LLM response string>"}`
  * **Errors:**
    * HTTP `400`: Missing vector store (documentation has not been generated).
    * HTTP `500`: Retrieval or LLM execution failure.

---

### 3. `GET /api/docs`
Lists available Markdown documentation files within the specified project path.

* **Function:** `api_get_docs(path: str)`
* **Workflow:**
  1. Validates that `path` is an existing directory (raises HTTP `400` if invalid).
  2. Scans for top-level fallback files (`ARCHITECTURE.md`, `QUICKSTART.md`).
  3. Recursively scans `target_path / "documentor_docs"` for `.md` files.
  4. Formats file paths relative to `target_path` using forward slashes (`/`).
* **Response:**
  * **Success (200):** `{"docs": ["documentor_docs/...", ...]} ` (sorted list of relative document paths)
  * **Errors:**
    * HTTP `400`: Target directory does not exist or is invalid.

---

### 4. `GET /api/docs/content`
Retrieves the raw text content of a specific documentation file.

* **Function:** `api_get_doc_content(path: str, doc: str)`
* **Workflow:**
  1. Resolves `target_path` and target `doc_path` (`target_path / doc`).
  2. **Security Check:** Ensures `doc_path` is located inside `target_path` to prevent path traversal attacks (raises HTTP `403` if breached).
  3. Ensures the file exists (raises HTTP `404` if not found).
  4. Reads and returns file contents encoded in UTF-8.
* **Response:**
  * **Success (200):** `{"content": "<file text content>"}`
  * **Errors:**
    * HTTP `403`: Access denied (attempted path traversal).
    * HTTP `404`: Document file not found.

---

## Static File Serving

To serve the frontend client directly, static files are mounted at the root path (`/`):

```python
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
```

* **Positioning:** This mount statement is executed at the end of the file to ensure API routes (`/api/*`) take precedence over static file resolution.
* **HTML Mode:** `html=True` allows direct serving of single-page applications or standard `index.html` files.

---

## Error & Security Summary

* **Path Traversal Protection:** Implemented in `api_get_doc_content` via `doc_path.startswith(target_path)`.
* **Path Validation:** Checks exist across endpoints (`.exists()`, `.is_dir()`) returning standard HTTP exception codes (`400`, `403`, `404`, `500`).