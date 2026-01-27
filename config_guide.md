# 生成长篇故事配置指南

## 当前限制

当前系统配置在 `config.py` 中限制了故事长度：
```python
CREATION_CONFIG = {
    "num_chapters": 1,         # 总章数（减少为1章以控制长度）
    "target_length_per_chapter": 2500,  # 每章目标字数（减少以控制token）
    "total_target_length": 3000  # 总目标字数
}
```

## 如何生成超过5000字的故事

要生成超过5000字的短篇故事，需要修改：
- 将 `"total_target_length"` 设置为更高的值 (例如 `6000`)
- 可选：同时调整 `"target_length_per_chapter"` (如 `6000`)

修改步骤：

1. 编辑 `config.py` 文件中的 `CREATION_CONFIG` 部分：
```python
CREATION_CONFIG = {
    "num_chapters": 1,
    "target_length_per_chapter": 6000,  # 每章目标字数修改为6000
    "total_target_length": 6000        # 总目标字数设置为6000
}
```

2. 使用test_concept.txt作为创意输入，运行系统
3. 系统将会生成长篇故事直到达到目标长度

## 生成长篇故事脚本说明

`generate_long_story.py` 脚本已经准备就绪，但目前无法运行直到设置 API 密钥。

## 关于 API 密钥设置

要使脚本正常工作，需要：

1. 设置环境变量：
```bash
export OPENAI_API_KEY='your_api_key_here'
```

2. 或者在OpenAIChatCompletionClient初始化时提供 API key：
```python
model_client = OpenAIChatCompletionClient(
    model="your_model_name",
    base_url="your_base_url",
    api_key="your_api_key_here"  # 添加这一行
)
```

注意：当前配置指定使用qwen3-max模型通过https://apis.iflow.cn/v1访问.