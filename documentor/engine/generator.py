from typing import Dict, Any
import litellm
import json

class LLMGenerator:
    """
    Step 3: Multi-Pass Generation.
    Uses LiteLLM to orchestrate multiple LLM passes for generating documentation.
    Users can bring their own API keys by setting standard environment variables.
    """
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.0):
        self.model = model
        self.temperature = temperature # Default to 0.0 for maximum determinism and accuracy

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
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        return response.choices[0].message.content

    def generate_module_guides(self, vector_store: Any, parsed_data: Dict[str, Any], progress_callback=None) -> Dict[str, str]:
        """
        Pass B: Iterates over the parsed data to write detailed guides for files.
        """
        guides = {}
        for file_info in parsed_data.get("files", []):
            path = file_info["path"]
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
                
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature
            )
            guides[path] = response.choices[0].message.content
            
        return guides

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
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        return response.choices[0].message.content

    def run_full_pipeline(self, parsed_data: Dict[str, Any], vector_store: Any, mapper: Any, progress_callback=None) -> Dict[str, str]:
        """
        Orchestrates all passes. Returns a dictionary of filename -> markdown content.
        """
        results = {}
        
        if progress_callback: progress_callback("Analyzing Architecture...")
        graph = mapper.map_dependencies(parsed_data)
        results["ARCHITECTURE.md"] = self.generate_architecture_overview(graph)
        
        if progress_callback: progress_callback("Writing Quickstart...")
        results["QUICKSTART.md"] = self.generate_quickstart(vector_store)
        
        guides = self.generate_module_guides(vector_store, parsed_data, progress_callback)
        for path, content in guides.items():
            results[f"docs/{path}.md"] = content
            
        return results
