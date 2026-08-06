# Documentation: `documentor/engine/vectorizer.py`

## Overview

The `documentor/engine/vectorizer.py` module defines the `VectorStore` class, which serves as the vectorization layer (Step 2a) of the `documentor` engine. Its primary responsibility is to interface with **ChromaDB** to store parsed code chunks as vector embeddings and perform similarity-based retrieval against those embedded chunks.

---

## Dependencies

- **`chromadb`**: Provides vector database capabilities (`PersistentClient`, collection management, and vector search). Uses ChromaDB's default embedding function (SentenceTransformers).
- **`hashlib`**: Used to generate deterministic, unique MD5 hash IDs for code chunks.
- **`os`**: Handles local file system directory creation for persistent database storage.
- **`typing`**: Provides type annotations (`Dict`, `Any`, `List`).

---

## Class: `VectorStore`

The `VectorStore` class handles database initialization, chunk processing, embedding persistence (via upsert operations), and querying.

### Initialization

```python
def __init__(self, db_path: str = "./.documentor/chroma")
```

#### Parameters:
- `db_path` (*str*, optional): The filesystem path where ChromaDB persists its data. Defaults to `"./.documentor/chroma"`.

#### Initialization Logic:
1. Ensures the target directory (`db_path`) exists on the local file system using `os.makedirs(..., exist_ok=True)`.
2. Initializes a persistent ChromaDB client using `chromadb.PersistentClient(path=self.db_path)`.
3. Fetches or creates a ChromaDB collection named `"codebase"` (`self.collection`).

---

## Core Methods

### 1. `chunk_and_store`

```python
def chunk_and_store(self, parsed_data: Dict[str, Any]) -> None
```

Processes parsed AST chunks from input data, structures them into document payloads with unique IDs and metadata, and upserts them into the ChromaDB collection in batches.

#### Parameters:
- `parsed_data` (*Dict[str, Any]*): A dictionary containing parsed file and chunk information.

#### Expected `parsed_data` Structure:
```python
{
    "files": [
        {
            "path": "path/to/file.py",
            "chunks": [
                {
                    "content": "def my_func(): pass",
                    "name": "my_func",
                    "type": "function"
                }
            ]
        }
    ]
}
```

#### Process Flow:
1. **Iterate Files & Chunks**: Traverses each file dictionary inside `parsed_data.get("files", [])` and each chunk inside `file_info.get("chunks", [])`.
2. **Whitespace Check**: Ignores any chunk whose `content` is empty or contains only whitespace (`if not content.strip()`).
3. **ID Generation**: Constructs a unique string using the file path, chunk name, and chunk index (`f"{path}_{chunk.get('name')}_{i}"`), then computes its MD5 hex digest using `hashlib.md5(...).hexdigest()`.
4. **Metadata Construction**: Constructs a metadata dictionary for each valid chunk:
   - `path`: File path (`str`)
   - `type`: Chunk type (`str`, defaults to `"unknown"` if omitted)
   - `name`: Chunk name (`str`, defaults to `"unknown"` if omitted)
5. **Batching and Upserting**:
   - Chunks are collected into `documents`, `metadatas`, and `ids` lists.
   - If `documents` is non-empty, items are processed in fixed batch sizes of 100 (`batch_size = 100`).
   - Calls `self.collection.upsert(...)` for each batch.

---

### 2. `retrieve`

```python
def retrieve(self, query: str, n_results: int = 5) -> List[Any]
```

Searches the vector store for code chunks relevant to a natural language or text query.

#### Parameters:
- `query` (*str*): The search query text.
- `n_results` (*int*, optional): The maximum number of results to return. Defaults to `5`.

#### Process Flow:
1. **Empty Collection Guard**: Checks if `self.collection.count() == 0`. If the collection is empty, immediately returns an empty list `[]`.
2. **Query Execution**: Calls `self.collection.query(...)` with:
   - `query_texts`: `[query]`
   - `n_results`: `min(n_results, self.collection.count())` to prevent asking for more items than exist in the collection.
3. **Return Value**: Returns the raw result object (or list structure) produced by ChromaDB's `query` method.

---

## Summary of Key Rules & Behaviors

| Feature | Implementation Detail |
| :--- | :--- |
| **Storage Engine** | ChromaDB `PersistentClient` |
| **Collection Name** | `"codebase"` |
| **Default Storage Path** | `./.documentor/chroma` |
| **ID Strategy** | MD5 hash of `"{path}_{chunk_name}_{index}"` |
| **Batch Size** | 100 elements per upsert call |
| **Empty Content Handling** | Stripped and skipped if empty |
| **Empty Database Query Handling** | Guarded; returns `[]` if collection count is `0` |