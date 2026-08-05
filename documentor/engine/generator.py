from typing import Dict, Any, Set, Callable, Optional
import litellm
import json
import time

class LLMGenerator:
    """
    Step 3: Multi-Pass Generation.
    Uses LiteLLM to orchestrate multiple LLM passes for generating documentation.
    Users can bring their own API keys by setting standard environment variables.
    """
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.0):
        self.model = model
        self.temperature = temperature # Default to 0.0 for maximum determinism and accuracy

    def _call_llm_with_retry(self, prompt: str, max_retries: int = 5) -> str:
        """Wraps litellm.completion with exponential backoff for rate limits/high demand."""
        for attempt in range(max_retries):
            try:
                response = litellm.completion(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature
                )
                return response.choices[0].message.content
            except Exception as e:
                error_msg = str(e).lower()
                # Check for rate limits, high demand, or 429
                if "rate limit" in error_msg or "high demand" in error_msg or "429" in error_msg or "too many requests" in error_msg:
                    if attempt < max_retries - 1:
                        sleep_time = 2 ** attempt
                        time.sleep(sleep_time)
                        continue
                raise e

    def generate_architecture_overview(self, graph: Dict[str, Any]) -> str:
        """
        Pass A: Generates a high-level system overview, including Mermaid.js diagrams.
        """
        prompt = f"""
You are an expert software architect. Below is a dependency graph of a codebase.
It shows which files depend on which other files, and the key entities (classes/functions) within them.

Dependency Graph:
{json.dumps(graph, indent=2)}

Please write a comprehensive ARCHITECTURE.md file. 
CRITICAL RULE: DO NOT hallucinate features, dependencies, or components that are not explicitly present in the provided graph. Your primary objective is 100% accuracy.
It must include a Mermaid.js diagram illustrating the core interactions.
"""
        return self._call_llm_with_retry(prompt)

    def generate_module_guides(
        self, 
        vector_store: Any, 
        parsed_data: Dict[str, Any], 
        progress_callback: Optional[Callable[[str], None]] = None,
        write_callback: Optional[Callable[[str, str], None]] = None,
        skip_files: Optional[Set[str]] = None
    ) -> None:
        """
        Pass B: Iterates over the parsed data to write detailed guides for files.
        """
        if skip_files is None:
            skip_files = set()

        for file_info in parsed_data.get("files", []):
            path = file_info["path"]
            doc_path = f"docs/{path}.md"
            
            if doc_path in skip_files:
                if progress_callback: progress_callback(f"Skipping {path} (already generated)...")
                continue

            code = file_info.get("code", "")
            
            # To save tokens, skip very small files
            if len(code.strip()) < 50:
                continue
                
            prompt = f"""
You are an expert technical writer. Please write a detailed documentation guide for the following file.
File path: {path}

Code:
```
{code}
```

CRITICAL RULE: DO NOT hallucinate or invent features, methods, or logic that does not exist in the code snippet provided. Only explain what is strictly present in the code. Your primary objective is 100% accurate documentation.
Explain its purpose, key components, and how it works. Use Markdown format.
"""
            if progress_callback:
                progress_callback(f"Documenting {path}...")
                
            content = self._call_llm_with_retry(prompt)
            if write_callback:
                write_callback(doc_path, content)

    def generate_quickstart(self, vector_store: Any) -> str:
        """
        Pass C: Extracts env vars, setup instructions by querying the vector store.
        """
        search_results = vector_store.retrieve("environment variables install setup run command", n_results=5)
        
        context = ""
        if search_results and search_results.get('documents') and len(search_results['documents']) > 0:
            context = "\n---\n".join(search_results['documents'][0])
            
        prompt = f"""
You are an expert developer. Create a QUICKSTART.md file based strictly on the following code snippets extracted from the repository that relate to setup, installation, and environment variables.

Context Snippets:
{context}

CRITICAL RULE: DO NOT guess or hallucinate environment variables, dependencies, or commands. If the provided context does not explicitly mention them, DO NOT include them. Only provide accurate setup steps derived strictly from the text above. If there isn't enough information, state that clearly instead of guessing.
"""
        return self._call_llm_with_retry(prompt)

    def run_full_pipeline(
        self, 
        parsed_data: Dict[str, Any], 
        vector_store: Any, 
        mapper: Any, 
        progress_callback: Optional[Callable[[str], None]] = None,
        write_callback: Optional[Callable[[str, str], None]] = None,
        skip_files: Optional[Set[str]] = None
    ) -> None:
        """
        Orchestrates all passes and uses write_callback to save files immediately.
        """
        if skip_files is None:
            skip_files = set()

        if "ARCHITECTURE.md" not in skip_files:
            if progress_callback: progress_callback("Analyzing Architecture...")
            graph = mapper.map_dependencies(parsed_data)
            content = self.generate_architecture_overview(graph)
            if write_callback:
                write_callback("ARCHITECTURE.md", content)
        elif progress_callback:
            progress_callback("Skipping ARCHITECTURE.md (already generated)...")
            
        if "QUICKSTART.md" not in skip_files:
            if progress_callback: progress_callback("Writing Quickstart...")
            content = self.generate_quickstart(vector_store)
            if write_callback:
                write_callback("QUICKSTART.md", content)
        elif progress_callback:
            progress_callback("Skipping QUICKSTART.md (already generated)...")
            
        self.generate_module_guides(vector_store, parsed_data, progress_callback, write_callback, skip_files)
