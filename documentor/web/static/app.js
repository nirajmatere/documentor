document.addEventListener('DOMContentLoaded', () => {
    const generateForm = document.getElementById('generate-form');
    const generateBtn = document.getElementById('generate-btn');
    const btnText = generateBtn.querySelector('.btn-text');
    const loader = generateBtn.querySelector('.loader');
    const generateResult = document.getElementById('generate-result');
    
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatHistory = document.getElementById('chat-history');
    
    // Helper to show messages in generate section
    function showMessage(msg, isError = false) {
        generateResult.textContent = msg;
        generateResult.className = `message ${isError ? 'error' : 'success'}`;
        generateResult.classList.remove('hidden');
    }

    // Handle Generation
    generateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
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
        appendMessage('user', query);
        chatInput.value = '';
        chatInput.disabled = true;
        
        // Add Temporary Bot Loader
        const loaderId = appendMessage('bot', 'Thinking...');
        
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
            
            updateMessage(loaderId, data.answer);
        } catch (err) {
            updateMessage(loaderId, `Error: ${err.message}`);
            document.getElementById(loaderId).style.color = 'var(--error)';
        } finally {
            chatInput.disabled = false;
            chatInput.focus();
        }
    });

    function appendMessage(role, text) {
        const id = 'msg-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = `chat-msg ${role}`;
        div.textContent = text;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return id;
    }

    function updateMessage(id, text) {
        const msgElement = document.getElementById(id);
        if (msgElement) {
            msgElement.textContent = text;
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    }
});
