import typer
import os
import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv, set_key

from documentor.engine.parser import ASTParser
from documentor.engine.vectorizer import VectorStore
from documentor.engine.mapper import DependencyMapper
from documentor.engine.generator import LLMGenerator
import litellm

app = typer.Typer(help="Documentor: Enterprise-grade AI documentation suite")
CONFIG_DIR = Path.home() / ".documentor"
CONFIG_FILE = CONFIG_DIR / "config.env"

def load_config():
    if CONFIG_FILE.exists():
        load_dotenv(CONFIG_FILE)

def handle_litellm_error(e: Exception):
    """Helper to catch litellm specific errors and print clean messages."""
    error_msg = str(e).lower()
    if "api key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
        typer.secho("Error: Invalid or missing API key.", fg=typer.colors.RED)
        typer.secho("Action Required: Run 'documentor configure' to set up a valid API key.", fg=typer.colors.YELLOW)
    elif "context length" in error_msg or "maximum context" in error_msg:
        typer.secho("Error: The codebase is too large for the selected model's context window.", fg=typer.colors.RED)
        typer.secho("Action Required: Use a model with a larger context window (e.g., gemini-1.5-pro or gpt-4o).", fg=typer.colors.YELLOW)
    elif "rate limit" in error_msg:
        typer.secho("Error: You have hit the rate limit for your LLM provider.", fg=typer.colors.RED)
        typer.secho("Action Required: Wait a moment before trying again, or upgrade your LLM API tier.", fg=typer.colors.YELLOW)
    else:
        typer.secho(f"An unexpected LLM error occurred: {str(e)}", fg=typer.colors.RED)
    raise typer.Exit(1)

@app.command()
def configure():
    """
    Configure API keys for the LLM providers.
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE.exists():
            CONFIG_FILE.touch()
            
        typer.echo("Configure your Bring-Your-Own-LLM (BYO-LLM) settings.")
        provider = typer.prompt("Enter the environment variable name (e.g., OPENAI_API_KEY, GEMINI_API_KEY)")
        
        # Accept any format without validation
        api_key = typer.prompt(f"Enter the value for {provider}", hide_input=True)
        
        set_key(str(CONFIG_FILE), provider, api_key)
        typer.echo(f"Saved {provider} successfully to {CONFIG_FILE}")
    except Exception as e:
        typer.secho(f"Error saving configuration: {str(e)}", fg=typer.colors.RED)
        typer.secho("Action Required: Ensure you have write permissions to ~/.documentor/config.env", fg=typer.colors.YELLOW)
        raise typer.Exit(1)

@app.command()
def generate(path: str = typer.Argument(..., help="Path to the repository to document"),
             model: str = typer.Option("gpt-4o-mini", help="LiteLLM compatible model name")):
    """
    Triggers the 4-step Core Engine to generate accurate documentation for the given path.
    """
    try:
        load_config()
        target_path = Path(path).resolve()
        
        if not target_path.exists() or not target_path.is_dir():
            typer.secho(f"Error: Directory '{target_path}' does not exist.", fg=typer.colors.RED)
            typer.secho("Action Required: Provide a valid directory path.", fg=typer.colors.YELLOW)
            raise typer.Exit(1)
            
        typer.echo(f"Step 1: Parsing {target_path} ...")
        parser = ASTParser(str(target_path))
        parsed_data = parser.parse()
        
        typer.echo(f"Step 2a: Vectorizing code ...")
        vector_db_path = target_path / ".documentor" / "chroma"
        vector_store = VectorStore(str(vector_db_path))
        vector_store.chunk_and_store(parsed_data)
        
        typer.echo(f"Step 2b: Mapping dependencies ...")
        mapper = DependencyMapper()
        
        typer.echo(f"Step 3: Generating documentation (Model: {model}) ...")
        generator = LLMGenerator(model=model, temperature=0.0)
        
        docs = generator.run_full_pipeline(parsed_data, vector_store, mapper)
        
        typer.echo("Step 4: Writing files ...")
        for doc_path, content in docs.items():
            full_path = target_path / doc_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            typer.echo(f"  - Created {doc_path}")
            
        typer.secho("Documentation generation complete!", fg=typer.colors.GREEN)
        
    except litellm.exceptions.APIError as e:
        handle_litellm_error(e)
    except Exception as e:
        typer.secho(f"Error: An unexpected issue occurred during generation.", fg=typer.colors.RED)
        typer.secho(f"Details: {str(e)}", fg=typer.colors.RED)
        typer.secho("Action Required: Verify the provided path is a valid code repository and try again.", fg=typer.colors.YELLOW)
        raise typer.Exit(1)

@app.command()
def chat(question: str = typer.Argument(..., help="Question to ask about the codebase"),
         path: str = typer.Option(".", help="Path to the repository"),
         model: str = typer.Option("gpt-4o-mini", help="LiteLLM compatible model name")):
    """
    Retrieval-Augmented Generation (RAG) query against the codebase.
    """
    try:
        load_config()
        target_path = Path(path).resolve()
        vector_db_path = target_path / ".documentor" / "chroma"
        
        if not vector_db_path.exists():
            typer.secho("Error: Vector store not found.", fg=typer.colors.RED)
            typer.secho("Action Required: Please run 'documentor generate <path>' first to index the codebase.", fg=typer.colors.YELLOW)
            raise typer.Exit(1)
            
        vector_store = VectorStore(str(vector_db_path))
        
        typer.echo("Searching codebase...")
        results = vector_store.retrieve(question, n_results=5)
        
        context = ""
        if results and results.get('documents') and len(results['documents']) > 0:
            context = "\n---\n".join(results['documents'][0])
            
        prompt = f"""
You are an expert developer assistant. Answer the user's question based strictly on the following codebase snippets.

Context Snippets:
{context}

Question: {question}

CRITICAL RULE: DO NOT hallucinate. If the answer is not in the context, tell the user you don't know based on the parsed code.
"""
        typer.echo("Generating answer...")
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        
        typer.echo("\n--- Answer ---\n")
        typer.echo(response.choices[0].message.content)
        
    except litellm.exceptions.APIError as e:
        handle_litellm_error(e)
    except Exception as e:
        typer.secho(f"Error: Failed to process the chat query.", fg=typer.colors.RED)
        typer.secho(f"Details: {str(e)}", fg=typer.colors.RED)
        raise typer.Exit(1)

@app.command()
def serve(port: int = typer.Option(8000, help="Port to run the Web UI on")):
    """
    Spins up the Web UI locally.
    """
    typer.secho(f"Starting Documentor Web UI on http://localhost:{port}", fg=typer.colors.GREEN)
    uvicorn.run("documentor.web.main:app", host="127.0.0.1", port=port, reload=False)

if __name__ == "__main__":
    app()
