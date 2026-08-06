# Module Documentation: `documentor/engine/vectorizer.py`

## Overview

The `documentor/engine/vectorizer.py` module defines the `VectorStore` class, which handles the vectorization, persistent storage, and retrieval of code chunks using [ChromaDB](https://www.trychroma.com/). 

Its primary role is to take parsed AST code chunks, generate deterministic MD5 identifier hashes, attach metadata, batch-upsert the data into a persistent vector database collection named `"codebase"`, and provide a query interface for similarity searches.

---

## Class: `VectorStore`

`VectorStore` serves as the interface between parsed code structure dictionaries and ChromaDB's persistent store.

### Initialization

```python
VectorStore(db_path: str = "./.documentor/chroma")
```

#### Parameters
* **`db_path`** (`str`, optional): The local file system directory path where ChromaDB will persist its data. Defaults to `"./.documentor/chroma"`.

#### Initialization Steps
1. Ensures the target directory `db_path` exists on disk via `os.makedirs(self.db_path, exist_ok=True)`.
2. Instantiates a persistent ChromaDB client via `chromadb.PersistentClient(path=self.db_path)`.
3. Gets or creates the ChromaDB collection named `"codebase"` using default embedding settings (SentenceTransformers).

---

## Key Methods

### 1. `chunk_and_store`

```python
chunk_and_store(parsed_data: Dict[str, Any]) -> None
```

Processes structured AST dictionary data, formats code chunks into documents with associated metadata and unique IDs, and upserts them to the `"codebase"` collection in batches.

#### Parameters
* **`parsed_data`** (`Dict[str, Any]`): A dictionary containing parsed file and chunk information.

#### Input Data Requirements
`parsed_data` expects the following structure:
```python
{
    "files": [
        {
            "path": "path/to/file.py",
            "chunks": [
                {
                    "content": "def example(): pass",
                    "name": "example",
                    "type": "function"
                }
            ]
        }
    ]
}
```

#### Processing Logic
1. Iterates through the list of dictionaries under the `"files"` key in `parsed_data`.
2. For each file, extracts the file `path` and iterates over its `chunks`.
3. **Validation**: Skips any chunk whose `"content"` field is empty or contains only whitespace.
4. **ID Generation**: Computes an MD5 hash using UTF-8 encoding based on the string:
   ```
   "{path}_{chunk_name}_{chunk_index}"
   ```
5. **Metadata Construction**: Constructs a dictionary for each valid chunk:
   * `"path"`: The file path (`str`).
   * `"type"`: The chunk type (defaults to `"unknown"` if omitted).
   * `"name"`: The chunk name (defaults to `"unknown"` if omitted).
6. **Batch Upsert**: If valid documents exist, upserts them into `self.collection` in fixed batch sizes of 100 documents (`batch_size = 100`) to avoid operational limits.

---

### 2. `retrieve`

```python
retrieve(query: str, n_results: int = 5) -> List[Any]
```

Performs a text similarity search against the stored vector embeddings in the `"codebase"` collection.

#### Parameters
* **`query`** (`str`): The natural language or code string to search against the stored embeddings.
* **`n_results`** (`int`, optional): The maximum number of relevant results to return. Defaults to `5`.

#### Processing Logic
1. Checks the total document count in the collection using `self.collection.count()`.
2. If `self.collection.count() == 0`, returns an empty list `[]`.
3. Runs `self.collection.query(...)` with:
   * `query_texts=[query]`
   * `n_results=min(n_results, self.collection.count())` (ensures `n_results` does not exceed the count of stored items).
4. Returns the raw query results returned by ChromaDB.

---

## Dependency Requirements

* `chromadb`: Vector database framework for persistence and query functionality.
* `hashlib`: Standard Python module used for generating MD5 document IDs.
* `os`: Standard Python module used for directory creation (`os.makedirs`).
* `typing`: Standard Python module for type hints (`Dict`, `Any`, `List`).