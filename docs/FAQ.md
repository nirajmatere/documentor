# Frequently Asked Questions (FAQ)

## 1. How can I set my own API key?

Documentor supports multiple interfaces, and you can configure your LLM API keys for each:

*   **CLI:** Set your keys via standard environment variables (e.g., `export OPENAI_API_KEY="..."`). You can also place a `.env` file in the root of the project you are documenting, and Documentor will automatically load it.
*   **Web App:** If you run the local Web UI, the backend will inherit your system's environment variables. We also plan to include a "Settings" page in the Web UI where you can securely input your API key for that session.
*   **GitHub Action:** When running in CI/CD, store your API keys as **GitHub Repository Secrets**. You can pass them to the Documentor action in your workflow file (`.github/workflows/documentor.yml`) like this:
    ```yaml
    env:
      GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
    ```

## 2. Does Documentor work well with any LLM?

**Yes!** We use [LiteLLM](https://github.com/BerriAI/litellm) as our orchestration layer. LiteLLM acts as a universal translator that supports 100+ LLM providers. Instead of writing custom API requests for OpenAI, Anthropic, or Gemini, Documentor sends a standardized request. LiteLLM automatically detects the model prefix (e.g., `gemini/gemini-1.5-pro` vs `gpt-4o`), retrieves the corresponding API key from your environment, and formats the prompt exactly as the specific provider expects.

## 3. How does choosing different API keys/models affect the project?

While Documentor will run successfully with any supported model, your choice of LLM will affect the final output in three key ways:

*   **Quality & Reasoning:** State-of-the-art models (like GPT-4o, Claude 3.5 Sonnet, or Gemini 1.5 Pro) generally produce more accurate architecture diagrams, better recognize complex dependencies, and write more comprehensive explanations than smaller or older models.
*   **Context Window Limits:** Different models have different maximum context lengths (e.g., Gemini 1.5 Pro supports 1-2M tokens, while some local models might only support 4k-8k). If you use a model with a small context window on a very large codebase, you may encounter "context limit exceeded" errors during the generation phase.
*   **Formatting Adherence:** We rely on LLMs to output strict formats, such as Markdown and Mermaid.js syntax for diagrams. Highly capable models are much better at strictly adhering to these formatting instructions, reducing the chance of rendering errors in the final documentation.
