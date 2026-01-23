// ui/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // 模型配置和管理
    const agentModelTable = document.getElementById('agentModelTable');
    const startCreationBtn = document.getElementById('startCreation');
    const creationProgress = document.getElementById('creationProgress');
    const storyIdea = document.getElementById('storyIdea');
    const storyTheme = document.getElementById('storyTheme');

    // 章节和实时更新功能
    const realtimeUpdates = document.getElementById('realtimeUpdates');
    const connectionStatus = document.getElementById('connectionStatus');
    const currentStatus = document.getElementById('currentStatus');
    const chapterUpdates = document.getElementById('chapterUpdates');
    const chapterContents = document.getElementById('chapterContents');
    const chaptersContainer = document.getElementById('chaptersContainer');

    // 知识库功能
    const knowledgeTitle = document.getElementById('knowledgeTitle');
    const knowledgeType = document.getElementById('knowledgeType');
    const knowledgeContent = document.getElementById('knowledgeContent');
    const knowledgeTags = document.getElementById('knowledgeTags');
    const addKnowledgeBtn = document.getElementById('addKnowledge');
    const knowledgeSearch = document.getElementById('knowledgeSearch');
    const searchBtn = document.getElementById('searchBtn');
    const searchResults = document.getElementById('searchResults');

    let ws = null; // WebSocket连接
    let isGenerating = false; // 是否正在生成

    // 初始化UI元素
    initializeAgentManagement();
    initializeKnowledgeBase();
    initializeWebSocketFeatures();

    // 开始故事创作
    startCreationBtn.addEventListener('click', startStoryCreation);

    // 搜索知识
    searchBtn.addEventListener('click', searchKnowledgeBase);
    knowledgeSearch.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchKnowledgeBase();
        }
    });

    // 添加知识到知识库
    addKnowledgeBtn.addEventListener('click', addKnowledgeToBase);

    // 初始化代理管理
    function initializeAgentManagement() {
        const changeModelButtons = document.querySelectorAll('#agentModelTable button');
        changeModelButtons.forEach(button => {
            button.addEventListener('click', function() {
                const row = this.closest('tr');
                const agentType = row.cells[0].textContent.toLowerCase().split('/')[0].split(' ').join('_');
                const modelSelect = row.querySelector('select');  // Changed from input to select
                const newModel = modelSelect.value;

                updateAgentModel(agentType, newModel);
            });
        });

        // 初始化提示词管理功能
        document.getElementById('loadPromptBtn')?.addEventListener('click', loadPromptContent);
        document.getElementById('savePromptBtn')?.addEventListener('click', savePromptContent);
    }

    // 初始化WebSocket相关功能
    function initializeWebSocketFeatures() {
        // 初始化章节容器
        chaptersContainer.innerHTML = '<div class="text-center text-muted">暂无章节内容</div>';
    }

    // 建立WebSocket连接
    function connectWebSocket() {
        // 关闭现有的连接
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
        }

        // 使用适当的协议 (ws:// 或 wss://)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/progress`;

        ws = new WebSocket(wsUrl);

        ws.onopen = function(event) {
            console.log('WebSocket连接已建立');
            connectionStatus.className = 'badge bg-success';
            connectionStatus.textContent = '已连接';
            updateCurrentStatus('WebSocket连接成功，等待故事生成指令...');
        };

        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (e) {
                console.error('解析WebSocket消息时出错:', e);
            }
        };

        ws.onclose = function(event) {
            console.log('WebSocket连接已关闭', event);
            connectionStatus.className = 'badge bg-warning';
            connectionStatus.textContent = '已断开';

            if (isGenerating) {
                // 如果在生成过程中断线，尝试重连
                setTimeout(() => {
                    updateCurrentStatus('连接已断开，正在尝试重新连接...');
                    connectWebSocket();
                }, 2000);
            }
        };

        ws.onerror = function(error) {
            console.error('WebSocket错误:', error);
            connectionStatus.className = 'badge bg-danger';
            connectionStatus.textContent = '错误';
            updateCurrentStatus(`WebSocket连接错误: ${error.message}`);
        };
    }

    // 处理WebSocket消息
    function handleWebSocketMessage(data) {
        console.log('收到WebSocket消息:', data);

        if (data.type === 'connection_ok') {
            // 连接确认消息
            console.log('WebSocket连接确认');
        } else if (data.type === 'status_update') {
            // 处理状态更新
            handleStatusUpdate(data.status_data);
        } else if (data.type === 'completion_update') {
            // 处理完成消息
            handleCompletion(data.result);
        } else if (data.type === 'error') {
            // 处理错误消息
            handleError(data.error);
        }
    }

    // 处理状态更新
    function handleStatusUpdate(statusData) {
        if (statusData.is_generating) {
            isGenerating = true;
            realtimeUpdates.style.display = 'block';
            updateCurrentStatus(statusData.status_message);
        } else {
            isGenerating = false;
            updateCurrentStatus(statusData.status_message);
        }

        // 显示进度
        if (creationProgress.style.display === 'none') {
            creationProgress.style.display = 'block';
        }

        // 这里我们可以根据需要计算进度百分比
        if (statusData.current_chapter > 0 && statusData.total_chapters > 0) {
            const progress = Math.min(100, Math.floor((statusData.current_chapter / statusData.total_chapters) * 100));
            creationProgress.querySelector('.progress-bar').style.width = progress + '%';
            creationProgress.querySelector('.progress-bar').textContent = progress + '%';
        }

        // 添加到章节更新历史
        const updateEntry = document.createElement('div');
        updateEntry.className = 'alert alert-light mb-2';
        updateEntry.innerHTML = `
            <small>
                <strong>更新时间:</strong> ${new Date().toLocaleTimeString()}<br>
                <strong>状态:</strong> ${statusData.status_message}<br>
                <strong>当前章节:</strong> ${statusData.current_chapter || 0} / ${statusData.total_chapters || '?'}<br>
                <strong>生成中:</strong> ${statusData.is_generating ? '是' : '否'}<br>
            </small>
        `;
        chapterUpdates.appendChild(updateEntry);
        chapterUpdates.scrollTop = chapterUpdates.scrollHeight;
    }

    // 处理生成完成
    function handleCompletion(result) {
        isGenerating = false;
        updateCurrentStatus('故事生成完成！正在处理最终结果...');

        // 隐藏进度条
        setTimeout(() => {
            creationProgress.style.display = 'none';
        }, 1000);

        if (result.status === 'success' && result.data) {
            // 显示生成完成的章节内容
            displayStoryChapters(result.data);
        } else if (result.status === 'error') {
            updateCurrentStatus(`生成过程中出现错误: ${result.message}`);
        }
    }

    // 处理错误
    function handleError(errorMsg) {
        isGenerating = false;
        updateCurrentStatus(`错误: ${errorMsg}`);
        creationProgress.style.display = 'none';
    }

    // 更新当前状态显示
    function updateCurrentStatus(message) {
        currentStatus.textContent = message;
        currentStatus.className = 'alert alert-info';
    }

    // 显示故事章节
    function displayStoryChapters(storyData) {
        chaptersContainer.innerHTML = '';
        chapterContents.style.display = 'block';

        // 添加整体故事信息
        const storyInfo = document.createElement('div');
        storyInfo.className = 'mb-4 p-3 bg-light rounded';
        storyInfo.innerHTML = `
            <h4>${storyData.initial_idea.substring(0, 50)}${storyData.initial_idea.length > 50 ? '...' : ''}</h4>
            <p><strong>总字数:</strong> ${storyData.final_story.length}</p>
            <p><strong>研究计划:</strong> ${storyData.research_plan ? storyData.research_plan.length + ' 字' : 'N/A'}</p>
        `;
        chaptersContainer.appendChild(storyInfo);

        // 如果有详细的章节信息，展示详细内容
        // 为简单起见，目前显示整个故事
        const fullStorySection = document.createElement('div');
        fullStorySection.className = 'card mb-3 chapter-card';
        fullStorySection.innerHTML = `
            <div class="card-header chapter-header">
                <h5 class="chapter-title">完整故事</h5>
            </div>
            <div class="card-body">
                <pre class="story-content">${storyData.final_story}</pre>
            </div>
        `;
        chaptersContainer.appendChild(fullStorySection);

        // 将故事内容按照章节模式展示 (如果可以解析出章节)
        const chaptersSection = document.createElement('div');
        chaptersSection.className = 'mt-3';

        // 解析章节（基于标题或分段模式）
        const storyContent = storyData.final_story || storyData.draft_story || '';
        const chapterRegex = /[#*]*[第][\u4e00-\u9fa5\d\s]*[章].*[\n\r]/g;
        const matches = [...storyContent.matchAll(chapterRegex)];

        if (matches.length > 1) {
            let lastIndex = 0;
            matches.forEach((match, index) => {
                const chapterStart = match.index;
                const chapterEnd = matches[index + 1] ? matches[index + 1].index : storyContent.length;

                const chapterTitle = match[0].trim();
                const chapterText = storyContent.substring(lastIndex, chapterEnd).trim();

                const chapterSection = document.createElement('div');
                chapterSection.className = 'card mb-3 chapter-card';
                chapterSection.innerHTML = `
                    <div class="card-header bg-primary text-white chapter-header">
                        <h6 class="chapter-title mb-0">${chapterTitle || `第${index+1}章`}</h6>
                    </div>
                    <div class="card-body chapter-content">
                        <pre class="story-content">${chapterText}</pre>
                    </div>
                `;
                chaptersSection.appendChild(chapterSection);

                lastIndex = chapterEnd;
            });
        } else {
            // 如果无法分割章节，就显示整个文本
            const defaultChapterSection = document.createElement('div');
            defaultChapterSection.className = 'card chapter-card';
            defaultChapterSection.innerHTML = `
                <div class="card-header chapter-header">
                    <h6 class="chapter-title">生成的故事内容</h6>
                </div>
                <div class="card-body chapter-content">
                    <pre class="story-content">${storyContent}</pre>
                </div>
            `;
            chaptersSection.appendChild(defaultChapterSection);
        }

        chaptersContainer.appendChild(chaptersSection);
    }

    // 更新开始故事创作函数，使用WebSocket和流式API
    function startStoryCreation() {
        const idea = storyIdea.value.trim();
        const theme = storyTheme.value;

        if (!idea) {
            alert('请输入一个故事创意');
            return;
        }

        // 重置UI
        isGenerating = true;
        creationProgress.style.display = 'block';
        creationProgress.querySelector('.progress-bar').style.width = '0%';
        creationProgress.querySelector('.progress-bar').textContent = '0%';
        creationProgress.querySelector('p').textContent = '正在准备...';

        // 建立WebSocket连接（如果尚未连接）
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            connectWebSocket();
        }

        // 发送创建请求
        const formData = new FormData();
        formData.append('concept', idea);
        formData.append('multi_chapter', 'true');
        formData.append('total_chapters', '1');  // 使用AI动态决策替代硬编码章节数

        fetch('/api/generate-novel-stream', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateCurrentStatus(data.message);
            } else {
                updateCurrentStatus(`错误: ${data.message}`);
                isGenerating = false;
            }
        })
        .catch(error => {
            console.error('请求创建故事时出错:', error);
            updateCurrentStatus(`网络错误: ${error.message}`);
            isGenerating = false;
        });
    }

    // 开始故事创作过程
    function startStoryCreation() {
        const idea = storyIdea.value.trim();
        const theme = storyTheme.value;

        if (!idea) {
            alert('请输入一个故事创意');
            return;
        }

        // 显示进度
        creationProgress.style.display = 'block';
        creationProgress.querySelector('.progress-bar').style.width = '0%';
        creationProgress.querySelector('.progress-bar').textContent = '0%';

        // 模拟创作过程
        simulateCreationProgress();
    }

    // 模拟创作进度 (实际功能的占位符)
    function simulateCreationProgress() {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.floor(Math.random() * 10) + 5;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                creationProgress.querySelector('p').textContent = '创作完成！';
                setTimeout(() => {
                    creationProgress.style.display = 'none';
                }, 3000);
            }

            creationProgress.querySelector('.progress-bar').style.width = progress + '%';
            creationProgress.querySelector('.progress-bar').textContent = progress + '%';
            creationProgress.querySelector('p').textContent = `处理中... ${progress}%`;
        }, 500);
    }

    // 初始化知识库功能
    function initializeKnowledgeBase() {
        // 预填入一些示例搜索结果
        // 在实际实现中，这些会从服务器加载
    }

    // 搜索知识库
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
            console.error('搜索知识库时出错:', error);

            // 备选方案: 显示示例结果
            displaySampleResults(query);
        }
    }

    // 显示搜索结果
    function displaySearchResults(results) {
        searchResults.innerHTML = '';

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="list-group-item">未找到结果</div>';
            return;
        }

        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'list-group-item knowledge-entry';
            item.innerHTML = `
                <h6 class="mb-1">${result.title}</h6>
                <p class="mb-1">${result.content.substring(0, 100)}${result.content.length > 100 ? '...' : ''}</p>
                <small class="text-muted">类型: ${result.knowledge_type} | 标签: ${result.tags.join(', ')}</small>
            `;

            item.addEventListener('click', () => {
                // 加载完整结果以进行编辑/查看
                loadKnowledgeEntry(result);
            });

            searchResults.appendChild(item);
        });
    }

    // 显示示例结果 (占位符)
    function displaySampleResults(query) {
        searchResults.innerHTML = '';
        const sampleResults = [
            {
                title: `"${query}" 的示例结果`,
                content: `这是一个与您的搜索相关的示例知识条目: ${query}. 这通常来自知识库.`,
                knowledge_type: 'example',
                tags: [query, 'sample']
            },
            {
                title: `另一个 ${query} 示例`,
                content: `显示 "${query}" 搜索结果的附加示例条目`,
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
                <small class="text-muted">类型: ${result.knowledge_type} | 标签: ${result.tags.join(', ')}</small>
            `;

            searchResults.appendChild(item);
        });
    }

    // 加载知识条目进行查看/编辑
    function loadKnowledgeEntry(entry) {
        knowledgeTitle.value = entry.title;
        knowledgeType.value = entry.knowledge_type;
        knowledgeContent.value = entry.content;
        knowledgeTags.value = entry.tags.join(',');
    }

    // 添加知识到知识库
    async function addKnowledgeToBase() {
        const title = knowledgeTitle.value.trim();
        const type = knowledgeType.value;
        const content = knowledgeContent.value.trim();
        const tags = knowledgeTags.value.trim().split(',').map(tag => tag.trim()).filter(tag => tag);

        if (!title || !content) {
            alert('请输入知识条目的标题和内容');
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
                alert('知识条目添加成功');

                // 清空表单
                knowledgeTitle.value = '';
                knowledgeType.value = 'example';
                knowledgeContent.value = '';
                knowledgeTags.value = '';

                // 如果有活动搜索，则刷新搜索
                if (knowledgeSearch.value.trim()) {
                    searchKnowledgeBase();
                }
            } else {
                throw new Error('添加知识条目失败');
            }
        } catch (error) {
            console.error('添加知识条目时出错:', error);
            alert('添加知识条目错误: ' + error.message);
        }
    }

    // 加载提示词内容
    async function loadPromptContent() {
        const promptType = document.getElementById('promptSelect').value;
        if (!promptType) {
            alert('请先选择提示词类型');
            return;
        }

        try {
            const response = await fetch(`/api/prompts/${promptType}`);
            const data = await response.json();

            if (response.ok && data.content) {
                document.getElementById('promptContent').value = data.content;
                alert('提示词加载成功');
            } else {
                // 如果API不存在，提供本地示例
                const samplePrompts = {
                    "writer": "你是一个网络文学故事生成器，任务是将《山海经》等古籍内容改编为符合现代网文阅读习惯的叙事段落...",
                    "mythologist": "你是一位《山海经》研究者。你的工作是为故事创作提供丰富的创意素材和灵感来源...",
                    "editor": "你是一个专业的故事编辑。你的任务是评估故事的整体质量并提供建设性反馈...",
                    "fact_checker": "你是一个专业的事实核查员。你的任务是检查故事的逻辑性和一致性...",
                    "dialogue_specialist": "你是一个对话质量专家。你的任务是评估和优化故事中的对话质量...",
                    "documentation_specialist": "你是一个故事档案员。你的任务是跟踪和维护故事中的一致性..."
                };
                document.getElementById('promptContent').value = samplePrompts[promptType] || '提示词内容';
                alert('使用本地示例提示词，请检查后端API是否正常');
            }
        } catch (error) {
            console.error('加载提示词时出错:', error);
            alert('加载提示词错误: ' + error.message);
        }
    }

    // 保存提示词内容
    async function savePromptContent() {
        const promptType = document.getElementById('promptSelect').value;
        const promptContent = document.getElementById('promptContent').value;

        if (!promptType || !promptContent) {
            alert('请选择提示词类型并输入内容');
            return;
        }

        try {
            const response = await fetch(`/api/prompts/${promptType}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: promptContent
                })
            });

            if (response.ok) {
                alert('提示词保存成功');
            } else {
                throw new Error('保存提示词失败');
            }
        } catch (error) {
            console.error('保存提示词时出错:', error);
            alert('保存提示词错误: ' + error.message);
        }
    }

    // 更新代理模型配置
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
                alert(`${agentType} 的模型已更新为 ${model}`);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || '更新模型失败');
            }
        } catch (error) {
            console.error('更新代理模型时出错:', error);
            alert('更新代理模型错误: ' + error.message);
        }
    }
});