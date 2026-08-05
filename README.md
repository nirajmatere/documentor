# Documentor

An enterprise-grade AI documentation suite. It ingests a codebase, parses it semantically, generates accurate documentation using LLMs, and serves it via CLI, Web UI, and CI/CD pipelines.

## Installation

### Recommended Method (pipx)
Because Documentor is a standalone CLI tool, the best way to install it on modern Linux/macOS systems (which enforce PEP 668) is using `pipx`. This installs Documentor in an isolated environment while exposing the CLI globally.

```bash
# If you don't have pipx installed: python3 -m pip install --user pipx
pipx install git+https://github.com/nirajmatere/documentor.git
```

### Alternative Methods
If you are inside an active virtual environment (like `.venv/`), you can use standard `pip`:
```bash
pip install git+https://github.com/nirajmatere/documentor.git
```
*(Note: If you attempt this globally on newer Linux distributions without `pipx`, you will get an `externally-managed-environment` error. You can bypass this by appending `--break-system-packages`, though `pipx` is heavily preferred).*

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
documentor generate /path/to/your/repo --model gpt-4o-mini
```
Once the repository is indexed, you can chat with your codebase using RAG:
```bash
documentor chat "How does the authentication system work?" --path /path/to/your/repo
```

### 2. Web UI (Playground)
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
          model: 'gpt-4o-mini'
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      - run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add docs/ ARCHITECTURE.md QUICKSTART.md
          git commit -m "docs: Auto-update AI documentation" || echo "No changes to commit"
          git push
```
