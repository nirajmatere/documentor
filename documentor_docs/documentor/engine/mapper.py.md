# Module Documentation: `documentor/engine/mapper.py`

## Overview

The `documentor/engine/mapper.py` module defines the `DependencyMapper` class, which performs dependency mapping across a set of parsed source code files. It analyzes extracted Code/AST chunk names across files to build a dependency graph that illustrates how different files/modules interact.

---

## Class: `DependencyMapper`

### Description
The `DependencyMapper` class processes parsed file data, catalogs defined entities (classes and functions), and scans source code to determine cross-file dependencies based on entity name references.

---

### Methods

#### `__init__()`
```python
def __init__(self):
    pass
```
* **Purpose**: Initializes the `DependencyMapper` instance.

---

#### `map_dependencies()`
```python
def map_dependencies(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]
```

* **Purpose**: Generates a dependency graph mapping files to the entities they define and the files they depend on.
* **Parameters**:
  * `parsed_data` (`Dict[str, Any]`): A dictionary containing parsed file information. Expected to contain a `"files"` key containing a list of file dictionaries.
* **Returns**:
  * `Dict[str, Any]`: A dictionary representing the dependency graph, keyed by file path.

---

## Processing Steps in `map_dependencies`

The mapping process operates in three primary steps:

### Step 1: Catalog Entities
1. Iterates over all file dictionaries under `parsed_data["files"]`.
2. Initializes a graph entry for each file path:
   ```python
   graph[path] = {"depends_on": set(), "entities": []}
   ```
3. Iterates over each chunk in `file_info["chunks"]`.
4. If a chunk's `name` exists and is not `"unknown"`:
   * The entity is mapped to its defining file path (`entities[name] = path`).
   * The entity name is appended to `graph[path]["entities"]`.

### Step 2: Scan Code for Cross-References
1. Collects all entity names and sorts them by length in descending order (`sorted(..., key=len, reverse=True)`). This ensures longer entity names are evaluated first.
2. Iterates over each file in `parsed_data["files"]` and evaluates its source code string (`file_info["code"]`).
3. For each entity in the sorted entity list:
   * **Length Filter**: Ignores entities with a name length under 4 characters (`len(name) < 4`) to prevent false positives.
   * **Cross-File Check**: Skips matching if the entity was defined in the current file being scanned (`entities[name] != path`).
   * **Regex Word Boundary Match**: Uses `re.search` with `r'\b' + re.escape(name) + r'\b'` to confirm the entity appears as a distinct word in the file's code.
   * If a match is found, the path of the file defining the entity (`entities[name]`) is added to the current file's `depends_on` set.

### Step 3: Format Output
Converts all `depends_on` values from Python `set` objects to `list` objects to ensure compatibility with JSON serialization.

---

## Data Schema Reference

### Expected Input Schema (`parsed_data`)
```json
{
  "files": [
    {
      "path": "path/to/file.py",
      "code": "source code string...",
      "chunks": [
        {
          "name": "EntityName"
        }
      ]
    }
  ]
}
```

### Output Schema (`graph`)
```json
{
  "path/to/file.py": {
    "depends_on": [
      "path/to/dependency_file.py"
    ],
    "entities": [
      "EntityName"
    ]
  }
}
```