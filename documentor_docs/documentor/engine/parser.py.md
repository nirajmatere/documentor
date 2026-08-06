# Technical Documentation: `documentor/engine/parser.py`

## Overview

The `documentor/engine/parser.py` module defines the `ASTParser` class, which serves as the entry point for scanning and parsing code repositories into Abstract Syntax Trees (ASTs). 

It performs three primary duties:
1. **Repository Traversal & Filtering:** Walks the file tree while respecting `.gitignore`, `.docignore`, and default system exclusion patterns.
2. **Multi-Language Tree-Sitter Loading:** Dynamically loads Tree-Sitter language parsers for various programming languages if their packages are available.
3. **AST Structure & Chunk Extraction:** Parses source files into syntax trees and extracts structural code blocks (classes and functions) into standard dictionary schemas.

---

## Dependencies

* **`os` & `pathlib.Path`**: File system navigation and path manipulation.
* **`typing`**: Type hinting (`List`, `Dict`, `Any`, `Optional`).
* **`pathspec`**: Gitignore-style path pattern matching (`gitwildmatch`).
* **`tree_sitter`**: Syntactic parsing library.
* **Optional Language Bindings**:
  * `tree_sitter_python`
  * `tree_sitter_javascript`
  * `tree_sitter_go`
  * `tree_sitter_typescript`
  * `tree_sitter_java`
  * `tree_sitter_rust`
  * `tree_sitter_r`
  * `tree_sitter_cpp`
  * `tree_sitter_c`
  * `tree_sitter_c_sharp`

---

## Class: `ASTParser`

### Class Signature
```python
class ASTParser:
    def __init__(self, root_dir: str)
```

---

### Methods

#### `__init__(root_dir: str)`
Initializes an `ASTParser` instance for a given target repository path.
* **Arguments:**
  * `root_dir` (`str`): Absolute or relative file system path to the root directory of the repository.
* **Attributes Initialized:**
  * `self.root_dir` (`Path`): Resolved `Path` object representing the repository root.
  * `self.ignore_spec` (`pathspec.PathSpec`): Compiled `pathspec` matcher containing ignore rules.
  * `self.languages` (`Dict[str, tree_sitter.Language]`): Dictionary mapping file extension strings (e.g., `".py"`) to their corresponding `tree_sitter.Language` instances.

---

#### `_load_languages()`
Attempts to import language grammar bindings for tree-sitter dynamically. If an import fails (`ImportError`), the language is silently skipped.

**Supported File Extensions & Parsers:**

| Language | Module Import | Associated Extensions |
| :--- | :--- | :--- |
| Python | `tree_sitter_python` | `.py` |
| JavaScript | `tree_sitter_javascript` | `.js`, `.jsx` |
| Go | `tree_sitter_go` | `.go` |
| TypeScript | `tree_sitter_typescript` | `.ts`, `.tsx` |
| Java | `tree_sitter_java` | `.java` |
| Rust | `tree_sitter_rust` | `.rs` |
| R | `tree_sitter_r` | `.r` |
| C++ | `tree_sitter_cpp` | `.cpp`, `.hpp`, `.cc` |
| C | `tree_sitter_c` | `.c`, `.h` |
| C# | `tree_sitter_c_sharp` | `.cs` |

---

#### `_load_gitignore() -> Optional[pathspec.PathSpec]`
Reads ignore patterns from `.gitignore` and `.docignore` files present in `self.root_dir`, appends built-in default ignore patterns, and compiles them into a `PathSpec` object.

* **Hardcoded Default Exclusions:**
  * Hidden files & directories (`.*`, `.*/**`)
  * Environment & configuration files (`*.env`, `.env*`)
  * Logs (`*.log`, `logs/`)
  * JavaScript / Node build artifacts (`node_modules/`, `dist/`, `build/`, `out/`, `coverage/`)
  * Python virtual environments and caches (`__pycache__/`, `venv/`, `env/`, `*.egg-info/`, `*.pyc`, `htmlcov/`)
  * Compiled languages / project build outputs (`target/`, `vendor/`, `bin/`, `obj/`)
  * Operating system metadata (`.DS_Store`, `Thumbs.db`)

