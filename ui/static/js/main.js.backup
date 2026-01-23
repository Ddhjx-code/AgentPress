// ui/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Model configuration and management
    const agentModelTable = document.getElementById('agentModelTable');
    const startCreationBtn = document.getElementById('startCreation');
    const creationProgress = document.getElementById('creationProgress');
    const storyIdea = document.getElementById('storyIdea');
    const storyTheme = document.getElementById('storyTheme');

    // Knowledge base functionality
    const knowledgeTitle = document.getElementById('knowledgeTitle');
    const knowledgeType = document.getElementById('knowledgeType');
    const knowledgeContent = document.getElementById('knowledgeContent');
    const knowledgeTags = document.getElementById('knowledgeTags');
    const addKnowledgeBtn = document.getElementById('addKnowledge');
    const knowledgeSearch = document.getElementById('knowledgeSearch');
    const searchBtn = document.getElementById('searchBtn');
    const searchResults = document.getElementById('searchResults');

    // Initialize UI elements
    initializeAgentManagement();
    initializeKnowledgeBase();

    // Start story creation
    startCreationBtn.addEventListener('click', startStoryCreation);

    // Search knowledge
    searchBtn.addEventListener('click', searchKnowledgeBase);
    knowledgeSearch.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchKnowledgeBase();
        }
    });

    // Add knowledge to base
    addKnowledgeBtn.addEventListener('click', addKnowledgeToBase);

    // Initialize Agent Management
    function initializeAgentManagement() {
        const changeModelButtons = document.querySelectorAll('#agentModelTable button');
        changeModelButtons.forEach(button => {
            button.addEventListener('click', function() {
                const row = this.closest('tr');
                const agentType = row.cells[0].textContent.toLowerCase().split('/')[0].split(' ').join('_');
                const modelInput = row.querySelector('input');
                const newModel = modelInput.value;

                updateAgentModel(agentType, newModel);
            });
        });
    }

    // Start story creation process
    function startStoryCreation() {
        const idea = storyIdea.value.trim();
        const theme = storyTheme.value;

        if (!idea) {
            alert('Please enter a story idea');
            return;
        }

        // Show progress
        creationProgress.style.display = 'block';
        creationProgress.querySelector('.progress-bar').style.width = '0%';
        creationProgress.querySelector('.progress-bar').textContent = '0%';

        // Simulate creation process
        simulateCreationProgress();
    }

    // Simulate creation progress (placeholder for actual functionality)
    function simulateCreationProgress() {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.floor(Math.random() * 10) + 5;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                creationProgress.querySelector('p').textContent = 'Creation completed!';
                setTimeout(() => {
                    creationProgress.style.display = 'none';
                }, 3000);
            }

            creationProgress.querySelector('.progress-bar').style.width = progress + '%';
            creationProgress.querySelector('.progress-bar').textContent = progress + '%';
            creationProgress.querySelector('p').textContent = `Processing... ${progress}%`;
        }, 500);
    }

    // Initialize Knowledge Base functionality
    function initializeKnowledgeBase() {
        // Pre-populate some sample search results
        // In real implementation, this would be loaded from server
    }

    // Search knowledge base
    async function searchKnowledgeBase() {
        const query = knowledgeSearch.value.trim();

        if (!query) {
            return;
        }

        try {
            const response = await fetch(`/api/knowledge/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();

            displaySearchResults(data.results);
        } catch (error) {
            console.error('Error searching knowledge base:', error);

            // Fallback: show sample results
            displaySampleResults(query);
        }
    }

    // Display search results
    function displaySearchResults(results) {
        searchResults.innerHTML = '';

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="list-group-item">No results found</div>';
            return;
        }

        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'list-group-item knowledge-entry';
            item.innerHTML = `
                <h6 class="mb-1">${result.title}</h6>
                <p class="mb-1">${result.content.substring(0, 100)}${result.content.length > 100 ? '...' : ''}</p>
                <small class="text-muted">Type: ${result.knowledge_type} | Tags: ${result.tags.join(', ')}</small>
            `;

            item.addEventListener('click', () => {
                // Load the full result for editing/viewing
                loadKnowledgeEntry(result);
            });

            searchResults.appendChild(item);
        });
    }

    // Display sample results (placeholder)
    function displaySampleResults(query) {
        searchResults.innerHTML = '';
        const sampleResults = [
            {
                title: `Sample result for "${query}"`,
                content: `This is a sample knowledge entry related to your search: ${query}. This would normally come from the knowledge base.`,
                knowledge_type: 'example',
                tags: [query, 'sample']
            },
            {
                title: `Another ${query} example`,
                content: `Additional sample entry showing results for "${query}"`,
                knowledge_type: 'technique',
                tags: [query, 'technique', 'method']
            }
        ];

        sampleResults.forEach(result => {
            const item = document.createElement('div');
            item.className = 'list-group-item knowledge-entry';
            item.innerHTML = `
                <h6 class="mb-1">${result.title}</h6>
                <p class="mb-1">${result.content.substring(0, 100)}${result.content.length > 100 ? '...' : ''}</p>
                <small class="text-muted">Type: ${result.knowledge_type} | Tags: ${result.tags.join(', ')}</small>
            `;

            searchResults.appendChild(item);
        });
    }

    // Load knowledge entry for viewing/editing
    function loadKnowledgeEntry(entry) {
        knowledgeTitle.value = entry.title;
        knowledgeType.value = entry.knowledge_type;
        knowledgeContent.value = entry.content;
        knowledgeTags.value = entry.tags.join(',');
    }

    // Add knowledge to base
    async function addKnowledgeToBase() {
        const title = knowledgeTitle.value.trim();
        const type = knowledgeType.value;
        const content = knowledgeContent.value.trim();
        const tags = knowledgeTags.value.trim().split(',').map(tag => tag.trim()).filter(tag => tag);

        if (!title || !content) {
            alert('Please fill in the title and content for the knowledge entry');
            return;
        }

        try {
            const response = await fetch('/knowledge/entry', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: title,
                    content: content,
                    knowledge_type: type,
                    tags: tags,
                    source: 'manual'
                })
            });

            if (response.ok) {
                alert('Knowledge entry added successfully');

                // Clear the form
                knowledgeTitle.value = '';
                knowledgeType.value = 'example';
                knowledgeContent.value = '';
                knowledgeTags.value = '';

                // Refresh search if there's an active search
                if (knowledgeSearch.value.trim()) {
                    searchKnowledgeBase();
                }
            } else {
                throw new Error('Failed to add knowledge entry');
            }
        } catch (error) {
            console.error('Error adding knowledge entry:', error);
            alert('Error adding knowledge entry: ' + error.message);
        }
    }

    // Update agent model configuration
    async function updateAgentModel(agentType, model) {
        try {
            const response = await fetch(`/api/models/${agentType}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: model
                })
            });

            if (response.ok) {
                alert(`Model for ${agentType} updated to ${model}`);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update model');
            }
        } catch (error) {
            console.error('Error updating agent model:', error);
            alert('Error updating agent model: ' + error.message);
        }
    }
});