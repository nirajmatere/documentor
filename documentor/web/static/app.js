document.addEventListener('DOMContentLoaded', () => {
    const docsList = document.getElementById('docs-list');
    const viewerContent = document.getElementById('viewer-content');
    
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatHistory = document.getElementById('chat-history');
    
    const toggleChatBtn = document.getElementById('toggle-chat-btn');
    const chatSection = document.getElementById('chat-section');
    const workspaceGrid = document.querySelector('.workspace-grid');
    const docsSidebar = document.getElementById('docs-sidebar');
    const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
    const openSidebarBtn = document.getElementById('open-sidebar-btn');
    const sidebarStub = document.getElementById('sidebar-stub');
    
    const toggleThemeBtn = document.getElementById('toggle-theme-btn');
    const fullscreenChatBtn = document.getElementById('fullscreen-chat-btn');
    const closeChatBtn = document.getElementById('close-chat-btn');
    
    let chatHistoryArr = [];
    
    // Theme toggle
    if (localStorage.getItem('theme') === 'light') {
        document.documentElement.classList.add('light-mode');
    }
    
    toggleThemeBtn.addEventListener('click', () => {
        document.documentElement.classList.toggle('light-mode');
        localStorage.setItem('theme', document.documentElement.classList.contains('light-mode') ? 'light' : 'dark');
        try { mermaid.initialize({ theme: (document.documentElement.classList.contains('light-mode') ? 'default' : 'dark') }); } catch(e){}
    });

    fullscreenChatBtn.addEventListener('click', () => {
        workspaceGrid.classList.toggle('chat-fullscreen');
    });

    if (toggleSidebarBtn) {
        toggleSidebarBtn.addEventListener('click', () => {
            docsSidebar.classList.add('hidden');
            workspaceGrid.classList.add('sidebar-hidden');
            if (sidebarStub) sidebarStub.classList.remove('hidden');
        });
    }

    if (openSidebarBtn) {
        openSidebarBtn.addEventListener('click', () => {
            docsSidebar.classList.remove('hidden');
            workspaceGrid.classList.remove('sidebar-hidden');
            if (sidebarStub) sidebarStub.classList.add('hidden');
        });
    }

    if (closeChatBtn) {
        closeChatBtn.addEventListener('click', () => {
            chatSection.classList.add('hidden');
            workspaceGrid.classList.remove('chat-open');
            workspaceGrid.classList.remove('chat-fullscreen');
        });
    }
    
    toggleChatBtn.addEventListener('click', () => {
        chatSection.classList.toggle('hidden');
        if (chatSection.classList.contains('hidden')) {
            workspaceGrid.classList.remove('chat-open');
            workspaceGrid.classList.remove('chat-fullscreen');
        } else {
            workspaceGrid.classList.add('chat-open');
        }
    });
    
    // Configure marked for security
    const renderer = new marked.Renderer();
    const originalCode = renderer.code.bind(renderer);
    renderer.code = function(code, language, isEscaped) {
        if (language === 'mermaid') {
            return `<div class="mermaid">${code}</div>`;
        }
        return originalCode(code, language, isEscaped);
    };

    const originalLink = renderer.link.bind(renderer);
    renderer.link = function(...args) {
        const link = originalLink(...args);
        return link.replace('<a ', '<a target="_blank" rel="noopener noreferrer" ');
    };

    marked.setOptions({
        renderer: renderer,
        headerIds: false,
        mangle: false,
        breaks: true
    });

    try {
        mermaid.initialize({ startOnLoad: false, theme: (document.documentElement.classList.contains('light-mode') ? 'default' : 'dark') });
    } catch(e) {}

    // Load Existing Docs
    async function loadDocs() {
        const repoPath = ".";
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

            // Helper to build tree
            const tree = {};
            data.docs.forEach(doc => {
                const parts = doc.split('/');
                let current = tree;
                for (let i = 0; i < parts.length; i++) {
                    const part = parts[i];
                    if (!current[part]) {
                        current[part] = (i === parts.length - 1) ? doc : {};
                    }
                    current = current[part];
                }
            });

            function renderTree(node, parentEl) {
                const ul = document.createElement('ul');
                ul.className = parentEl === docsList ? 'tree-root' : 'tree-nested';
                
                for (const key of Object.keys(node).sort()) {
                    const li = document.createElement('li');
                    
                    if (typeof node[key] === 'string') {
                        // File
                        li.className = 'tree-file';
                        li.textContent = '📄 ' + key;
                        li.addEventListener('click', (e) => {
                            e.stopPropagation();
                            document.querySelectorAll('.docs-list .tree-file').forEach(el => el.classList.remove('active'));
                            li.classList.add('active');
                            loadDocContent(repoPath, node[key]);
                        });
                    } else {
                        // Folder
                        li.className = 'tree-folder';
                        li.innerHTML = `<span>📂 ${key}</span>`;
                        const childUl = renderTree(node[key], li);
                        li.appendChild(childUl);
                        
                        li.querySelector('span').addEventListener('click', (e) => {
                            e.stopPropagation();
                            childUl.classList.toggle('hidden');
                            const span = li.querySelector('span');
                            if(childUl.classList.contains('hidden')) {
                                span.textContent = '📁 ' + key;
                            } else {
                                span.textContent = '📂 ' + key;
                            }
                        });
                    }
                    ul.appendChild(li);
                }
                return ul;
            }

            docsList.innerHTML = '';
            docsList.appendChild(renderTree(tree, docsList));
            
            // Auto-load first doc
            const firstFile = docsList.querySelector('.tree-file');
            if (firstFile) firstFile.click();

        } catch (err) {
            docsList.innerHTML = `<li class="empty-state" style="color:var(--error)">${err.message}</li>`;
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

    // Auto load docs on start
    loadDocs();

    // Handle Chat
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const query = chatInput.value.trim();
        const repoPath = ".";
        const model = ""; // We'll let the backend use the environment default
        
        if (!query) return;
        
        // Add User Message
        appendMessage('user', query, false);
        chatHistoryArr.push({ role: 'user', content: query });
        chatInput.value = '';
        chatInput.disabled = true;
        
        // Add Temporary Bot Loader
        const loaderId = appendMessage('bot', 'Thinking...', false);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, path: repoPath, model: model, history: chatHistoryArr.slice(0, -1) })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Chat request failed.');
            }
            
            updateMessage(loaderId, data.answer, true);
            chatHistoryArr.push({ role: 'assistant', content: data.answer });
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
            div.innerHTML = DOMPurify.sanitize(marked.parse(text), { ADD_TAGS: ['div'], ADD_ATTR: ['class'] });
            setTimeout(() => { try { mermaid.run({ nodes: div.querySelectorAll('.mermaid') }); } catch(e){} }, 10);
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
                msgElement.innerHTML = DOMPurify.sanitize(marked.parse(text), { ADD_TAGS: ['div'], ADD_ATTR: ['class'] });
                setTimeout(() => { try { mermaid.run({ nodes: msgElement.querySelectorAll('.mermaid') }); } catch(e){} }, 10);
            } else {
                msgElement.textContent = text;
            }
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    }
});
