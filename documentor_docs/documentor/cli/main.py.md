# Technical Documentation: `documentor/cli/main.py`

## Overview

The `documentor/cli/main.py` module serves as the primary Command-Line Interface (CLI) entry point for the **Documentor** application. Built using [Typer](https://typer.tiangolo.com/), this module handles environment configuration, coordinates the multi-step documentation generation pipeline, provides Retrieval-Augmented Generation (RAG) chat capabilities against codebase embeddings, and serves the Web UI.

---

## Architecture & Dependencies

### External Dependencies
* **`typer`**: Manages command-line commands, arguments, options, and colorized terminal output (`typer.secho`).
* **`litellm`**: Provides a unified API client interface for LLM completions and manages LLM API calls.
* **`uvicorn`**: ASGI server implementation used to run the web interface.
* **`dotenv` (`load_dotenv`, `set_key`)**: Manages reading and writing persistent environment variable configurations.
* **`importlib.metadata`**: Fetches the installed package version of `documentor-ai`.

### Internal Modules
* **`documentor.engine.parser.ASTParser`**: Parses codebase AST data.
* **`documentor.engine.vectorizer.VectorStore`**: Handles vector embeddings and local Chroma DB persistence.
* **`documentor.engine.mapper.DependencyMapper`**: Maps repository dependencies.
* **`documentor.engine.generator.LLMGenerator`**: Orchestrates LLM prompt execution and document content generation.

---

## Global Setup & Configuration

### Warning & Log Suppression
To maintain clean CLI execution output, LiteLLM debug logs and general Python warnings are suppressed upon module load:
```python
warnings.simplefilter("ignore")
litellm.suppress_debug_info = True
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
logging.getLogger("LiteLLMRouter").setLevel(logging.ERROR)
```

### Paths & Constants
* **`CONFIG_DIR`**: Local directory for Documentor settings (`~/.documentor`).
* **`CONFIG_FILE`**: Key-value environment store (`~/.documentor/config.env`).

---

## Functions Reference

### Helper Functions

#### `version_callback(value: bool)`
* **Purpose**: Callback function triggered when `--version` or `-v` flags are provided.
* **Behavior**: Queries package metadata for `documentor-ai`. Prints the version string (or `unknown` if uninstalled) and exits execution.

#### `load_config()`
* **Purpose**: Loads stored configuration settings into environment variables if `~/.documentor/config.env` exists.

#### `handle_litellm_error(e: Exception)`
* **Purpose**: Catches and interprets `litellm.exceptions.APIError` exceptions, formatting them into user-friendly terminal output.
* **Handled Errors**:
  * **Authentication/API Key**: Alerts user to missing/invalid API key and suggests running `documentor configure`.
  * **Context Length Exceeded**: Prompts user to select a model with a larger context window (e.g., `gemini-1.5-pro` or `gpt-4o`).
  * **Rate Limit Exceeded**: Recommends waiting or upgrading the provider API tier.
  * **Unhandled LLM Errors**: Prints full exception message.
* **Exit Code**: Always exits with status code `1`.

---

## CLI Commands Reference

### 1. Root Application Callback
```python
@app.callback()
def main(version: bool)
```
Provides the general CLI application description.
* **Options**:
  * `--version` / `-v`: Displays application version and exits.

---

### 2. `configure` Command
```python
@app.command()
def configure()
```
Configures Bring-Your-Own-LLM (BYO-LLM) settings and stores API keys in `~/.documentor/config.env`.

#### Workflow:
1. Creates directory `~/.documentor` and touches `config.env` if they do not exist.
2. Iteratively prompts the user for inputs for the following configuration fields:
   * `MODEL_NAME`
   * `GEMINI_API_KEY`
   * `OPENAI_API_KEY`
   * `ANTHROPIC_API_KEY`
3. Writes non-empty responses into `config.env` using `set_key`.
4. Handles file permission errors by notifying the user to check write access.

---

### 3. `generate` Command
```python
@app.command()
def generate(
    path: str,
    model: Optional[str] = None,
    regenerate: bool = False,
    resume: bool = True,
    files: Optional[List[str]] = None
)
```
Executes the document generation pipeline against a designated repository path.

#### Arguments & Options:
| Name | Type | Argument/Option | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `path` | `str` | Argument | *Required* | Path to target codebase directory. |
| `model` | `Optional[str]` | `--model` | Environment `MODEL_NAME` or `gemini/gemini-3.6-flash` | LiteLLM-compatible model identifier. |
| `regenerate` | `bool` | `--regenerate` | `False` | Forces total regeneration, overwriting existing `.md` files. |
| `resume` | `bool` | `--resume` | `True` | Skips generation for files already present under `documentor_docs/`. |
| `files` | `Optional[List[str]]` | `--file` / `-f` | `None` | Restricts execution to specific relative file paths. |

#### Internal Execution Flow:
1. **Load Configuration**: Calls `load_config()`.
2. **Path Resolution**: Validates that target path exists and is a directory.
3. **Step 1 (AST Parsing)**: Instantiates `ASTParser(target_path)` and executes `.parse()`.
4. **Step 2a (Vectorization)**: Initializes `VectorStore` at `<target_path>/.documentor/chroma` and calls `.chunk_and_store(parsed_data)`.
5. **Step 2b (Dependency Mapping)**: Instantiates `DependencyMapper()`.
6. **Step 3 (LLM Generator)**:
   * Instantiates `LLMGenerator(model=model, temperature=0.0)`.
   * **Resume Check**: If `resume=True` and `regenerate=False`, scans `<target_path>/documentor_docs/**/*.md` to compile a `skip_files` set.
   * Defines internal progress visualizer `print_progress(msg)` and file writer `write_file(doc_path, content)`.
   * Invokes `generator.run_full_pipeline(...)` passing parsed data, vector store, dependency mapper, progress callbacks, `skip_files`, and target `only_files`.

---

### 4. `chat` Command
```python
@app.command()
def chat(
    question: Optional[str] = None,
    path: str = ".",
    model: Optional[str] = None
)
```
Provides Retrieval-Augmented Generation (RAG) query functionality against an indexed vector store.

#### Arguments & Options:
| Name | Type | Argument/Option | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `question` | `Optional[str]` | Argument | `None` | Codebase query. If omitted, starts an interactive terminal session. |
| `path` | `str` | `--path` | `"."` | Path to repository root containing `.documentor/chroma`. |
| `model` | `Optional[str]` | `--model` | Environment `MODEL_NAME` or `gemini/gemini-3.6-flash` | Model for answer generation. |

#### Execution Flow & Prompt Rules:
1. Verifies existence of Vector Store at `<target_path>/.documentor/chroma`. Exits if not found.
2. Queries `VectorStore.retrieve(q, n_results=5)` to retrieve context snippets.
3. Constructs an LLM prompt enforcing three critical rules:
   * **Rule 1**: Refuse non-codebase, off-topic, or jailbreak questions.
   * **Rule 2**: Avoid hallucination; state if information is missing from context.
   * **Rule 3**: Explicitly state referenced code file names directly in the response.
4. Calls `litellm.completion` (`temperature=0.0`) and prints formatted responses.
5. Runs either as a single execution (if `question` parameter is supplied) or an interactive loop (terminates on input `exit` or `quit`).

---

### 5. `serve` Command
```python
@app.command()
def serve(port: int = 8000)
```
Launches the Web UI backend local application via `uvicorn`.

#### Options:
| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `port` | `int` | `8000` | Port number on `127.0.0.1` to serve the Web application. |

#### Invocation:
Runs `uvicorn.run("documentor.web.main:app", host="127.0.0.1", port=port, reload=False)`.

---

## Application Entry Point

When executed directly (`python -m documentor.cli.main`), the script invokes the Typer application:
```python
if __name__ == "__main__":
    app()
```