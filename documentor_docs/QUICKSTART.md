# Quickstart Guide

This guide covers configuring and using the CLI tool based on the available codebase functionality.

---

## Configuration & Environment Variables

Configuration settings are stored in `~/.documentor/config.env`. 

### Supported Environment Variables
- `MODEL_NAME`: LiteLLM-compatible model name (Default: `gemini/gemini-3.6-flash`)
- `GEMINI_API_KEY`: API key for Google Gemini provider
- `OPENAI_API_KEY`: API key for OpenAI provider
- `ANTHROPIC_API_KEY`: API key for Anthropic provider

### Setting Up Configuration
Run the interactive configuration command to set up your Bring-Your-Own-LLM (BYO-LLM) settings and API keys:

```bash
configure
```
*You will be prompted to enter values for `MODEL_NAME`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, and `ANTHROPIC_API_KEY`. Press enter on any prompt to leave it empty.*

---

## Usage Commands

### 1. Generate Documentation
Parses the repository, vectorizes the code (stored in `<path>/.documentor/chroma`), maps dependencies, and generates documentation files inside `documentor_docs`.

```bash
generate <path-to-repository>
```

#### Options:
- `--model <model_name>`: LiteLLM-compatible model name to use for generation.
- `--regenerate`: Force regenerate all documentation, overwriting existing files.
- `--resume`: Skip already generated documentation files (default behavior).
- `-f, --file <file_path>`: Specify individual files (relative to repository path) to regenerate documentation for.

---

### 2. Chat with Codebase (RAG Query)
Query the codebase using Retrieval-Augmented Generation (RAG). 

> **Prerequisite:** You must run `generate <path>` first to index the codebase into the vector store.

#### Single Question Mode
```bash
chat "How does the parsing logic work?" --path <path-to-repository>
```

#### Interactive Chat Mode
Omit the question argument to launch an interactive session:
```bash
chat --path <path-to-repository>
```
*(Type `exit` or `quit` to end the interactive session).*

#### Options:
- `question` *(Optional)*: The question to ask about the codebase.
- `--path <path>`: Path to the repository (Default: `.`).
- `--model <model_name>`: LiteLLM-compatible model name.