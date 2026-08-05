# Documentor

An enterprise-grade AI documentation suite. It ingests a codebase, parses it semantically, generates accurate documentation using LLMs, and serves it via CLI, Web UI, and CI/CD pipelines.

## Installation

### Recommended Method (pipx)
Because Documentor is a standalone CLI tool, the best way to install it on modern Linux/macOS systems (which enforce PEP 668) is using `pipx`. This installs Documentor in an isolated environment while exposing the CLI globally.

```bash
# If you don't have pipx installed: python3 -m pip install --user pipx
pipx install documentor-ai
```

### Alternative Methods
If you are inside an active virtual environment (like `.venv/`), you can use standard `pip`:
```bash
pip install documentor-ai
```
*(Note: If you attempt this globally on newer Linux distributions without `pipx`, you will get an `externally-managed-environment` error. You can bypass this by appending `--break-system-packages`, though `pipx` is heavily preferred).*

### Upgrading an Existing Installation
To get the latest version (including new features like Interactive Chat), run the upgrade command corresponding to how you installed it:

```bash
# If you used pipx
pipx upgrade documentor-ai

# If you used standard pip
pip install --upgrade documentor-ai
```

## BYO-LLM (Bring Your Own LLM)
Documentor uses LiteLLM under the hood, allowing you to use your preferred model (OpenAI, Anthropic, Gemini, DeepSeek, local models via Ollama, etc.).

Run the interactive setup command to configure your API keys:
```bash
documentor configure
```
*(Alternatively, you can just export your keys directly in your terminal, e.g. `export OPENAI_API_KEY="sk-..."`)*

## Usage

### 1. Command Line Interface (CLI)
To generate documentation for a repository, run:
```bash
documentor generate /path/to/your/repo --model gemini/gemini-3.6-flash
```

> **Note on Parsing:** Documentor automatically ignores `node_modules`, `dist`, `.env` files, logs, and all `.git` ignored files by default. If you want to force Documentor to ignore specific files or folders, just create a `.docignore` file in the root of your project!

**More Examples:**
Generate for the current directory (`.`) using Google's fast Gemini Flash model:
```bash
documentor generate . --model gemini/gemini-3.6-flash
```

**Single/Multiple Specific Files:**
If you only want to generate or regenerate documentation for specific files (for instance, if you only updated a few files in a large project), you can specify them using the `--file` or `-f` flag. This will skip `ARCHITECTURE.md` and `QUICKSTART.md` and only document the targeted files:
```bash
documentor generate . -f src/main.py -f src/utils.py
```

Generate using Anthropic's Claude:
```bash
documentor generate . --model claude-3-5-sonnet-20240620
```

### 2. Chat with your Codebase (RAG)
Once the repository is indexed, you can ask questions about your codebase.

**Interactive Chat Mode (Recommended):**
If you run `chat` without providing a specific question, it will drop you into an interactive terminal where you can chat continuously!
```bash
documentor chat --path . --model gemini/gemini-3.6-flash
```

**Single Question Mode:**
If you just want a quick answer, you can provide the question directly:
```bash
documentor chat "How does the authentication system work?" --path . --model gemini/gemini-3.6-flash
```

### 3. Web UI (Playground)
Prefer a visual interface? Spin up the beautifully designed, glassmorphic Web UI:
```bash
documentor serve --port 8000
```
Then open `http://localhost:8000` in your browser.

### 3. GitHub Action (CI/CD)
Documentor comes packaged as a lightning-fast Docker Action. You can automate documentation generation on your Pull Requests by creating `.github/workflows/documentor.yml` in your target repository:

```yaml
name: Generate AI Docs
on:
  pull_request:
    branches: [ main ]
jobs:
  docs:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: nirajmatere/documentor@main
        with:
          model: 'gemini/gemini-3.6-flash'
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      - run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add documentor_docs/
          git commit -m "docs: Auto-update AI documentation" || echo "No changes to commit"
          git push
```
