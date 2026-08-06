# Technical Documentation: `documentor/engine/parser.py`

## Overview

The `documentor/engine/parser.py` module defines the `ASTParser` class, which serves as the core source code parser for the repository documentation generator. 

Its primary function is to traverse a repository directory, filter out ignored files and directories using `.gitignore`, `.docignore`, and predefined patterns, and construct an Abstract Syntax Tree (AST) representation of supported code files using `tree-sitter`. The parser extracts code structural elements (classes, functions, or full files as fallbacks) into structured chunks for downstream documentation tasks.

---

## Class: `ASTParser`

`ASTParser` is the central class responsible for repository traversal, language grammar loading, path exclusion, and AST-based chunk extraction.

### Initialization

```python
ASTParser(root_dir: str)
```

#### Parameters
- `root_dir` (`str`): The root directory path of the codebase to be analyzed.

#### Behavior
1. Converts `root_dir` into a `pathlib.Path` object stored at `self.root_dir`.
2. Loads exclusion rules via `_load_gitignore()` and assigns the result to `self.ignore_spec`.
3. Initializes an empty `self.languages` dictionary and populates it by invoking `_load_languages()`.

---

## Method Details

### Public Methods

#### `parse() -> Dict[str, Any]`
The main entry point for parsing the codebase.

* **Returns:** A dictionary containing a list of parsed file details under the `"files"` key.
* **Return Structure:**
  ```python
  {
      "files": [
          {
              "path": "relative/path/to/file.py",
              "language": ".py",
              "code": "...",  # Full file string content
              "chunks": [
                  {
                      "type": "class" | "function" | "file",
                      "name": "...",
                      "content": "..."
                  }
              ]
          }
      ]
  }
  ```

---

### Internal / Helper Methods

#### `_load_languages()`
Dynamically attempts to import `tree-sitter` language grammars for supported extensions. If a language bindings package is not installed, the `ImportError` is silently caught, and that file extension will not be parsed.

##### Extension to Grammar Mapping:
| Extension(s) | Tree-Sitter Language Grammar Module |
| :--- | :--- |
| `.py` | `tree_sitter_python` |
| `.js`, `.jsx` | `tree_sitter_javascript` |
| `.go` | `tree_sitter_go` |
| `.ts`, `.tsx` | `tree_sitter_typescript` (`language_typescript` / `language_tsx`) |
| `.java` | `tree_sitter_java` |
| `.rs` | `tree_sitter_rust` |
| `.r` | `tree_sitter_r` |
| `.cpp`, `.hpp`, `.cc` | `tree_sitter_cpp` |
| `.c`, `.h` | `tree_sitter_c` |
| `.cs` | `tree_sitter_c_sharp` |

---

#### `_load_gitignore() -> Optional[pathspec.PathSpec]`
Reads ignore patterns from `.gitignore` and `.docignore` files within `root_dir` (if present) and appends a list of built-in default exclusions.

##### Hardcoded Default Exclusions:
- **Hidden files/folders:** `.*`, `.*/**`
- **Environment files:** `*.env`, `.env*`
- **Logs:** `*.log`, `logs/`
- **JS / TS / Node builds:** `node_modules/`, `dist/`, `build/`, `out/`, `coverage/`
- **Python artifacts:** `__pycache__/`, `venv/`, `env/`, `*.egg-info/`, `*.pyc`, `htmlcov/`
- **Compiled binaries & target dirs:** `target/`, `vendor/`, `bin/`, `obj/`
- **OS files:** `.DS_Store`, `Thumbs.db`

Returns a `pathspec.PathSpec` compiled with the `"gitwildmatch"` rule set.

---

#### `_traverse() -> List[Path]`
Recursively traverses `self.root_dir` using `os.walk()`.

* Modifies directory list (`dirs[:]`) in-place during traversal to skip traversing ignored directories altogether.
* Filters individual files using `_is_ignored()`.
* Selects files whose extension (`suffix`) is present in `self.languages`.
* **Returns:** A list of `pathlib.Path` objects representing eligible code files.

---

#### `_is_ignored(path: Path) -> bool`
Evaluates whether a given path matches the compiled `self.ignore_spec` patterns.

* **Parameters:** `path` (`Path`) - Absolute or relative file path.
* **Returns:** `True` if the path relative to `self.root_dir` matches the ignore rules; `False` otherwise (or if `self.ignore_spec` is `None`).

---

#### `_parse_file(file_path: Path) -> Optional[Dict[str, Any]]`
Parses an individual file into structured data and chunks using Tree-sitter.

* **Workflow:**
  1. Verifies the file extension exists in `self.languages`.
  2. Opens and reads file as text (`utf-8`). Returns `None` if a `UnicodeDecodeError` occurs.
  3. Parses raw bytes using `tree_sitter.Parser`.
  4. Calls `_extract_chunks()` recursively starting at `tree.root_node`.
  5. Fallback behavior: If no structural chunks (classes or functions) are identified, creates a single chunk covering the entire file (`type`: `"file"`).
* **Returns:** A dictionary containing file details (`path`, `language`, `code`, `chunks`), or `None` if invalid.

---

#### `_extract_chunks(node, code_bytes: bytes, chunks: List[Dict[str, Any]])`
Traverses the Tree-sitter AST nodes recursively to locate specific code structures.

##### Extracted Types:
* **Class Chunk (`type: "class"`):** Triggered when `node.type` contains `"class_definition"`, `"class_declaration"`, or `"type_declaration"`.
* **Function Chunk (`type: "function"`):** Triggered when `node.type` contains `"function_definition"`, `"function_declaration"`, or `"method_definition"`.

If a node matches a class or function declaration, its content slice is extracted and added to `chunks`, and child nodes are not traversed further. Otherwise, the method recursively visits each child node (`node.children`).

---

#### `_get_node_name(node, code_bytes: bytes) -> str`
Extracts the name/identifier of a class or function node.

* Iterates over `node.children`.
* If a child has `type == "identifier"` or `type == "name"`, decodes its byte slice to a string using UTF-8 (replacing encoding errors).
* Returns `"unknown"` if no identifier or name child node is found.

---

## Data Flow Diagram

```
[ Root Directory ]
       │
       ▼
 _load_gitignore()  ──> Combine (.gitignore + .docignore + Default Rules) ──> PathSpec
       │
       ▼
   _traverse()      ──> Walk directory tree, prune ignored folders & match suffixes
       │
       ▼
  _parse_file()     ──> Read UTF-8 bytes ──> Tree-sitter AST Parsing
       │
       ▼
 _extract_chunks()  ──> Extract Classes ("class") & Functions ("function")
       │                 └─ (Fallback to full file chunk if none found)
       ▼
    parse()         ──> Aggregate and return final output dictionary
```