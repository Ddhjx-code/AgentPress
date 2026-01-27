"""
PyInstaller runtime hook to fix Python path for modules
"""
import sys
import os
from pathlib import Path

# 如果在打包环境
if hasattr(sys, '_MEIPASS'):
    # 获取PyInstaller的临时目录
    temp_dir = Path(sys._MEIPASS)

    # 添加主目录到路径
    if str(temp_dir) not in sys.path:
        sys.path.insert(0, str(temp_dir))

    # 动态检查并添加core和src路径
    core_path = temp_dir / 'core'
    src_path = temp_dir / 'src'

    # 添加core路径（优先，这样 import core 模块能正常工作）
    if core_path.exists() and core_path.is_dir():
        if str(core_path) not in sys.path:
            sys.path.insert(0, str(core_path))

        # 确保__init__.py可以被识别（可能不需要，但为了安全起见）
        core_init = core_path / '__init__.py'
        if not core_init.exists():
            # 如果不存在，我们仍应能通过路径导入
            pass

    # 添加src路径
    if src_path.exists() and src_path.is_dir():
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        # 同样检查src的__init__.py
        src_init = src_path / '__init__.py'
        if not src_init.exists():
            pass

# 作为后备方案，确保当前执行文件目录也在路径中
exec_dir = Path(sys.executable).parent
if str(exec_dir) not in sys.path:
    sys.path.insert(0, str(exec_dir))