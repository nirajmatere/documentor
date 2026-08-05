# Documentor

An enterprise-grade AI documentation suite. It ingests a codebase, parses it semantically, generates accurate documentation using LLMs, and serves it via CLI, Web UI, and CI/CD pipelines.

## BYO-LLM
Documentor uses LiteLLM under the hood, allowing you to use your preferred model (OpenAI, Anthropic, Gemini, DeepSeek, local models via Ollama, etc.).

Simply set the corresponding environment variables:
```bash
export OPENAI_API_KEY="sk-..."
# or
export GEMINI_API_KEY="AIza..."
# or
export ANTHROPIC_API_KEY="sk-ant-..."
```
