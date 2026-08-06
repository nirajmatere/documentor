# Technical Documentation: `documentor/cli/main.py`

## Overview

The `documentor/cli/main.py` file serves as the main Command Line Interface (CLI) entry point for the **Documentor** application. Built using the [Typer](https://typer.tiangolo.com/) framework, it integrates the core engine modules (`ASTParser`, `VectorStore`, `DependencyMapper`, and `LLMGenerator`) to provide four primary commands:

1. `configure`: Interactive setup of environment variables and API keys.
2. `generate`: Orchestration of the multi-step documentation generation pipeline.
3. `chat`: Interactive or single-prompt Retrieval-Augmented Generation (RAG) query tool against the indexed codebase.
4. `serve`: Local Web UI server deployment using Uvicorn.

---

## Global Setup & Configuration

### Directory and File Constants
* **`CONFIG_DIR`**: `Path.home() / ".documentor"` — Target directory for global application settings.
* **`CONFIG_FILE`**: `CONFIG_DIR / "config.env"` — Environment file storing API keys and model options.

### Warning and Log Management
Upon module load, logging and warnings are configured to suppress verbosity from underlying components:
* All standard Python warnings are ignored (`warnings.simplefilter("ignore")`).
* `litellm` debug information is disabled (`litellm.suppress_debug_info = True`).
* `LiteLLM` and `LiteLLMRouter` loggers are restricted to `logging.ERROR` level.

---

## Functions Reference

### `version_callback(value: bool)`
Checks if the version option was passed. If `value` is `True`, retrieves the installed package version for `documentor-ai` using `importlib.metadata.version`. If not installed as a package, reports `unknown`. Terminates execution via `typer.Exit()`.

### `main(version: Optional[bool])`
The root CLI app callback.
* **Option**: `--version` / `-v` (Eager callback executing `version_callback`).

### `load_config()`
Checks for the presence of `CONFIG_FILE` (`~/.documentor/config.env`). If present, loads its content into environment variables using `dotenv.load_dotenv`.

### `handle_litellm_error(e: Exception)`
Helper function to intercept and categorize errors raised by `litellm`. Prints formatted, color-coded error messages and actionable suggestions to stdout, then terminates execution with status code `1`:
* **Authentication/API Key Errors**: Instructs the user to run `documentor configure`.
* **Context Length Exceeded**: Advises switching to a model with a larger context window (e.g., `gemini-1.5-pro` or `gpt-4o`).
* **Rate Limits**: Suggests waiting or upgrading the API tier.
* **Uncategorized Errors**: Prints the raw error message.

---

## Commands Reference

### 1. `configure`
Interactively configures environment variables stored in `~/.documentor/config.env`.

* **Usage**: `documentor configure`
* **Workflow**:
  1. Creates the `~/.documentor` directory and touches `config.env` if missing.
  2. Prompts the user sequentially for values across four fields:
     * `MODEL_NAME`
     * `GEMINI_API_KEY`
     * `OPENAI_API_KEY`
     * `ANTHROPIC_API_KEY`
  3. Writes non-empty input values to `config.env` using `python-dotenv`'s `set_key`.
* **Error Handling**: Catches file creation/write exceptions, prints permission warnings, and exits with code `1`.

---

### 2. `generate`
Executes the documentation generation pipeline against a designated repository.

* **Usage**: `documentor generate <path> [OPTIONS]`
* **Parameters**:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `path` | Argument | *(Required)* | Path to the target repository directory. |
| `--model` | Option | Environment variable `MODEL_NAME` or `gemini/gemini-3.6-flash` | LiteLLM-compatible model identifier. |
| `--regenerate` | Option | `False` | Forces full regeneration, ignoring existing documentation files. |
| `--resume` | Option | `True` | Skips generating documentation for files that already have an existing Markdown file under `documentor_docs`. |
| `--file`, `-f` | Option | `None` (List of strings) | Specific relative file path(s) to restrict generation to. |

* **Workflow**:
  1. Calls `load_config()` and resolves the target path.
  2. **Validation**: Verifies the path exists and is a directory.
  3. **Step 1 (Parse)**: Instantiates `ASTParser` on the target directory and parses source code.
  4. **Step 2a (Vectorize)**: Stores code embeddings into a Chroma vector store located at `<repo_path>/.documentor/chroma` using `VectorStore`.
  5. **Step 2b (Map)**: Instantiates `DependencyMapper`.
  6. **Step 3 (Generate)**: Instantiates `LLMGenerator` (`temperature=0.0`).
  7. **Skip Logic**: If `--resume` is active and `--regenerate` is `False`, scans `<repo_path>/documentor_docs` for existing `.md` files and adds relative paths to `skip_files`.
  8. **Execution**: Invokes `LLMGenerator.run_full_pipeline(...)` with inline progress callbacks (`print_progress`) and file writing callbacks (`write_file`).

---

### 3. `chat`
Performs Retrieval-Augmented Generation (RAG) queries against an indexed codebase.

* **Usage**: `documentor chat [QUESTION] [OPTIONS]`
* **Parameters**:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `question` | Argument | `None` | Question string. If omitted, starts an interactive terminal session. |
| `--path` | Option | `"."` | Path to the repository context. |
| `--model` | Option | Environment variable `MODEL_NAME` or `gemini/gemini-3.6-flash` | LiteLLM-compatible model identifier. |

* **Workflow**:
  1. Calls `load_config()` and checks for the vector database path at `<target_path>/.documentor/chroma`.
  2. If the vector store does not exist, errors out requesting the user run `documentor generate` first.
  3. **RAG Logic (`run_query`)**:
     * Queries `VectorStore.retrieve(q, n_results=5)` for relevant code contexts.
     * Constructs a system prompt injecting retrieved snippets.
     * Enforces prompt constraint rules (e.g., reject off-topic questions, decline bug searches, avoid hallucination, require strict filename references).
     * Invokes `litellm.completion` with `temperature=0.0`.
     * Displays the generated response.
  4. **Interactive Mode**: If no `question` argument is supplied, runs a `while True` loop prompting user input until `exit` or `quit` is entered.

---

### 4. `serve`
Spins up the Documentor Web UI via Uvicorn.

* **Usage**: `documentor serve [OPTIONS]`
* **Parameters**:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--port` | Option | `8000` | Local port number to host the application server. |

* **Workflow**:
  * Calls `uvicorn.run("documentor.web.main:app", host="127.0.0.1", port=port, reload=False)`.