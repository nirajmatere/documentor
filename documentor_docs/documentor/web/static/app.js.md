# Technical Documentation: `documentor/web/static/app.js`

## Overview

The `app.js` file is the primary client-side JavaScript module for the Documentor web interface. It manages UI state, controls layout toggles (theme, chat pane, full-screen modes), dynamically constructs and renders a hierarchical directory tree for documentation, loads markdown content, and handles interactive chat capabilities with backend API endpoints.

---

## Key Features

1. **Theme Management**: Light/dark mode persistent toggling using browser `localStorage`.
2. **Workspace & Layout Controls**: Toggling chat visibility and chat full-screen layout states.
3. **Markdown Rendering Engine Setup**: Configuration of `marked.js` options for secure and formatted text parsing.
4. **Documentation Explorer**:
   * Async fetching of repository document structures from `/api/docs`.
   * Dynamic recursive construction of a file/folder tree view.
   * Auto-loading of the first document on initial application load.
5. **Document Viewer**: Async retrieval (`/api/docs/content`) and markdown parsing of selected documentation files.
6. **Interactive AI Chat Interface**: Async messaging interface querying `/api/chat`, supporting loading states, formatted markdown responses, and auto-scrolling chat history.

---

## DOM Element Selectors

The script binds to and manipulates the following elements upon DOM load:

| Selector | DOM Element Reference | Functionality |
| :--- | :--- | :--- |
| `#docs-list` | `docsList` | Container list for the document file tree navigation. |
| `#viewer-content` | `viewerContent` | Main container pane where markdown content is rendered. |
| `#chat-form` | `chatForm` | Form element containing the chat query submission interface. |
| `#chat-input` | `chatInput` | Input field for user chat messages. |
| `#chat-history` | `chatHistory` | Display container for user and bot chat messages. |
| `#toggle-chat-btn` | `toggleChatBtn` | Button to toggle visibility of the chat pane. |
| `#chat-section` | `chatSection` | Container wrapping the entire chat UI. |
| `.workspace-grid` | `workspaceGrid` | Parent container element controlling overall workspace layout modes. |
| `#toggle-theme-btn` | `toggleThemeBtn` | Button to toggle between light and dark themes. |
| `#fullscreen-chat-btn` | `fullscreenChatBtn` | Button to expand chat section into full-screen mode. |

---

## Configuration & UI Toggles

### Theme Toggle
* **Initialization**: On initial script execution, reads `localStorage.getItem('theme')`. If set to `'light'`, it applies the `light-mode` CSS class to `document.documentElement`.
* **Event Listener**: Clicking `toggleThemeBtn` toggles the `light-mode` class on `document.documentElement` and persists the user preference (`'light'` or `'dark'`) into `localStorage`.

### Workspace Layout Controls
* **Full-screen Chat**: Clicking `fullscreenChatBtn` toggles the `chat-fullscreen` class on `.workspace-grid`.
* **Chat Toggle**: Clicking `toggleChatBtn` toggles the `hidden` class on `chatSection`.
  * If hidden: removes `chat-open` and `chat-fullscreen` classes from `workspaceGrid`.
  * If visible: adds `chat-open` class to `workspaceGrid`.

### Marked JS Options
The external `marked` library is initialized with the following security and formatting options:
```javascript
marked.setOptions({
    headerIds: false,
    mangle: false,
    breaks: true
});
```

---

## Functions & Core Logic

### `loadDocs()`

Fetches the available documentation list for the repository path `.` and builds the tree UI.

* **API Request**: `GET /api/docs?path=.`
* **Process**:
  1. Requests documentation file list from backend.
  2. Clears `#docs-list`.
  3. Displays an empty state message if no documents exist.
  4. Parses array of file path strings into a nested tree object.
  5. Invokes internal recursive helper `renderTree(node, parentEl)` to build `<ul>`/`<li>` elements:
     * **Files (`tree-file`)**: Prepends `📄 `, adds event listeners for active selection, and calls `loadDocContent(repoPath, doc)`.
     * **Folders (`tree-folder`)**: Prepends `📂 `, renders nested `<ul>` (`tree-nested`), and adds click handlers to collapse/expand folders, updating icon states (`📁` / `📂`).
  6. Automatically triggers a `click` event on the first `.tree-file` found in the list.
* **Error Handling**: Displays an error message inside `docsList` if the network request fails or returns a non-OK HTTP status.

---

### `loadDocContent(repoPath, doc)`

Retrieves and displays the content of a selected documentation file.

* **Parameters**:
  * `repoPath` *(string)*: Root path context (defaults to `"."`).
  * `doc` *(string)*: Relative file path of the document to load.
* **API Request**: `GET /api/docs/content?path=<encoded_repoPath>&doc=<encoded_doc>`
* **Process**:
  1. Sets `viewerContent` HTML to `<p>Loading...</p>`.
  2. Fetches content from the API.
  3. Renders the retrieved raw text as parsed Markdown using `marked.parse(data.content)`.
* **Error Handling**: Updates `viewerContent` with an inline error message styled with `--error` color if the fetch fails.

---

### Chat System Logic

#### `chatForm` Submit Event
* **Parameters sent via POST**:
  * `query`: Trimmed user query string from `chatInput`.
  * `path`: `"."`
  * `model`: `""` (relies on backend defaults)
* **Process**:
  1. Prevents default form submission.
  2. Extracts and validates non-empty query string.
  3. Appends user message to history via `appendMessage('user', query, false)`.
  4. Disables `chatInput`.
  5. Appends temporary bot message placeholder via `appendMessage('bot', 'Thinking...', false)` and retains its unique ID (`loaderId`).
  6. Sends POST request to `/api/chat` with JSON body payload.
  7. On success, updates the bot loader message using `updateMessage(loaderId, data.answer, true)` to parse and display markdown.
  8. On failure, updates the bot loader message with the error text styled in `--error` color.
  9. Re-enables `chatInput` and restores focus.

#### `appendMessage(role, text, useMarkdown = false)`
* **Parameters**:
  * `role` *(string)*: Message sender CSS modifier (`'user'` or `'bot'`).
  * `text` *(string)*: Raw message text or markdown content.
  * `useMarkdown` *(boolean)*: Toggles standard text rendering vs `marked.parse()` markdown rendering.
* **Behavior**:
  * Generates unique message ID: `'msg-' + Date.now()`.
  * Appends message `<div>` element to `chatHistory`.
  * Automatically scrolls `chatHistory` container to the bottom.
* **Returns**: Generated element string ID (`id`).

#### `updateMessage(id, text, useMarkdown = false)`
* **Parameters**:
  * `id` *(string)*: DOM element ID of the message to update.
  * `text` *(string)*: New text content or markdown.
  * `useMarkdown` *(boolean)*: Toggles standard text rendering vs `marked.parse()` markdown rendering.
* **Behavior**:
  * Finds targeted DOM element by ID.
  * Replaces its contents with raw text or parsed markdown HTML.
  * Automatically scrolls `chatHistory` container to the bottom.

---

## API Integration Reference

| Endpoint | Method | Parameters / Body | Description |
| :--- | :--- | :--- | :--- |
| `/api/docs` | `GET` | `path` (Query string) | Fetches array of document paths (`data.docs`). |
| `/api/docs/content` | `GET` | `path`, `doc` (Query strings) | Fetches file content string (`data.content`) for a given document. |
| `/api/chat` | `POST` | `{ query: string, path: string, model: string }` | Submits chat prompt and returns generated answer string (`data.answer`). |