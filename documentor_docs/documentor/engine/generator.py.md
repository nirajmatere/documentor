# Technical Documentation: `documentor/engine/generator.py`

## Overview

The `documentor/engine/generator.py` module defines the `LLMGenerator` class, which serves as the multi-pass documentation generation engine within the system. It leverages the `litellm` library to interface with various Large Language Model (LLM) providers using standard API keys set in the environment.

The generator operates through distinct passes to produce:
1. An overall architecture overview (`ARCHITECTURE.md`) with Mermaid.js diagrams based on a dependency graph.
2. Individual detailed module documentation guides for each source file (`documentor_docs/<file_path>.md`).
3. A quickstart and setup guide (`QUICKSTART.md`) based on contextual search results extracted from a vector store.

---

## Class: `LLMGenerator`

The `LLMGenerator` class encapsulates configuration settings for LLM invocation, handles rate limits with exponential backoff, and provides methods to trigger specific documentation generation tasks or the complete pipeline.

### Initialization

```python
def __init__(self, model: str, temperature: float = 0.0)
```

- **`model`** (`str`): The name/identifier of the target model recognized by `litellm`.
- **`temperature`** (`float`, default `0.0`): Controls model randomness. Set to `0.0` by default to maximize determinism and factual accuracy.

---

## Key Methods

### 1. `_call_llm_with_retry`

```python
def _call_llm_with_retry(self, prompt: str, max_retries: int = 5) -> str
```

Wraps calls to `litellm.completion` with retry logic and exponential backoff to handle rate limits, server overload, or transient errors.

* **Behavior**:
  * Loops up to `max_retries` times (default is `5`).
  * Sends a single user message containing the `prompt` to `litellm.completion`.
  * Catches exceptions and checks error messages for key strings: `"rate limit"`, `"high demand"`, `"429"`, or `"too many requests"`.
  * If a rate limit or demand error is detected, sleeps for $2^{\text{attempt}}$ seconds before retrying.
  * Re-raises the exception if all retries are exhausted or if an unhandled error occurs.

---

### 2. `generate_architecture_overview`

```python
def generate_architecture_overview(self, graph: Dict[str, Any]) -> str
```

Performs **Pass A** of the documentation pipeline.

* **Parameters**:
  * `graph` (`Dict[str, Any]`): Dependency graph of the codebase containing file dependencies and key entities (classes/functions).
* **Behavior**:
  * Formats the `graph` as a JSON string.
  * Construct a prompt instructing the LLM to act as a software architect and generate an `ARCHITECTURE.md` file featuring Mermaid.js interaction diagrams.
  * Applies anti-hallucination prompt constraints.
  * Returns the LLM-generated documentation string.

---

### 3. `generate_module_guides`

```python
def generate_module_guides(
    self, 
    vector_store: Any, 
    parsed_data: Dict[str, Any], 
    progress_callback: Optional[Callable[[str], None]] = None,
    write_callback: Optional[Callable[[str, str], None]] = None,
    skip_files: Optional[Set[str]] = None,
    only_files: Optional[Set[str]] = None
) -> None
```

Performs **Pass B** of the documentation pipeline, generating individual module documentation files.

* **Parameters**:
  * `vector_store` (`Any`): Vector store reference (reserved for contextual information).
  * `parsed_data` (`Dict[str, Any]`): Dictionary containing codebase metadata, specifically expecting a key `"files"` containing a list of file dictionaries with `path` and `code`.
  * `progress_callback` (`Callable[[str], None]`, optional): Function invoked with status message updates.
  * `write_callback` (`Callable[[str, str], None]`, optional): Function invoked to write generated content to target file paths (`write_callback(file_path, content)`).
  * `skip_files` (`Set[str]`, optional): Set of destination paths to skip if already processed.
  * `only_files` (`Set[str]`, optional): Set of specific source file paths to process exclusively.
* **Execution Logic**:
  1. Iterates through each file entry in `parsed_data["files"]`.
  2. If `only_files` is specified and the current file `path` is not in it, skips the file.
  3. Constructs target destination path: `doc_path = f"documentor_docs/{path}.md"`.
  4. Skips generation if `doc_path` exists in `skip_files`.
  5. Skips files where `code.strip()` contains fewer than 50 characters to reduce unnecessary token consumption.
  6. Constructs a prompt with the source code and strict anti-hallucination rules.
  7. Invokes `_call_llm_with_retry` and writes the output using `write_callback` if provided.

---

### 4. `generate_quickstart`

```python
def generate_quickstart(self, vector_store: Any) -> str
```

Performs **Pass C** of the documentation pipeline.

* **Parameters**:
  * `vector_store` (`Any`): Instance with a `retrieve` method used to pull installation and setup contexts.
* **Behavior**:
  * Queries `vector_store.retrieve("environment variables install setup run command", n_results=5)`.
  * Extracts retrieved context documents and formats them separated by `---`.
  * Constructs a prompt requesting a `QUICKSTART.md` file based strictly on the retrieved context snippets.
  * Instructs the LLM to state if insufficient information exists rather than guessing dependencies or commands.
  * Returns the LLM-generated output string.

---

### 5. `run_full_pipeline`

```python
def run_full_pipeline(
    self, 
    parsed_data: Dict[str, Any], 
    vector_store: Any, 
    mapper: Any, 
    progress_callback: Optional[Callable[[str], None]] = None,
    write_callback: Optional[Callable[[str, str], None]] = None,
    skip_files: Optional[Set[str]] = None,
    only_files: Optional[Set[str]] = None
) -> None
```

Orchestrates the entire multi-pass execution sequence (`ARCHITECTURE.md` $\rightarrow$ `QUICKSTART.md` $\rightarrow$ Module Guides).

* **Parameters**:
  * `parsed_data` (`Dict[str, Any]`): Parsed source repository metadata.
  * `vector_store` (`Any`): Vector database handle for context lookup.
  * `mapper` (`Any`): Object containing a `map_dependencies(parsed_data)` method to build the repository dependency graph.
  * `progress_callback` (`Callable[[str], None]`, optional): Status updates callback.
  * `write_callback` (`Callable[[str, str], None]`, optional): File output writer callback.
  * `skip_files` (`Set[str]`, optional): Set of output documentation paths to bypass.
  * `only_files` (`Set[str]`, optional): Set of source files to target exclusively.

* **Pipeline Flow**:
  1. Checks if target filtering (`only_files`) is inactive:
     - **Architecture Pass**: If `documentor_docs/ARCHITECTURE.md` is not in `skip_files`, generates dependency graph via `mapper.map_dependencies(parsed_data)`, runs `generate_architecture_overview`, and invokes `write_callback`.
     - **Quickstart Pass**: If `documentor_docs/QUICKSTART.md` is not in `skip_files`, runs `generate_quickstart`, and invokes `write_callback`.
  2. **Module Guides Pass**: Calls `generate_module_guides` with supplied file filter options and callbacks.