import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from documentor.engine.parser import ASTParser
from documentor.engine.vectorizer import VectorStore
from documentor.engine.mapper import DependencyMapper
from documentor.engine.generator import LLMGenerator
import litellm

# Load config globally for FastAPI server
from documentor.cli.main import load_config
load_config()

app = FastAPI(title="Documentor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    path: str
    model: str = "gpt-4o-mini"

class ChatRequest(BaseModel):
    query: str
    path: str
    model: str = "gpt-4o-mini"

@app.post("/api/generate")
async def api_generate(req: GenerateRequest):
    target_path = Path(req.path).resolve()
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=400, detail="Provided path is not a valid directory.")
        
    try:
        parser = ASTParser(str(target_path))
        parsed_data = parser.parse()
        
        vector_db_path = target_path / ".documentor" / "chroma"
        vector_store = VectorStore(str(vector_db_path))
        vector_store.chunk_and_store(parsed_data)
        
        mapper = DependencyMapper()
        generator = LLMGenerator(model=req.model, temperature=0.0)
        
        docs = generator.run_full_pipeline(parsed_data, vector_store, mapper)
        
        for doc_path, content in docs.items():
            full_path = target_path / doc_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
                
        return {"status": "success", "message": "Documentation generated successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    target_path = Path(req.path).resolve()
    vector_db_path = target_path / ".documentor" / "chroma"
    
    if not vector_db_path.exists():
        raise HTTPException(status_code=400, detail="Vector store not found. Generate documentation first.")
        
    try:
        vector_store = VectorStore(str(vector_db_path))
        results = vector_store.retrieve(req.query, n_results=5)
        
        context = ""
        if results and results.get('documents') and len(results['documents']) > 0:
            context = "\n---\n".join(results['documents'][0])
            
        prompt = f"""
You are an expert developer assistant. Answer the user's question based strictly on the following codebase snippets.

Context Snippets:
{context}

Question: {req.query}

CRITICAL RULE: DO NOT hallucinate. If the answer is not in the context, tell the user you don't know based on the parsed code.
"""
        response = litellm.completion(
            model=req.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/docs")
async def api_get_docs(path: str):
    target_path = Path(path).resolve()
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=400, detail="Provided path is not a valid directory.")
        
    docs = []
    docs_dir = target_path / "documentor_docs"
    if docs_dir.exists() and docs_dir.is_dir():
        for file in docs_dir.glob("**/*.md"):
            rel_path = file.relative_to(target_path)
            # Use forward slashes for URLs
            docs.append(str(rel_path).replace("\\", "/"))
            
    return {"docs": sorted(docs)}

@app.get("/api/docs/content")
async def api_get_doc_content(path: str, doc: str):
    target_path = Path(path).resolve()
    doc_path = (target_path / doc).resolve()
    
    # Security: Ensure doc_path is inside target_path
    if not str(doc_path).startswith(str(target_path)):
        raise HTTPException(status_code=403, detail="Access denied")
        
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
        
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    return {"content": content}

# Mount static files last so API routes take precedence
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