* **Returns:** `pathspec.PathSpec` configured with the `"gitwildmatch"` pattern syntax.

---

#### `parse() -> Dict[str, Any]`
Main entry point for parsing the codebase.

* **Returns:** A dictionary containing list of parsed file payloads.
  ```python
  {
      "files": [
          # List of file_info objects returned by _parse_file
      ]
  }
  ```

---

#### `_traverse() -> List[Path]`
Walks the repository directory tree starting at `self.root_dir` using `os.walk`.

* Modifies `dirs` in-place to prevent walking into ignored directories early.
* Checks each file against `_is_ignored()`.
* Filters out files whose extension is not mapped in `self.languages`.
* **Returns:** A list of valid `Path` objects to be parsed.

---

#### `_is_ignored(path: Path) -> bool`
Evaluates whether a given path matches the loaded ignore specifications.

* **Arguments:**
  * `path` (`Path`): File or directory path to test.
* **Returns:** `True` if the path matches an ignore pattern, `False` otherwise. (Returns `False` if `self.ignore_spec` is not set).

---

#### `_parse_file(file_path: Path) -> Optional[Dict[str, Any]]`
Reads and parses an individual source code file using Tree-Sitter.

* **Arguments:**
  * `file_path` (`Path`): Path to the source file.
* **Returns:**
  * `None` if the extension is unsupported or if a `UnicodeDecodeError` occurs when reading the file.
  * A dictionary structured as follows if parsing succeeds:
    ```python
    {
        "path": "relative/path/to/file.ext",  # Path relative to root_dir
        "language": ".ext",                    # File extension
        "code": "...",                         # Entire source code text
        "chunks": [...]                        # List of extracted class/function chunks
    }
    ```
* **Fallback Logic:** If no distinct class or function chunks are extracted, `_parse_file` populates `chunks` with a single fallback item representing the entire file:
  ```python
  {
      "type": "file",
      "name": "<filename.ext>",
      "content": "..."
  }
  ```

---

#### `_extract_chunks(node, code_bytes: bytes, chunks: List[Dict[str, Any]])`
Recursively traverses a Tree-Sitter AST node to identify high-level code structures (classes and functions) and append them to the `chunks` list.

* **Detected Node Types:**
  * **Class:** Matches node types containing `"class_definition"`, `"class_declaration"`, or `"type_declaration"`.
    * Output schema:
      ```python
      {
          "type": "class",
          "name": "<name>",
          "content": "<source_code_substring>"
      }
      ```
  * **Function/Method:** Matches node types containing `"function_definition"`, `"function_declaration"`, or `"method_definition"`.
    * Output schema:
      ```python
      {
          "type": "function",
          "name": "<name>",
          "content": "<source_code_substring>"
      }
      ```
* **Recursive Step:** If the current node type does not match class or function definitions, the function recurses into all child nodes (`node.children`).

---

#### `_get_node_name(node, code_bytes: bytes) -> str`
Helper method that scans a node's immediate children to retrieve its identifier/name string.

* Checks if a child node has a type equal to `"identifier"` or `"name"`.
* Decodes the node's byte range (`child.start_byte:child.end_byte`) to string using UTF-8 (with `replace` error handling).
* **Returns:** The identifier string if found, or `"unknown"` if no child matching `"identifier"` or `"name"` exists.

---

## Data Structures Summary

### Output Schema of `ASTParser.parse()`

```json
{
  "files": [
    {
      "path": "src/example.py",
      "language": ".py",
      "code": "class Example:\n    def run(self):\n        pass\n",
      "chunks": [
        {
          "type": "class",
          "name": "Example",
          "content": "class Example:\n    def run(self):\n        pass\n"
        }
      ]
    }
  ]
}
```