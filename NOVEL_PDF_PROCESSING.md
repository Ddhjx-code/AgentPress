# PDF小说知识库分析工具使用指南

本指南介绍如何使用AgentPress新增的PDF小说分析功能。

## 1. 概述

AgentPress的新增功能支持从PDF格式的世界经典小说中提取文学技巧、节奏分析、经典段落等内容，将其存入知识库中用于后续创作参考。

### 新增功能包括：
- PDF内容提取与智能分段
- 使用AI分析的文学技巧识别
- 经典段落自动判断
- 人物塑造与对话技巧分析
- Web API与命令行双模式处理
- 丰富的知识分类体系

## 2. 新的知识类型

- `novel-technique` - 小说写作技巧分析
- `classic-paragraph` - 经典文学段落
- `character-development` - 人物塑造技巧
- `dialogue-technique` - 对话写作技法
- 继承原有 `example`、`technique` 等类型

## 3. Web API接口

### 3.1 上传单个PDF文件处理
```
POST /api/process-novel-pdf
Content-Type: multipart/form-data

Form Data:
- pdf_file (file): PDF文件
- file_type (string): "pdf" (可选，默认)
```

### 3.2 批量处理PDF文件
```
POST /api/process-novel-pdf-batch
Content-Type: application/json

Body:
{
  "pdf_paths": ["/path/to/file1.pdf", "/path/to/file2.pdf"]
}
```

### 3.3 获取知识库统计
```
GET /api/novel-knowledge-stats
```

### 3.4 搜索小说技巧
```
GET /api/search-novel-techniques?query={搜索词}&tags={tag1,tag2}
```

### 3.5 获取特定类型示例
```
GET /api/examples-by-novel-type?novel_type={type}&limit={number}
```

## 4. 命令行工具使用

### 4.1 处理单个PDF文件
```bash
python process_novels.py /path/to/novel.pdf --mode single
```

### 4.2 处理整个PDF目录
```bash
python process_novels.py /path/to/novels_directory --mode directory
```

## 5. 配置要求

### 5.1 环境变量设置
确保 `.env` 文件包含以下配置：
```
QWEN_API_KEY=your_api_key_here
BASE_URL=https://apis.iflow.cn/v1
MODEL_NAME=qwen3-max
```

## 6. 数据流程

1. PDF解析 → 内容提取
2. 内容分段 → 章节识别
3. AI分析 → 技巧识别
4. 知识条目生成 → 数据库存储
5. 标签分类 → 检索优化

## 7. 技术架构

- **PDFProcessor**: PDF解析和内容预处理
- **LiteraryAnalyzer**: AI驱动的文学技巧分析
- **NovelKnowledgeExtender**: PDF导入和知识库管理
- **Web API**: Web界面和接口服务
- **知识库**: 现有的存储、检索、管理功能

## 8. 注意事项

- 确保AI API配置正确，保证分析功能正常
- 每个PDF文件处理时间取决于长度和AI API响应速度
- 大量文件处理建议使用命令行工具
- 知识库文件默认存储在 `data/knowledge_repo/json_storage.json`

## 9. 自定义扩展

如需扩展分析维度或修改标签规则，可以：

1. 修改 `knowledge/literary_analyzer.py` 中的 `analysis_prompt_templates`
2. 调整 `knowledge/novel_knowledge_extender.py` 中的知识类型
3. 在命令行脚本中添加自定义处理逻辑

这个扩展使得AgentPress成为一个完整的文学分析和创作辅助系统，可以将经典作品中的优秀技法提取到知识库中，为AI创作提供参考。