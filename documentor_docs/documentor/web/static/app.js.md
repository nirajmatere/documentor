# Technical Documentation: `documentor/web/static/app.js`

## Overview

The `app.js` file serves as the client-side controller for the Documentor web application interface. Executed upon the `DOMContentLoaded` event, it manages user layout controls (sidebar, theme, chat panel), fetches and renders file-tree structures for existing documentation, dynamically parses and renders Markdown and Mermaid diagrams, and provides an interactive document-assisted chat interface.

---

## Technical Dependencies

The script relies on the following external global browser utilities/libraries:

1. **`marked`**: For rendering Markdown string content into HTML.
2. **`mermaid`**: For rendering graphical diagrams declared within Markdown code blocks (`language-mermaid`).
3. **`DOMPurify`**: For sanitizing HTML generated from Markdown content prior to injecting it into the DOM (used in the chat panel).
4. **`localStorage`**: For persisting the user's theme selection (`light` or `dark`).

---

## State Management

* **`chatHistoryArr`**: An array of message objects (`{ role: 'user' | 'assistant', content: string }`) maintained in memory to preserve conversation history across chat requests.

---

## Detailed Components & Logical Modules

### 1. Theme Management

Checks `localStorage` on load and applies the `light-mode` class to the root HTML element if configured. Clicking `#toggle-theme-btn`:
* Toggles the `light-mode` CSS class on `document.documentElement`.
* Updates `localStorage` with `'light'` or `'dark'`.
* Re-initializes `mermaid` with either the `'default'` (light) or `'dark'` theme.

```javascript
// LocalStorage check and theme toggle listener snippet
if (localStorage.getItem('theme') === 'light') {
    document.documentElement.classList.add('light-mode');
}
```

---

### 2. Workspace Layout & Drawer Controls

The layout uses CSS classes on `.workspace-grid` and UI containers to toggle visibility:

| Element ID / Selector | Action Target | Description |
| :--- | :--- | :--- |
| `#fullscreen-chat-btn` | `.workspace-grid` | Toggles class `chat-fullscreen`. |
| `#toggle-sidebar-btn` | `#docs-sidebar`, `.workspace-grid`, `#sidebar-stub` | Hides sidebar (`hidden`), updates grid (`sidebar-hidden`), reveals sidebar stub. |
| `#open-sidebar-btn` | `#docs-sidebar`, `.workspace-grid`, `#sidebar-stub` | Restores sidebar, removes `sidebar-hidden` from grid, hides stub. |
| `#close-chat-btn` | `#chat-section`, `.workspace-grid` | Hides chat section (`hidden`), removes `chat-open` and `chat-fullscreen` classes. |
| `#toggle-chat-btn` | `#chat-section`, `.workspace-grid` | Toggles chat section visibility. Adjusts `chat-open` and `chat-fullscreen` classes accordingly. |

---

### 3. Markdown & Mermaid Configuration

`marked` is configured with a custom renderer instance to safely handle external links and convert Mermaid syntax:

* **Code Block Overriding**: Intercepts code blocks where `language === 'mermaid'` and returns a wrapper `<div class="mermaid">${code}</div>`.
* **Link Overriding**: Intercepts link rendering to force external targets via `target="_blank" rel="noopener noreferrer"`.
* **Parser Options**:
  * `headerIds: false`
  * `mangle: false`
  * `breaks: true`

`mermaid` initialization is triggered on startup with `startOnLoad: false` and theme dynamically determined based on whether `light-mode` is present on the document element.

---

### 4. Documentation Explorer

#### `loadDocs()`
* **API Call**: `GET /api/docs?path=.`
* **Flow**:
  1. Requests documentation file list for repository path `"."`.
  2. Handles errors or empty document responses by showing status messages in `#docs-list` and `#viewer-content`.
  3. Transforms flat string array of relative document paths (`data.docs`) into a nested JavaScript object tree (`tree`).
  4. Calls `renderTree(tree, docsList)` to build DOM elements recursively.
  5. Automatically executes a click on the first rendered file (`.tree-file`) to load its content.

#### `renderTree(node, parentEl)`
* **Parameters**:
  * `node`: Object containing sub-trees or string values (representing file relative paths).
  * `parentEl`: HTML element container.
* **Logic**:
  * Sorts child keys alphabetically.
  * Creates an `<ul>` list element assigned class `tree-root` (for root level) or `tree-nested` (for nested subfolders).
  * **Leaf Nodes (Files)**: Appends `<li>` with class `tree-file`. Clicking a file highlights it as `.active` and triggers `loadDocContent(repoPath, filePath)`.
  * **Branch Nodes (Folders)**: Appends `<li>` with class `tree-folder` containing a clickable `<span>` element (`📂` or `📁`). Clicking toggles the nested `<ul>` visibility and updates folder icons.

#### `loadDocContent(repoPath, doc)`
* **Parameters**:
  * `repoPath`: Repository path identifier string (default: `"."`).
  * `doc`: Relative file path string.
* **API Call**: `GET /api/docs/content?path=<repoPath>&doc=<doc>`
* **Flow**:
  1. Shows `Loading...` prompt in `#viewer-content`.
  2. Parses returned Markdown string using `marked.parse(data.content)`.
  3. Replaces `#viewer-content` inner HTML with the parsed output.

---

### 5. Chat System Integration

#### Form Submission (`#chat-form`)
* Intercepts `submit` event.
* Captures user string query from `#chat-input`.
* Appends user query to UI using `appendMessage('user', query, false)`.
* Pushes `{ role: 'user', content: query }` into `chatHistoryArr`.
* Appends temporary loading message for the assistant using `appendMessage('bot', 'Thinking...', false)`.
* **API Call**:
  * `POST /api/chat`
  * **Payload**:
    ```json
    {
      "query": "User string query",
      "path": ".",
      "model": "",
      "history": [...] // Previous elements in chatHistoryArr excluding current query
    }
    ```
* **Response Processing**:
  * Replaces loading message using `updateMessage(loaderId, data.answer, true)`.
  * Pushes assistant answer into `chatHistoryArr` as `{ role: 'assistant', content: data.answer }`.
  * Handles errors by updating loading message text to red (`var(--error)`).
  * Restores chat input state and refocuses input.

#### Helper Functions

##### `appendMessage(role, text, useMarkdown = false)`
* Creates a message element (`div.chat-msg.${role}`) assigned a unique ID (`msg-<timestamp>`).
* If `useMarkdown` is `true`:
  * Parses `text` using `marked.parse()`.
  * Sanitizes HTML via `DOMPurify.sanitize()` configured to allow `div` tags and `class` attributes.
  * Schedules diagram rendering on child nodes via `mermaid.run()`.
* If `useMarkdown` is `false`:
  * Directly sets `textContent` to prevent HTML parsing.
* Scrolls `#chat-history` to bottom.
* Returns generated message element ID.

##### `updateMessage(id, text, useMarkdown = false)`
* Locates existing DOM element by ID.
* Applies Markdown parsing, sanitization, and Mermaid rendering if `useMarkdown` is true; otherwise updates text content.
* Scrolls `#chat-history` to bottom.

---

## API Endpoints Used

| Method | Endpoint | Query Parameters / Payload | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/docs` | `path` | Retrieves list of documentation relative paths. |
| `GET` | `/api/docs/content` | `path`, `doc` | Fetches raw content of specified documentation file. |
| `POST` | `/api/chat` | `{ query, path, model, history }` | Submits prompt and history array to retrieve AI response. |