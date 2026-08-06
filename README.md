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

Run the interactive setup command to configure your default model and API keys:
```bash
documentor configure
```
*(You will be prompted for `MODEL_NAME`, `GEMINI_API_KEY`, etc. You can just press Enter to leave them empty or fall back to the default `gemini/gemini-3.6-flash`)*

## Usage

### 1. Command Line Interface (CLI)
To generate documentation for a repository, run:
```bash
documentor generate /path/to/your/repo
```

> **Note on Parsing:** Documentor automatically ignores `node_modules`, `dist`, `.env` files, logs, and all `.git` ignored files by default. If you want to force Documentor to ignore specific files or folders, just create a `.docignore` file in the root of your project!

**More Examples:**
Generate for the current directory (`.`) using your configured model:
```bash
documentor generate .
```

**Single/Multiple Specific Files:**
If you only want to generate or regenerate documentation for specific files (for instance, if you only updated a few files in a large project), you can specify them using the `--file` or `-f` flag. This will skip `ARCHITECTURE.md` and `QUICKSTART.md` and only document the targeted files:
```bash
documentor generate . -f src/main.py -f src/utils.py
```

Generate using Anthropic's Claude (by overriding your default model):
```bash
documentor generate . --model claude-3-5-sonnet-20240620
```

### 2. Intelligent AI Assistant (Terminal)
Once the repository is indexed, you can converse with an intelligent AI assistant about your codebase directly from your terminal.

**Interactive Chat Mode (Recommended):**
If you run `chat` without providing a specific question, it will drop you into an interactive terminal where you can chat continuously!
```bash
documentor chat --path .
```

**Single Question Mode:**
If you just want a quick answer, you can provide the question directly:
```bash
documentor chat "How does the authentication system work?" --path .
```

> **Note on Intelligence:** The AI assistant is context-aware and highly intelligent! While it won't directly edit your files, you can ask it to explain code in simple terms, provide setup guides for beginners, or suggest code improvements.

### 3. Web UI (Playground & Visual Chat)
Prefer a visual interface? Spin up the beautifully designed, glassmorphic Web UI:
```bash
documentor serve --port 8000
```
Then open `http://localhost:8000` in your browser. The Web UI not only loads the documentation for your current directory (`.`), but it also features a **Full-screen Conversational AI Chat**! 

The Web UI chat includes:
- **Conversational Memory**: The AI remembers the context of your ongoing chat.
- **Mermaid Diagram Support**: Ask the AI to draw architectural diagrams, and it will render them as beautiful SVG graphics right in the chat!
- **Clean Layout**: Features a light/dark theme toggle, a collapsible sidebar, and a distraction-free fullscreen chat mode.

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
        env:
          # Define your model and map secrets appropriately
          MODEL_NAME: 'gemini/gemini-3.6-flash'
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
      - run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add documentor_docs/
          git diff --quiet && git diff --staged --quiet || git commit -m "docs: Auto-update AI documentation"
          git push
```
