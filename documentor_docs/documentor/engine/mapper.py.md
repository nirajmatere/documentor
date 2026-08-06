# Technical Documentation: `documentor/engine/mapper.py`

## Overview

The `documentor/engine/mapper.py` module defines the `DependencyMapper` class. Its primary role is to perform dependency mapping (designated as Step 2b in the pipeline) by mapping relationships and cross-references between different files based on parsed AST chunks and source code content. 

It processes parsed file data to build a dependency graph that details which entities (classes, functions) are defined in each file and which external files a given file depends on.

---

## Class: `DependencyMapper`

### Description
`DependencyMapper` determines how modules and files interact. It catalogs extracted entities across all parsed files and scans the source code of each file to locate cross-references to entities defined in other files.

---

## Methods

### `__init__(self)`
Initializes a new instance of the `DependencyMapper` class. This method currently takes no parameters (other than `self`) and performs no specific setup operations (`pass`).

---

### `map_dependencies(parsed_data: Dict[str, Any]) -> Dict[str, Any]`

Builds and returns a graph mapping file paths to their exported entities and cross-file dependencies.

#### Parameters
* **`parsed_data`** (`Dict[str, Any]`): A dictionary containing parsed AST data. It is expected to have a key `"files"`, which holds a list of dictionaries containing file details.

  **Expected Input Structure:**
  ```python
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

#### Return Value
* **`Dict[str, Any]`**: A dictionary representing the dependency graph where each key is a file path and the value is a dictionary containing defined entities and target dependency file paths.

  **Output Structure:**
  ```python
  {
      "path/to/file.py": {
          "entities": ["EntityName1", "EntityName2"],
          "depends_on": ["path/to/dependency_file.py"]
      }
  }
  ```

---

## Detailed Algorithm Workflow

The `map_dependencies` method executes in three sequential steps:

### Step 1: Entity Cataloging
1. Initializes an empty `graph` dictionary and an `entities` mapping dictionary (`entity_name -> file_path`).
2. Iterates through every file object under `parsed_data["files"]`.
3. For each file path:
   * Initializes `graph[path]` with an empty set for `"depends_on"` and an empty list for `"entities"`.
   * Loops through all code `chunks` in the file.
   * Extracts the `name` attribute of each chunk.
   * If `name` exists and is not equal to `"unknown"`:
     * Stores the mapping `entities[name] = path`.
     * Appends `name` to `graph[path]["entities"]`.

### Step 2: Cross-Reference Scanning
1. Sorts all cataloged entity names by character length in **descending order** (`key=len, reverse=True`). Sorting ensures longer names are matched before shorter substrings.
2. Iterates through each file entry in `parsed_data["files"]`:
   * Retrieves the source `code` string for the file (defaults to an empty string if missing).
   * Iterates through the sorted `entity_names`:
     * **Filter:** Ignores entity names with a length of less than 4 characters (`len(name) < 4`) to minimize false positives.
     * **Check Ownership:** Checks if `name` is present in `code` and verifies that the entity was **not** defined within the current file (`entities[name] != path`).
     * **Regex Matching:** Uses a regular expression search with word boundaries (`\b`) around the escaped entity name (`re.search(r'\b' + re.escape(name) + r'\b', code)`) to confirm a whole-word match in the source code.
     * **Record Dependency:** If matched, adds the entity's source file path (`entities[name]`) into the current file's `"depends_on"` set.

### Step 3: Serialization Normalization
1. Iterates over all file entries in `graph`.
2. Converts the `"depends_on"` values from Python `set` objects to `list` objects to ensure compatibility with JSON serialization.
3. Returns the populated `graph` dictionary.

---

## Key Rules & Heuristics

* **Exclusion of Unknown Entities:** Chunks named `"unknown"` are ignored during the cataloging step.
* **Minimum Length Limit:** Entities with names shorter than 4 characters (`len(name) < 4`) are skipped during the reference scan to prevent false positives from short identifiers or keywords.
* **Word Boundary Matching:** Regex search employs `\b` word boundaries to ensure partial string matches within longer identifiers do not count as cross-references.
* **Self-Dependency Exclusion:** Entities defined within the same file being scanned are excluded from adding a dependency onto the file itself.