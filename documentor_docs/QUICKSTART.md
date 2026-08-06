# Quickstart Guide

This guide covers the environment configuration and available command-line commands based on the codebase interface.

---

## 1. Configuration & Environment Variables

The application manages settings via a configuration file located at `~/.documentor/config.env`.

### Environment Variables
The following environment variables can be stored in `~/.documentor/config.env` or set in your environment:

* `MODEL_NAME`: LiteLLM compatible model name (Default if unset: `gemini/gemini-3.6-flash`)
* `GEMINI_API_KEY`: API key for Gemini models
* `OPENAI_API_KEY`: API key for OpenAI models
* `ANTHROPIC_API_KEY`: API key for Anthropic models

### Setup Configuration
Run the setup wizard to interactively configure your Bring-Your-Own-LLM (BYO-LLM) settings and API keys:

```bash
# Triggers configuration prompt for MODEL_NAME and API keys
configure
```
*Note: Ensure write permissions are available for `~/.documentor/config.env`.*

---

## 2. Usage & Commands

### Generate Documentation

Executes the pipeline to parse, vectorize, map dependencies, and generate documentation for a target repository.

```bash
generate <path> [OPTIONS]
```

* **Arguments:**
  * `<path>`: (Required) Path to the repository to document.

* **Options:**
  * `--model TEXT`: LiteLLM compatible model name (overrides default or `MODEL_NAME`).
  * `--regenerate`: Force regenerate all documentation, overwriting existing files.
  * `--resume`: Skip already generated documentation files (enabled by default).
  * `-f, --file TEXT`: Specific file(s) to regenerate documentation for (relative to repository path).

**Example:**
```bash
generate /path/to/repo --model gemini/gemini-3.6-flash
```

---

### Chat / Query Codebase

Performs Retrieval-Augmented Generation (RAG) queries against an indexed codebase.

> **Prerequisite:** You must run `generate <path>` on the repository first to create the vector database index (`.documentor/chroma`).

```bash
chat [QUESTION] [OPTIONS]
```

* **Arguments:**
  * `[QUESTION]`: (Optional) Question to ask about the codebase. If omitted, enters an interactive chat session (type `exit` or `quit` to end).

* **Options:**
  * `--path TEXT`: Path to the repository (Default: `.`).
  * `--model TEXT`: LiteLLM compatible model name.

**Examples:**

* Single query:
  ```bash
  chat "How does authentication work?" --path /path/to/repo
  ```

* Interactive chat session:
  ```bash
  chat --path /path/to/repo
  ```