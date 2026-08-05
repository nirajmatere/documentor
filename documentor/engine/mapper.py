from typing import Dict, Any
import re

class DependencyMapper:
    """
    Step 2b: Dependency Mapping.
    Determines how modules interact based on the parsed AST chunks.
    """
    def __init__(self):
        pass

    def map_dependencies(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds a graph showing how different modules and classes interact.
        It does this by cross-referencing extracted chunk names across files.
        """
        graph = {}
        
        # Step 1: Catalog all known entities (classes, functions)
        entities = {}
        for file_info in parsed_data.get("files", []):
            path = file_info["path"]
            graph[path] = {"depends_on": set(), "entities": []}
            for chunk in file_info.get("chunks", []):
                name = chunk.get("name")
                if name and name != "unknown":
                    entities[name] = path
                    graph[path]["entities"].append(name)
                    
        # Step 2: Scan code to find cross-references
        # Sort entity names by length descending so we match longest names first
        entity_names = sorted(entities.keys(), key=len, reverse=True)
        
        for file_info in parsed_data.get("files", []):
            path = file_info["path"]
            code = file_info.get("code", "")
            
            # Simple heuristic: if an entity name appears in the code, and it's not defined in this file,
            # it's a dependency.
            for name in entity_names:
                if len(name) < 4: # Ignore very short names to avoid false positives
                    continue
                if name in code and entities[name] != path:
                    # Use word boundaries to ensure we match whole words
                    if re.search(r'\b' + re.escape(name) + r'\b', code):
                        graph[path]["depends_on"].add(entities[name])
                        
        # Convert sets to lists for JSON serialization
        for path in graph:
            graph[path]["depends_on"] = list(graph[path]["depends_on"])
            
        return graph
