import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pathspec
import tree_sitter

class ASTParser:
    """
    Step 1: AST Parsing & Tree Generation.
    Traverses the repository, ignores files based on .gitignore, and uses tree-sitter
    to map out code structures across multiple languages.
    """
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.ignore_spec = self._load_gitignore()
        self.languages = {}
        self._load_languages()

    def _load_languages(self):
        try:
            import tree_sitter_python
            self.languages[".py"] = tree_sitter.Language(tree_sitter_python.language())
        except ImportError: pass
        
        try:
            import tree_sitter_javascript
            self.languages[".js"] = tree_sitter.Language(tree_sitter_javascript.language())
            self.languages[".jsx"] = tree_sitter.Language(tree_sitter_javascript.language())
        except ImportError: pass

        try:
            import tree_sitter_go
            self.languages[".go"] = tree_sitter.Language(tree_sitter_go.language())
        except ImportError: pass
        
        try:
            import tree_sitter_typescript
            self.languages[".ts"] = tree_sitter.Language(tree_sitter_typescript.language_typescript())
            self.languages[".tsx"] = tree_sitter.Language(tree_sitter_typescript.language_tsx())
        except ImportError: pass

        try:
            import tree_sitter_java
            self.languages[".java"] = tree_sitter.Language(tree_sitter_java.language())
        except ImportError: pass

        try:
            import tree_sitter_rust
            self.languages[".rs"] = tree_sitter.Language(tree_sitter_rust.language())
        except ImportError: pass

        try:
            import tree_sitter_r
            self.languages[".r"] = tree_sitter.Language(tree_sitter_r.language())
        except ImportError: pass

        try:
            import tree_sitter_cpp
            self.languages[".cpp"] = tree_sitter.Language(tree_sitter_cpp.language())
            self.languages[".hpp"] = tree_sitter.Language(tree_sitter_cpp.language())
            self.languages[".cc"] = tree_sitter.Language(tree_sitter_cpp.language())
        except ImportError: pass

        try:
            import tree_sitter_c
            self.languages[".c"] = tree_sitter.Language(tree_sitter_c.language())
            self.languages[".h"] = tree_sitter.Language(tree_sitter_c.language())
        except ImportError: pass

        try:
            import tree_sitter_c_sharp
            self.languages[".cs"] = tree_sitter.Language(tree_sitter_c_sharp.language())
        except ImportError: pass

    def _load_gitignore(self) -> Optional[pathspec.PathSpec]:
        gitignore_path = self.root_dir / ".gitignore"
        lines = []
        if gitignore_path.exists():
            with open(gitignore_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
        docignore_path = self.root_dir / ".docignore"
        if docignore_path.exists():
            with open(docignore_path, "r", encoding="utf-8") as f:
                lines.extend(f.readlines())
        
        # Comprehensive default exclusions to save API tokens and time
        lines.extend([
            # Hidden files and directories (covers .env, .next, .cache, .vscode, .git, .documentor, etc.)
            ".*", 
            ".*/**", 
            # Environment variables
            "*.env",
            ".env*",
            # Logs
            "*.log",
            "logs/",
            # JavaScript / TypeScript / Node
            "node_modules/",
            "dist/",
            "build/",
            "out/",
            "coverage/",
            # Python
            "__pycache__/",
            "venv/",
            "env/",
            "*.egg-info/",
            "*.pyc",
            "htmlcov/",
            # Rust / Go / Java / C# / C++
            "target/",
            "vendor/",
            "bin/",
            "obj/",
            # OS Generated
            ".DS_Store",
            "Thumbs.db"
        ])
        return pathspec.PathSpec.from_lines("gitwildmatch", lines)

    def parse(self) -> Dict[str, Any]:
        """
        Main entrypoint for parsing the codebase.
        Returns a structured representation of the codebase.
        """
        result = {"files": []}
        
        for file_path in self._traverse():
            file_info = self._parse_file(file_path)
            if file_info:
                result["files"].append(file_info)
                
        return result

    def _traverse(self) -> List[Path]:
        files_to_parse = []
        for root, dirs, files in os.walk(self.root_dir):
            root_path = Path(root)
            
            # Filter dirs in-place to avoid walking ignored directories
            dirs[:] = [d for d in dirs if not self._is_ignored(root_path / d)]
            
            for file in files:
                file_path = root_path / file
                if not self._is_ignored(file_path) and file_path.suffix in self.languages:
                    files_to_parse.append(file_path)
        return files_to_parse

    def _is_ignored(self, path: Path) -> bool:
        if not self.ignore_spec:
            return False
        rel_path = path.relative_to(self.root_dir)
        return self.ignore_spec.match_file(str(rel_path))

    def _parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        ext = file_path.suffix
        if ext not in self.languages:
            return None
            
        parser = tree_sitter.Parser(self.languages[ext])
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
        except UnicodeDecodeError:
            return None
            
        tree = parser.parse(bytes(code, "utf8"))
        
        chunks = []
        self._extract_chunks(tree.root_node, code, chunks)
        
        # If no specific chunks found, store the whole file as one chunk
        if not chunks:
            chunks.append({
                "type": "file",
                "name": file_path.name,
                "content": code
            })
            
        return {
            "path": str(file_path.relative_to(self.root_dir)),
            "language": ext,
            "code": code,
            "chunks": chunks
        }

    def _extract_chunks(self, node, code: str, chunks: List[Dict[str, Any]]):
        node_type = node.type
        
        if "class_definition" in node_type or "class_declaration" in node_type or "type_declaration" in node_type:
            chunks.append({
                "type": "class",
                "name": self._get_node_name(node, code),
                "content": code[node.start_byte:node.end_byte]
            })
        elif "function_definition" in node_type or "function_declaration" in node_type or "method_definition" in node_type:
            chunks.append({
                "type": "function",
                "name": self._get_node_name(node, code),
                "content": code[node.start_byte:node.end_byte]
            })
        else:
            for child in node.children:
                self._extract_chunks(child, code, chunks)
                
    def _get_node_name(self, node, code: str) -> str:
        for child in node.children:
            if child.type == "identifier" or child.type == "name":
                return code[child.start_byte:child.end_byte]
        return "unknown"
