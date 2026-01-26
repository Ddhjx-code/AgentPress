# 测试套件文档

## 目录结构

```
tests/
├── conftest.py              # Pytest配置和共享fixture
├── pytest.ini              # 测试配置
├── unit/                   # 单元测试
│   ├── test_pdf_processor.py          # PDF处理器单元测试
│   ├── test_literary_analyzer.py      # 文学分析器单元测试
│   └── test_enhanced_storage.py       # 增强存储系统单元测试
├── integration/            # 集成测试
│   └── test_pdf_analysis_integration.py # PDF分析集成测试
└── fixtures/               # 测试数据和固件
```

## 测试说明

### 单元测试 (unit/)
- 针对单个模块或函数进行详细测试
- 使用模拟对象隔离外部依赖
- 覆盖主要类和方法的核心功能

### 集成测试 (integration/)
- 验证多个模块间的交互
- 测试端到端流程（如PDF分析完整流程）
- 包含真实的系统集成场景

### 测试命令

运行所有测试：
```bash
pytest
```

运行単元测试：
```bash
pytest tests/unit/ -v
```

运行集成测试：
```bash
pytest tests/integration/ -v
```

运行特定测试模块：
```bash
pytest tests/unit/test_pdf_processor.py -v
```

## 测试覆盖范围

### PDF处理器测试
- 段落分割算法
- 内容清理和格式化
- 章节标题识别
- 长段落分割策略

### 文学分析器测试
- 段落分析流程
- 知识条目创建
- 分析提示词模板管理
- 批量分析功能

### 增强存储测试
- 分类存储系统
- 知识库CRUD操作
- 按类型检索功能
- 搜索和筛选功能

### 集成测试
- 完整PDF分析流程
- 系统组件交互
- 错误处理和边界情况

## 开发规范

### 编写単元测试
- 使用描述性的测试函数名称
- 提供清晰的断言和错误消息
- 使用pytest fixtures来简化测试设置
- 保持测试独立和可重复

### 编写集成测试
- 覆盖端到端用户场景
- 验证数据流和系统行为
- 包含错误路径和边界条件

所有测试都应保证系统功能的稳定性和可靠性。