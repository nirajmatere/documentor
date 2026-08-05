from typing import Dict, Any, List
import chromadb
import hashlib
import os

class VectorStore:
    """
    Step 2a: Vectorization.
    Connects to ChromaDB, chunks parsed code, and stores it as vector embeddings.
    """
    def __init__(self, db_path: str = "./.documentor/chroma"):
        self.db_path = db_path
        os.makedirs(self.db_path, exist_ok=True)
        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # We use the default embedding function (SentenceTransformers) built into ChromaDB
        self.collection = self.client.get_or_create_collection(name="codebase")

    def chunk_and_store(self, parsed_data: Dict[str, Any]):
        """
        Takes the parsed AST chunks and stores them in ChromaDB.
        """
        documents = []
        metadatas = []
        ids = []
        
        for file_info in parsed_data.get("files", []):
            path = file_info["path"]
            
            for i, chunk in enumerate(file_info.get("chunks", [])):
                content = chunk.get("content", "")
                if not content.strip():
                    continue
                    
                # Generate a unique ID based on path, name, and index
                doc_id = hashlib.md5(f"{path}_{chunk.get('name')}_{i}".encode('utf-8')).hexdigest()
                
                documents.append(content)
                metadatas.append({
                    "path": path,
                    "type": chunk.get("type", "unknown"),
                    "name": chunk.get("name", "unknown")
                })
                ids.append(doc_id)
                
        if documents:
            # Upsert into ChromaDB in batches of 100 to avoid limits
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                self.collection.upsert(
                    documents=documents[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size],
                    ids=ids[i:i+batch_size]
                )

    def retrieve(self, query: str, n_results: int = 5) -> List[Any]:
        """
        Retrieves relevant chunks based on a query.
        """
        if self.collection.count() == 0:
            return []
            
        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count())
        )
        
        return results
