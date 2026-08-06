# Technical Documentation: `documentor/engine/generator.py`

## Overview

The `documentor/engine/generator.py` module houses the `LLMGenerator` class, which serves as the core orchestration component for multi-pass documentation generation. Utilizing the `litellm` library, this module interfaces with Language Models (LLMs) to generate repository documentation—specifically architectural overviews, individual module/file guides, and quickstart documentation—while handling API rate limits through exponential backoff retries.

---

## Class Summary

### `LLMGenerator`

The primary class defined in this module. It manages prompt construction, interactions with LLMs via LiteLLM, error handling for rate limits, and step-by-step pipeline execution for documentation generation.

---

## Methods & Key Components

### `__init__(self, model: str, temperature: float = 0.0)`
Initializes the `LLMGenerator` instance.

* **Parameters:**
  * `model` (`str`): The target LLM model identifier (passed to LiteLLM).
  * `temperature` (`float`, default `0.0`): The temperature setting for model completion calls. Defaults to `0.0` for maximum determinism.

---

### `_call_llm_with_retry(self, prompt: str, max_retries: int = 5) -> str`
A helper method that executes LLM completion calls wrapped in exponential backoff logic to handle rate limiting and API throttling.

* **Parameters:**
  * `prompt` (`str`): The user prompt to be sent to the LLM.
  * `max_retries` (`int`, default `5`): Maximum number of attempts before raising an exception.
* **Behavior:**
  * Calls `litellm.completion` using the specified model, message role (`"user"`), and temperature.
  * Catches `Exception` instances. If the error message indicates rate limiting, high demand, HTTP 429, or too many requests, it sleeps for $2^{\text{attempt}}$ seconds before retrying.
  * Raises the exception if all retries fail or if the error is non-retryable.
* **Returns:**
  * `str`: The text content of the LLM's response (`response.choices[0].message.content`).

---

### `generate_architecture_overview(self, graph: Dict[str, Any]) -> str`
Executes Pass A of the generation process to create a high-level system overview.

* **Parameters:**
  * `graph` (`Dict[str, Any]`): Dependency graph of the codebase containing file dependencies and key entities (classes/functions).
* **Behavior:**
  * Serializes the `graph` dictionary into formatted JSON (`indent=2`).
  * Constructs a prompt instructing the LLM to write an `ARCHITECTURE.md` file including a Mermaid.js interaction diagram.
  * Enforces a prompt-level constraint prohibiting hallucination.
* **Returns:**
  * `str`: The generated `ARCHITECTURE.md` content.

---

### `generate_module_guides(...) -> None`
Executes Pass B of the generation process, writing standalone markdown documentation guides for individual source code files in the repository.

* **Parameters:**
  * `vector_store` (`Any`): Vector store reference (unused directly within this pass).
  * `parsed_data` (`Dict[str, Any]`): Dictionary containing code analysis metadata under the `"files"` key.
  * `progress_callback` (`Optional[Callable[[str], None]]`, optional): Optional callback function for status messages.
  * `write_callback` (`Optional[Callable[[str, str], None]]`, optional): Callback function accepting `(file_path, content)` to save generated output.
  * `skip_files` (`Optional[Set[str]]`, optional): Set of output file paths (`documentor_docs/<path>.md`) to skip if already processed.
  * `only_files` (`Optional[Set[str]]`, optional): Set of source file paths to process selectively.
* **Behavior:**
  1. Iterates through file entries inside `parsed_data["files"]`.
  2. Filters out files not present in `only_files` (if specified).
  3. Skips files if their target doc path exists in `skip_files`.
  4. Skips files whose source code length is under 50 stripped characters.
  5. Formats a prompt containing the source code and file path.
  6. Calls `_call_llm_with_retry` and executes `write_callback` with the output target path (`documentor_docs/<path>.md`) and generated content.

---

### `generate_quickstart(self, vector_store: Any) -> str`
Executes Pass C of the generation process, writing setup and quickstart documentation based on code context extracted from the vector store.

* **Parameters:**
  * `vector_store` (`Any`): An object implementing a `retrieve` method.
* **Behavior:**
  * Invokes `vector_store.retrieve("environment variables install setup run command", n_results=5)`.
  * Joins retrieved context documents with `\n---\n`.
  * Constructs a prompt for generating `QUICKSTART.md` strictly using the context snippets provided.
* **Returns:**
  * `str`: The generated `QUICKSTART.md` content.

---

### `run_full_pipeline(...) -> None`
Orchestrates the complete multi-pass generation execution.

* **Parameters:**
  * `parsed_data` (`Dict[str, Any]`): Parsed codebase metadata.
  * `vector_store` (`Any`): Vector store for context retrieval.
  * `mapper` (`Any`): Object implementing `map_dependencies(parsed_data)` to generate the dependency graph.
  * `progress_callback` (`Optional[Callable[[str], None]]`, optional): Callback for emitting progress updates.
  * `write_callback` (`Optional[Callable[[str, str], None]]`, optional): Callback for writing output files.
  * `skip_files` (`Optional[Set[str]]`, optional): Set of target document paths to skip.
  * `only_files` (`Optional[Set[str]]`, optional): Set of specific source paths to generate documentation for.
* **Execution Flow:**
  1. Checks if `only_files` is set. If `only_files` is **not** set:
     * Checks if `documentor_docs/ARCHITECTURE.md` is in `skip_files`. If not, maps dependencies via `mapper.map_dependencies(parsed_data)`, generates the architecture overview, and writes `documentor_docs/ARCHITECTURE.md`.
     * Checks if `documentor_docs/QUICKSTART.md` is in `skip_files`. If not, generates the quickstart documentation and writes `documentor_docs/QUICKSTART.md`.
  2. Invokes `generate_module_guides` with all supplied arguments to document individual source files.

---

## Workflow Diagram

```
                       run_full_pipeline()
                                |
       +------------------------+------------------------+
       | (If only_files is None)                         |
       v                                                 v
Generate ARCHITECTURE.md                          Generate QUICKSTART.md
(mapper.map_dependencies +                        (vector_store.retrieve +
 generate_architecture_overview)                   generate_quickstart)
       |                                                 |
       +------------------------+------------------------+
                                |
                                v
                   generate_module_guides()
             Iterates over parsed_data["files"]
                                |
                                v
                     _call_llm_with_retry()
              (LiteLLM call with Exponential Backoff)
                                |
                                v
                         write_callback()
```

---

## Exception & Retry Mechanics

The internal call method `_call_llm_with_retry` intercepts runtime exceptions resulting from LLM interaction. It identifies standard rate limit errors by checking for the presence of the following substrings (case-insensitive) within the exception string:
* `"rate limit"`
* `"high demand"`
* `"429"`
* `"too many requests"`

When encountered, execution pauses via `time.sleep(2 ** attempt)` for up to 5 attempts ($2^0=1\text{s}, 2^1=2\text{s}, 2^2=4\text{s}, 2^3=8\text{s}, 2^4=16\text{s}$) before re-raising the error.