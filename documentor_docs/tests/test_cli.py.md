# Documentation Guide: `tests/test_cli.py`

## Overview

The `tests/test_cli.py` file contains the unit test suite for the Command Line Interface (CLI) of the `documentor` application. It uses `pytest` alongside Typer's `CliRunner` to test CLI command execution, options, help text, configuration generation, and error handling for missing inputs or resources.

---

## Dependencies and Global Objects

### Dependencies
* **`pytest`**: The test framework used for defining and executing test cases and fixture injection (`monkeypatch`, `tmp_path`).
* **`typer.testing.CliRunner`**: Utility provided by Typer to simulate command-line execution and capture CLI output, exit codes, and standard inputs.
* **`importlib.metadata`**: Python standard library module mocked during tests to return deterministic package metadata (such as version).
* **`documentor.cli.main.app`**: The primary Typer application instance under test.

### Global Objects
* **`runner`**: An instance of `CliRunner()` instantiated at module scope to execute commands against `app`.

```python
runner = CliRunner()
```

---

## Test Functions Reference

### 1. `test_version(monkeypatch)`

#### Purpose
Verifies that invoking the CLI with the `--version` option outputs the expected application version and exits successfully.

#### Implementation Details
* **Fixtures Used**: `monkeypatch`
* **Mocking**: Overrides `importlib.metadata.version` to return `"0.1.22"`.
* **Invocation**: `runner.invoke(app, ["--version"])`
* **Assertions**:
  * `result.exit_code` equals `0`.
  * `result.stdout` contains `"Documentor version: 0.1.22"`.

---

### 2. `test_help()`

#### Purpose
Verifies that invoking the CLI with the `--help` option displays the main application description and lists the core subcommands.

#### Implementation Details
* **Fixtures Used**: None
* **Invocation**: `runner.invoke(app, ["--help"])`
* **Assertions**:
  * `result.exit_code` equals `0`.
  * `result.stdout` contains either `"Documentor: Enterprise-grade AI documentation suite"` or `"Documentor: A powerful AI documentation suite"`.
  * `result.stdout` contains references to the following subcommands:
    * `generate`
    * `chat`
    * `serve`
    * `configure`

---

### 3. `test_configure(monkeypatch, tmp_path)`

#### Purpose
Tests the `configure` subcommand by mocking target configuration file paths and simulating user input (pressing Enter through prompts).

#### Implementation Details
* **Fixtures Used**: `monkeypatch`, `tmp_path`
* **Mocking**:
  * Sets `documentor.cli.main.CONFIG_FILE` to `tmp_path / "config.env"`.
  * Sets `documentor.cli.main.CONFIG_DIR` to `tmp_path`.
* **Invocation**: `runner.invoke(app, ["configure"], input="\n\n\n\n")` (Simulates accepting default options across 4 interactive prompts).
* **Assertions**:
  * `result.exit_code` equals `0`.
  * `result.stdout` contains `"Configuration saved successfully"`.
  * The file at `tmp_path / "config.env"` exists on the filesystem.

---

### 4. `test_generate_missing_dir()`

#### Purpose
Verifies error handling when running the `generate` subcommand with a target directory path that does not exist.

#### Implementation Details
* **Fixtures Used**: None
* **Invocation**: `runner.invoke(app, ["generate", "/path/that/does/not/exist"])`
* **Assertions**:
  * `result.exit_code` equals `1`.
  * `result.stdout` contains `"Error: Directory '/path/that/does/not/exist' does not exist"`.

---

### 5. `test_chat_no_vector_db(tmp_path)`

#### Purpose
Verifies error handling when executing the `chat` subcommand on a path where no vector database/store is present.

#### Implementation Details
* **Fixtures Used**: `tmp_path`
* **Invocation**: `runner.invoke(app, ["chat", "How does this work?", "--path", str(tmp_path)])`
* **Assertions**:
  * `result.exit_code` equals `1`.
  * `result.stdout` contains `"Error: Vector store not found"`.

---

## Summary of Tested CLI Behaviors

| Subcommand / Option | Tested Scenario | Expected Exit Code | Key Output Checked |
| :--- | :--- | :--- | :--- |
| `--version` | Query application version | `0` | `"Documentor version: 0.1.22"` |
| `--help` | Display help page and available subcommands | `0` | Header text + listing of `generate`, `chat`, `serve`, `configure` |
| `configure` | Interactive configuration generation with default inputs | `0` | `"Configuration saved successfully"` & creation of `config.env` |
| `generate` | Provide non-existent directory path | `1` | `"Error: Directory '...' does not exist"` |
| `chat` | Execute prompt against directory lacking vector store | `1` | `"Error: Vector store not found"` |