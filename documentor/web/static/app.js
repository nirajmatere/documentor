document.addEventListener('DOMContentLoaded', () => {
    const generateForm = document.getElementById('generate-form');
    const generateBtn = document.getElementById('generate-btn');
    const loadBtn = document.getElementById('load-btn');
    const btnText = generateBtn.querySelector('.btn-text');
    const loader = generateBtn.querySelector('.loader');
    const loadLoader = loadBtn.querySelector('.loader');
    const generateResult = document.getElementById('generate-result');
    
    const docsList = document.getElementById('docs-list');
    const viewerContent = document.getElementById('viewer-content');
    
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatHistory = document.getElementById('chat-history');
    
    // Configure marked for security
    marked.setOptions({
        headerIds: false,
        mangle: false,
        breaks: true
    });

    // Helper to show messages in generate section
    function showMessage(msg, isError = false) {
        generateResult.textContent = msg;
        generateResult.className = `message ${isError ? 'error' : 'success'}`;
        generateResult.classList.remove('hidden');
    }

    // Load Existing Docs
    async function loadDocs() {
        const repoPath = document.getElementById('repo-path').value.trim();
        if (!repoPath) {
            showMessage("Please enter a Repository Path first.", true);
            return;
        }

        const btnTextLoad = loadBtn.querySelector('.btn-text');
        loadBtn.disabled = true;
        btnTextLoad.textContent = 'Loading...';
        loadLoader.classList.remove('hidden');

        try {
            const response = await fetch(`/api/docs?path=${encodeURIComponent(repoPath)}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to load docs.');
            }

            docsList.innerHTML = '';
            if (data.docs.length === 0) {
                docsList.innerHTML = '<li class="empty-state">No documentation found in this path.</li>';
                viewerContent.innerHTML = '<h2>No Docs Found</h2><p>Run Generate Docs first.</p>';
                return;
            }

            data.docs.forEach(doc => {
                const li = document.createElement('li');
                li.textContent = doc;
                li.addEventListener('click', () => {
                    document.querySelectorAll('.docs-list li').forEach(el => el.classList.remove('active'));
                    li.classList.add('active');
                    loadDocContent(repoPath, doc);
                });
                docsList.appendChild(li);
            });
            
            // Auto-load first doc
            docsList.firstChild.click();

        } catch (err) {
            docsList.innerHTML = `<li class="empty-state" style="color:var(--error)">${err.message}</li>`;
        } finally {
            loadBtn.disabled = false;
            btnTextLoad.textContent = 'Load Existing';
            loadLoader.classList.add('hidden');
        }
    }

    // Load specific document content
    async function loadDocContent(repoPath, doc) {
        viewerContent.innerHTML = '<p>Loading...</p>';
        try {
            const response = await fetch(`/api/docs/content?path=${encodeURIComponent(repoPath)}&doc=${encodeURIComponent(doc)}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to load content.');
            }
            
            viewerContent.innerHTML = marked.parse(data.content);
        } catch (err) {
            viewerContent.innerHTML = `<p style="color:var(--error)">Error: ${err.message}</p>`;
        }
    }

    loadBtn.addEventListener('click', loadDocs);

    // Handle Generation
    generateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // If the event was triggered by the submit button
        if (e.submitter && e.submitter.id === 'load-btn') return;

        const repoPath = document.getElementById('repo-path').value;
        const model = document.getElementById('model-select').value;
        
        // UI Loading State
        generateBtn.disabled = true;
        btnText.textContent = 'Generating... (This may take a minute)';
        loader.classList.remove('hidden');
        generateResult.classList.add('hidden');
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: repoPath, model: model })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to generate documentation.');
            }
            
            showMessage(data.message);
            // Automatically load the newly generated docs
            loadDocs();
        } catch (err) {
            showMessage(err.message, true);
        } finally {
            // Restore UI
            generateBtn.disabled = false;
            btnText.textContent = 'Generate Docs';
            loader.classList.add('hidden');
        }
    });

    // Handle Chat
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const query = chatInput.value.trim();
        const repoPath = document.getElementById('repo-path').value;
        const model = document.getElementById('model-select').value;
        
        if (!query) return;
        if (!repoPath) {
            alert('Please enter a Repository Path above first.');
            return;
        }
        
        // Add User Message
        appendMessage('user', query, false);
        chatInput.value = '';
        chatInput.disabled = true;
        
        // Add Temporary Bot Loader
        const loaderId = appendMessage('bot', 'Thinking...', false);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, path: repoPath, model: model })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Chat request failed.');
            }
            
            updateMessage(loaderId, data.answer, true);
        } catch (err) {
            updateMessage(loaderId, `Error: ${err.message}`, false);
            document.getElementById(loaderId).style.color = 'var(--error)';
        } finally {
            chatInput.disabled = false;
            chatInput.focus();
        }
    });

    function appendMessage(role, text, useMarkdown = false) {
        const id = 'msg-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = `chat-msg ${role}`;
        if (useMarkdown) {
            div.innerHTML = marked.parse(text);
        } else {
            div.textContent = text;
        }
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return id;
    }

    function updateMessage(id, text, useMarkdown = false) {
        const msgElement = document.getElementById(id);
        if (msgElement) {
            if (useMarkdown) {
                msgElement.innerHTML = marked.parse(text);
            } else {
                msgElement.textContent = text;
            }
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    }
});
