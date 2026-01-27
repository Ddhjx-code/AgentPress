"""
AgentPress 包入口点，提供命令行接口
"""
import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# 导入并运行CLI
from cli import main

if __name__ == "__main__":
    main()